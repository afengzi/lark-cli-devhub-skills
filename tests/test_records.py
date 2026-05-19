import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.devhub_lib.records import write_outbox, write_receipt


class RecordEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_receipt_uses_v15_shape(self):
        with patch("scripts.devhub_lib.records.repo_runtime_dir", return_value=self.cwd / ".devhub" / "receipts"):
            path = write_receipt(
                self.cwd,
                "record-ai-run",
                "rec123",
                "AI run summary",
                {
                    "table": "AI Runs",
                    "payload_title": "Investigated voice command stream",
                    "source": {"type": "manual", "commit": "abc123", "pr": ""},
                },
            )

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["operation"], "record-ai-run")
        self.assertEqual(data["target"]["table"], "AI Runs")
        self.assertEqual(data["target"]["record_id"], "rec123")
        self.assertEqual(data["source"]["type"], "manual")
        self.assertEqual(data["summary"], "AI run summary")

    def test_write_outbox_uses_v15_shape(self):
        with patch("scripts.devhub_lib.records.repo_runtime_dir", return_value=self.cwd / ".devhub" / "outbox"):
            path = write_outbox(
                self.cwd,
                "record-release",
                {"table": "Releases", "payload": {"Title": "Release"}},
                "missing scope",
            )

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["operation"], "record-release")
        self.assertEqual(data["error"], "missing scope")
        self.assertEqual(data["payload"]["table"], "Releases")
        self.assertEqual(data["retry_count"], 0)


if __name__ == "__main__":
    unittest.main()
