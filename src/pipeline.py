from __future__ import annotations
import json, os, shutil, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / 'config' / 'settings.json'

def validate() -> int:
    try:
        cfg = json.loads(CONFIG.read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as exc:
        print(f'CONFIG_ERROR: {exc}')
        return 1
    errors = []
    if not shutil.which('ffmpeg') or not shutil.which('ffprobe'):
        errors.append('FFmpeg and ffprobe must be installed.')
    if not cfg.get('channel_handle'):
        errors.append('channel_handle is missing in config/settings.json')
    if cfg.get('publishing', {}).get('enabled', False):
        errors.append('Publishing is intentionally blocked until OAuth, media checks, duplicate protection and approval gate are implemented.')
    for key in ('YOUTUBE_CLIENT_ID', 'YOUTUBE_CLIENT_SECRET', 'YOUTUBE_REFRESH_TOKEN'):
        if not os.getenv(key): print(f'INFO: {key} is not configured.')
    if not os.getenv('VIDEO_GENERATOR_COMMAND'):
        print('INFO: No video-generation provider configured; generation is inactive.')
    if errors:
        for error in errors: print('VALIDATION_ERROR:', error)
        return 1
    print('VALIDATION_OK: basic configuration/runtime checks passed.')
    print('UPLOAD_STATUS: disabled; no upload attempted.')
    print('GENERATION_STATUS: not configured; no video generated.')
    return 0

def prepare() -> int:
    print('PREPARE_BLOCKED: real video-generation adapter is not implemented; refusing to claim a video was generated.')
    return 2

if __name__ == '__main__':
    if len(sys.argv) != 2 or sys.argv[1] not in ('validate', 'prepare'):
        print('Usage: python -m src.pipeline {validate|prepare}'); raise SystemExit(2)
    raise SystemExit(validate() if sys.argv[1] == 'validate' else prepare())
