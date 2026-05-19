import unittest

from scripts.devhub_lib.reports import draft_report
from scripts.devhub_lib.whiteboard import draft_whiteboard


class ReportDraftTests(unittest.TestCase):
    def test_weekly_report_contains_core_sections(self):
        records = {
            "Tasks": [{"Title": "Fix voice stream", "Status": "Done", "AI Summary": "Closed stream bug"}],
            "Bugfixes": [{"Title": "Voice command ack fixed", "AI Summary": "Ack path corrected"}],
            "AI Runs": [{"Title": "Codex run", "Verification Result": "python3 -m unittest passed"}],
            "Releases": [{"Title": "Release 2026-05-20", "Summary": "Voice fix"}],
            "Decisions": [{"Title": "Use command stream", "Decision": "Keep command ack path"}],
        }

        text = draft_report("weekly", "music-agent", records)

        self.assertIn("# Weekly Report: music-agent", text)
        self.assertIn("## Completed Work", text)
        self.assertIn("Fix voice stream", text)
        self.assertIn("Voice command ack fixed", text)
        self.assertIn("Use command stream", text)

    def test_release_report_contains_release_sections(self):
        records = {"Releases": [{"Title": "Release 2026-05-20", "Rollback Notes": "Revert commit abc"}]}

        text = draft_report("release", "music-agent", records)

        self.assertIn("# Release Brief: music-agent", text)
        self.assertIn("## Rollback Notes", text)
        self.assertIn("Revert commit abc", text)


class WhiteboardDraftTests(unittest.TestCase):
    def test_architecture_draft_contains_artifact_instruction(self):
        text = draft_whiteboard(
            "architecture",
            "music-agent",
            "voice command stream replaces retired audio ack path",
        )
        self.assertIn("# Whiteboard Draft: music-agent", text)
        self.assertIn("## Diagram Nodes", text)
        self.assertIn("voice command stream", text)
        self.assertIn("Create an Artifacts record", text)


if __name__ == "__main__":
    unittest.main()
