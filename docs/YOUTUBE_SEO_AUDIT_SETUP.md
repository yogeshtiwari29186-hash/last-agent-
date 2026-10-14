# YouTube SEO Audit setup

This workflow is a read-only starting implementation. It runs unit tests, then attempts an authenticated audit and uploads both JSON and HTML reports as a GitHub Actions artifact. It does not edit or publish YouTube content.

## 1. Google Cloud setup

1. Open https://console.cloud.google.com/ and create/select a project.
2. Enable **YouTube Data API v3** and **YouTube Analytics API**.
3. Configure the OAuth consent screen for the intended account and testing/production status as appropriate.
4. Create an OAuth 2.0 Client ID of type **Desktop app** for the one-time local authorization flow.
5. Use the scope `https://www.googleapis.com/auth/youtube.readonly`. Analytics API report queries require authorized access to the channel's data.
6. Complete a one-time OAuth authorization for the Google account that owns/manages the channel and obtain a refresh token. Do not paste the token into chat or commit it to Git.

The refresh token must be generated for the same OAuth client ID/secret used in the workflow. If the OAuth consent screen is in Testing, refresh-token lifetime/availability can be limited for external apps; check Google's current OAuth policy before relying on long-running schedules.

## 2. GitHub Actions secrets

In the repository, open **Settings → Secrets and variables → Actions → New repository secret** and add:

- `YOUTUBE_CLIENT_ID`
- `YOUTUBE_CLIENT_SECRET`
- `YOUTUBE_REFRESH_TOKEN`

Never put secret values in workflow YAML, reports, logs, issues, or source files.

## 3. Run and inspect

- Open **Actions → YouTube SEO Audit → Run workflow** for a manual run.
- The scheduled run is daily at 12:00 UTC (17:30 India Standard Time).
- Open a completed run and download the `youtube-seo-audit-N` artifact to get `audit.json` and `audit.html`.

If secrets are absent, the report must say `BLOCKED_AUTH`; this is not a completed audit. OAuth errors produce `FAILED_AUTH`, API errors produce `FAILED_API`. Read the report status before trusting any findings.

## Current audit coverage

- Reads channel identity and up to 200 most recent uploads.
- Checks title and description presence/length, whether tags were returned, and whether thumbnail metadata was returned.
- Queries available period metrics: views, estimated minutes watched, average view duration, likes, comments, and shares.
- Uses a 28-day window ending two days before the run to reduce the risk of partial latest-day data.
- Emits JSON and HTML.

## Important limitations

- Heuristic title/description lengths are review prompts, not YouTube ranking rules.
- Tags are optional; missing tags are informational, not a penalty claim.
- This version does not calculate YouTube search ranking, keyword demand, impressions CTR, detailed retention curves, competitor analytics, or AI-generated recommendations.
- Analytics metric/report combinations can vary. If the Analytics query is unsupported, metadata audit continues with a warning and report status reflects that warning.
- No video/channel edits, uploads, or scheduled publishing are implemented.
- A scheduled workflow is not proof of a successful API audit. Check the report status and Actions logs.

## Local tests

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
```
