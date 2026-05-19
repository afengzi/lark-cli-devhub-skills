import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


def load_validate_module():
    root = Path(__file__).resolve().parents[1]
    path = root / "scripts" / "validate.py"
    spec = importlib.util.spec_from_file_location("devhub_validate", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class ValidateScanTests(unittest.TestCase):
    def setUp(self):
        self.module = load_validate_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_scan_ignores_local_superpowers_state(self):
        state = self.root / ".superpowers" / "brainstorm" / "state"
        state.mkdir(parents=True)
        (state / "server-info").write_text("/" + "Users/example/local-only\n", encoding="utf-8")

        with patch.object(self.module, "ROOT", self.root):
            errors = self.module.scan_forbidden()

        self.assertEqual(errors, [])

    def test_scan_still_catches_committed_user_paths(self):
        docs = self.root / "docs"
        docs.mkdir()
        (docs / "bad.md").write_text("path " + "/" + "Users/example/project\n", encoding="utf-8")

        with patch.object(self.module, "ROOT", self.root):
            errors = self.module.scan_forbidden()

        self.assertEqual(errors, ["docs/bad.md contains forbidden content: absolute macOS user path"])


if __name__ == "__main__":
    unittest.main()
