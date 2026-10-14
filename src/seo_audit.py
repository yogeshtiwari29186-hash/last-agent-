"""Read-only YouTube SEO audit. Never changes channel/video metadata."""
from __future__ import annotations

import argparse
import html
import json
import os
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def audit_metadata(video: dict[str, Any]) -> list[dict[str, str]]:
    """Return explainable metadata findings for one video."""
    snippet = video.get("snippet") or {}
    title = str(snippet.get("title") or "").strip()
    description = str(snippet.get("description") or "").strip()
    tags = snippet.get("tags") or []
    findings: list[dict[str, str]] = []
    video_id = str(video.get("id") or "")
    link = f"https://www.youtube.com/watch?v={video_id}" if video_id else ""

    def add(severity: str, code: str, message: str, recommendation: str) -> None:
        findings.append({
            "severity": severity, "code": code, "video_id": video_id,
            "video_url": link, "title": title,
            "evidence": message, "recommendation": recommendation,
        })

    if not title:
        add("high", "TITLE_MISSING", "The video title is empty or unavailable.",
            "Write a clear, accurate title that describes the video's actual content.")
    elif len(title) < 15:
        add("medium", "TITLE_SHORT", f"Title has {len(title)} characters.",
            "Consider a more descriptive title if it helps viewers understand the topic.")
    elif len(title) > 70:
        add("low", "TITLE_LONG", f"Title has {len(title)} characters.",
            "Review whether the key topic can be made clearer earlier in the title.")

    if not description:
        add("medium", "DESCRIPTION_MISSING", "Description is empty.",
            "Add a useful, accurate description of the video and its main topic.")
    elif len(description) < 100:
        add("low", "DESCRIPTION_BRIEF", f"Description has {len(description)} characters.",
            "Consider adding useful context; do not add repetitive or unrelated keywords.")

    if not tags:
        add("info", "NO_TAGS", "No video tags were returned.",
            "Tags are optional and generally play a limited discovery role; add only relevant terms when useful.")
    if not (snippet.get("thumbnails") or {}):
        add("info", "THUMBNAIL_UNAVAILABLE", "Thumbnail metadata was not returned.",
            "Check the thumbnail in YouTube Studio; this API response did not include thumbnail metadata.")
    return findings


def _credentials_from_env():
    client_id = os.getenv("YOUTUBE_CLIENT_ID")
    client_secret = os.getenv("YOUTUBE_CLIENT_SECRET")
    refresh_token = os.getenv("YOUTUBE_REFRESH_TOKEN")
    if not all((client_id, client_secret, refresh_token)):
        return None
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    credentials = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.readonly"],
    )
    credentials.refresh(Request())
    return credentials


def run_audit(output_dir: Path, end_date: date | None = None) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    end = end_date or (date.today() - timedelta(days=2))
    start = end - timedelta(days=27)
    report: dict[str, Any] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED_AUTH",
        "channel": None,
        "date_range": {"start": start.isoformat(), "end": end.isoformat()},
        "summary": {"videos_checked": 0, "findings": 0, "high": 0, "medium": 0, "low": 0, "info": 0},
        "findings": [],
        "videos": [],
        "limitations": [
            "Read-only audit: this tool never edits titles, descriptions, tags, thumbnails, or publishes videos.",
            "YouTube search ranking and keyword demand are not directly measured by these checks.",
            "CTR and detailed audience-retention metrics are omitted unless a separately validated API report is implemented.",
            "YouTube API data may be delayed, sampled, or unavailable for some metrics.",
        ],
    }

    try:
        credentials = _credentials_from_env()
    except Exception as exc:
        report["status"] = "FAILED_AUTH"
        report["error"] = f"OAuth refresh failed: {type(exc).__name__}: {exc}"
        _write_reports(output_dir, report)
        return report

    if credentials is None:
        report["message"] = (
            "Audit blocked: configure YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, "
            "and YOUTUBE_REFRESH_TOKEN in GitHub Actions secrets."
        )
        _write_reports(output_dir, report)
        return report

    try:
        from googleapiclient.discovery import build

        youtube = build("youtube", "v3", credentials=credentials, cache_discovery=False)
        analytics = build("youtubeAnalytics", "v2", credentials=credentials, cache_discovery=False)
        channels = youtube.channels().list(part="snippet,contentDetails", mine=True).execute()
        items = channels.get("items", [])
        if not items:
            raise RuntimeError("OAuth user has no accessible YouTube channel.")
        channel = items[0]
        report["channel"] = {
            "id": channel["id"],
            "title": channel.get("snippet", {}).get("title", "Unknown"),
        }

        uploads_playlist = channel.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads")
        video_ids: list[str] = []
        if uploads_playlist:
            page_token = None
            while len(video_ids) < 200:
                page = youtube.playlistItems().list(
                    part="contentDetails", playlistId=uploads_playlist,
                    maxResults=min(50, 200 - len(video_ids)), pageToken=page_token
                ).execute()
                video_ids.extend(
                    item.get("contentDetails", {}).get("videoId", "")
                    for item in page.get("items", [])
                    if item.get("contentDetails", {}).get("videoId")
                )
                page_token = page.get("nextPageToken")
                if not page_token:
                    break

        metadata: dict[str, dict[str, Any]] = {}
        for offset in range(0, len(video_ids), 50):
            batch = video_ids[offset:offset + 50]
            response = youtube.videos().list(
                part="snippet,statistics,contentDetails", id=",".join(batch)
            ).execute()
            for item in response.get("items", []):
                metadata[item["id"]] = item

        analytics_rows: dict[str, dict[str, Any]] = {}
        if video_ids:
            try:
                result = analytics.reports().query(
                    ids="channel==MINE",
                    startDate=start.isoformat(),
                    endDate=end.isoformat(),
                    dimensions="video",
                    metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments,shares",
                    sort="-views",
                    maxResults=200,
                ).execute()
                headers = [header["name"] for header in result.get("columnHeaders", [])]
                for row in result.get("rows", []):
                    values = dict(zip(headers, row))
                    vid = values.get("video")
                    if vid:
                        analytics_rows[vid] = values
            except Exception as exc:
                report.setdefault("warnings", []).append(
                    f"Analytics report unavailable ({type(exc).__name__}); metadata audit continued."
                )

        video_reports = []
        for vid in video_ids:
            item = metadata.get(vid)
            if not item:
                continue
            video_findings = audit_metadata(item)
            report["findings"].extend(video_findings)
            stats = item.get("statistics") or {}
            metrics = analytics_rows.get(vid, {})
            video_reports.append({
                "id": vid,
                "title": item.get("snippet", {}).get("title", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
                "published_at": item.get("snippet", {}).get("publishedAt"),
                "views_public": int(stats.get("viewCount", 0) or 0),
                "views_period": metrics.get("views"),
                "estimated_minutes_watched": metrics.get("estimatedMinutesWatched"),
                "average_view_duration_seconds": metrics.get("averageViewDuration"),
                "likes_period": metrics.get("likes"),
                "comments_period": metrics.get("comments"),
                "shares_period": metrics.get("shares"),
                "finding_count": len(video_findings),
            })
        report["videos"] = video_reports
        report["summary"]["videos_checked"] = len(video_reports)
        report["summary"]["findings"] = len(report["findings"])
        for severity in ("high", "medium", "low", "info"):
            report["summary"][severity] = sum(1 for f in report["findings"] if f["severity"] == severity)
        report["status"] = "COMPLETED" if not report.get("warnings") else "COMPLETED_WITH_WARNINGS"
    except Exception as exc:
        report["status"] = "FAILED_API"
        report["error"] = f"{type(exc).__name__}: {exc}"

    _write_reports(output_dir, report)
    return report


def _write_reports(output_dir: Path, report: dict[str, Any]) -> None:
    json_path = output_dir / "audit.json"
    html_path = output_dir / "audit.html"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    findings = report.get("findings", [])
    rows = []
    for finding in findings:
        rows.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                html.escape(str(finding.get("severity", ""))),
                html.escape(str(finding.get("code", ""))),
                html.escape(str(finding.get("title", ""))),
                html.escape(str(finding.get("evidence", ""))),
                html.escape(str(finding.get("recommendation", ""))),
            )
        )
    channel = report.get("channel") or {}
    document = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>YouTube SEO Audit</title><style>
body{{font:16px system-ui;max-width:1200px;margin:2rem auto;padding:0 1rem;color:#172033}}
.status{{padding:.8rem;border:1px solid #bbb;border-radius:8px}}table{{width:100%;border-collapse:collapse}}
th,td{{text-align:left;border-bottom:1px solid #ddd;padding:.6rem;vertical-align:top}}
</style></head><body><h1>YouTube SEO Audit</h1>
<p class="status"><b>Status:</b> {status}</p><p><b>Channel:</b> {channel}</p>
<p><b>Period:</b> {start} to {end}</p><p><b>Videos checked:</b> {count} · <b>Findings:</b> {findings_count}</p>
{message}<h2>Findings</h2><table><thead><tr><th>Severity</th><th>Rule</th><th>Video</th><th>Evidence</th><th>Recommendation</th></tr></thead>
<tbody>{rows}</tbody></table><h2>Limitations</h2><ul>{limitations}</ul>
<p>Read-only report. No YouTube content was changed.</p></body></html>""".format(
        status=html.escape(str(report.get("status", "UNKNOWN"))),
        channel=html.escape(str(channel.get("title", "Not connected"))),
        start=html.escape(str(report.get("date_range", {}).get("start", ""))),
        end=html.escape(str(report.get("date_range", {}).get("end", ""))),
        count=report.get("summary", {}).get("videos_checked", 0),
        findings_count=report.get("summary", {}).get("findings", 0),
        message=f"<p>{html.escape(str(report.get('message', report.get('error', ''))))}</p>" if report.get("message") or report.get("error") else "",
        rows="".join(rows) or "<tr><td colspan='5'>No findings were produced. Check report status before interpreting this as success.</td></tr>",
        limitations="".join(f"<li>{html.escape(str(item))}</li>" for item in report.get("limitations", [])),
    )
    html_path.write_text(document, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a read-only YouTube SEO audit.")
    parser.add_argument("--output-dir", default="reports")
    args = parser.parse_args()
    report = run_audit(Path(args.output_dir))
    print(f"Audit status: {report['status']}")
    print(f"Report files: {args.output_dir}/audit.json, {args.output_dir}/audit.html")
    if report["status"] in {"BLOCKED_AUTH", "FAILED_AUTH", "FAILED_API"}:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
