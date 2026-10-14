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
