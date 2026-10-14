import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.seo_audit import audit_metadata, run_audit


class AuditMetadataTests(unittest.TestCase):
    def test_flags_missing_title_and_description(self):
        findings = audit_metadata({"id": "abc123", "snippet": {"title": "", "description": ""}})
        codes = {item["code"] for item in findings}
        self.assertIn("TITLE_MISSING", codes)
        self.assertIn("DESCRIPTION_MISSING", codes)

    def test_accepts_descriptive_metadata(self):
        findings = audit_metadata({
            "id": "abc123",
            "snippet": {
                "title": "A descriptive title for this educational video",
                "description": "A useful description. " * 10,
                "tags": ["education", "tutorial"],
                "thumbnails": {"default": {"url": "https://example.test/thumb.jpg"}},
            },
        })
        self.assertEqual(findings, [])

    def test_short_title_is_a_finding_not_a_crash(self):
        findings = audit_metadata({"id": "x1", "snippet": {"title": "Hi", "description": "D" * 120}})
        self.assertIn("TITLE_SHORT", {item["code"] for item in findings})

    def test_missing_oauth_is_reported_as_blocked_not_success(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(
            "os.environ",
            {"YOUTUBE_CLIENT_ID": "", "YOUTUBE_CLIENT_SECRET": "", "YOUTUBE_REFRESH_TOKEN": ""},
            clear=False,
        ):
            report = run_audit(Path(temp))
            self.assertEqual(report["status"], "BLOCKED_AUTH")
            self.assertTrue((Path(temp) / "audit.json").exists())
            self.assertTrue((Path(temp) / "audit.html").exists())
            saved = json.loads((Path(temp) / "audit.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["status"], "BLOCKED_AUTH")


if __name__ == "__main__":
    unittest.main()
