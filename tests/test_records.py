import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.devhub_lib.cli import build_parser
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


class ParserRecordCommandTests(unittest.TestCase):
    def test_v15_record_commands_exist(self):
        parser = build_parser()
        for command in [
            "record-task",
            "record-bugfix",
            "record-pitfall",
            "record-playbook",
            "record-ai-run",
            "record-release",
            "record-decision",
            "record-artifact",
            "record-project-fact",
        ]:
            args = parser.parse_args([command, "--payload", "/tmp/payload.json"])
            self.assertTrue(callable(args.func))

    def test_record_commands_accept_optional_wiki_writeback(self):
        parser = build_parser()
        args = parser.parse_args(["record-bugfix", "--payload", "/tmp/payload.json", "--wiki"])
        self.assertTrue(callable(args.func))
        self.assertTrue(args.wiki)

    def test_cleanup_relation_fields_command_exists(self):
        parser = build_parser()
        args = parser.parse_args(["cleanup-relation-fields", "--dry-run"])
        self.assertTrue(callable(args.func))
        self.assertTrue(args.dry_run)

    def test_report_draft_accepts_wiki_writeback(self):
        parser = build_parser()
        args = parser.parse_args(["report-draft", "--kind", "weekly", "--project", "music_agent", "--records", "/tmp/records.json", "--wiki"])
        self.assertTrue(callable(args.func))
        self.assertTrue(args.wiki)


if __name__ == "__main__":
    unittest.main()
