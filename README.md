# YouTube Automation for @coodwithyogesh

This is a safe starter scaffold, not a finished auto-publisher.

## Added
- GitHub Actions scheduled validation at 12:00 UTC (17:30 India time) and manual run.
- Python 3.12 and FFmpeg setup.
- Shorts and long-video configuration defaults.
- Fail-closed publishing defaults (`publishing.enabled=false`).
- A validation command that does not print secret values.

## Not yet implemented
- Actual AI script, voiceover or video generation.
- Full media-quality checks and duplicate detection.
- YouTube OAuth and API upload.
- A real approval/publishing gate.

The workflow will not upload videos and will not claim a video was generated. Keep publishing disabled until the missing parts are implemented and tested.

## Test
Open Actions → YouTube Automation → Run workflow → choose `validate`.

## Future secrets
After OAuth is configured, add `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN` under Settings → Secrets and variables → Actions. Never commit credentials or share secret values in chat. This scaffold does not yet use these secrets.

Next, implement a real video-generation provider, ffprobe media checks, YouTube OAuth upload as private, processing-status verification, duplicate prevention, and a genuine approval gate before scheduled publishing.


## YouTube SEO Audit (read-only)

A separate workflow, `.github/workflows/youtube-seo-audit.yml`, runs daily at 12:00 UTC (17:30 India time), on relevant code pushes, or manually. It runs offline unit tests and produces JSON + HTML audit reports as a GitHub Actions artifact.

Implementation: `src/seo_audit.py`. Setup instructions: [docs/YOUTUBE_SEO_AUDIT_SETUP.md](docs/YOUTUBE_SEO_AUDIT_SETUP.md).

This audit is not active against a real channel until the Google Cloud APIs and OAuth credentials are configured as GitHub Actions secrets:
`YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, and `YOUTUBE_REFRESH_TOKEN`. Missing credentials produce a `BLOCKED_AUTH` report, not a successful audit. The audit is read-only and does not change videos or publish content. Review the report status before relying on results.
