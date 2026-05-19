import unittest
import tempfile
from pathlib import Path

import scripts.devhub_lib.wiki_docs as wiki_docs


class WikiArtifactLayoutTests(unittest.TestCase):
    def test_artifacts_are_created_under_global_and_project_folders(self):
        calls = []
        records = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["wiki", "+node-list"]:
                return {"data": {"items": []}}, "{}"
            if args[:2] == ["wiki", "+node-create"]:
                title = args[args.index("--title") + 1]
                token = "node_" + title.replace(" ", "_").replace("/", "_")
                return {"node_token": token, "obj_token": "doc_" + token, "url": f"https://wiki/{token}"}, "{}"
            if args[:2] == ["docs", "+create"]:
                title = args[args.index("--title") + 1]
                return {"document_id": "doc_" + title.replace(" ", "_"), "url": f"https://doc/{title}"}, "{}"
            if args[:2] == ["docs", "+fetch"]:
                return {"data": {"document": {"content": "<title>generated</title>"}}}, "{}"
            if args[:2] == ["docs", "+update"]:
                if "--content" in args and '<whiteboard type="blank"></whiteboard>' in args:
                    return {"data": {"document": {"new_blocks": [{"block_type": "whiteboard", "block_token": "wb_token"}]}}}, "{}"
                return {"ok": True}, "{}"
            raise AssertionError(args)

        def fake_run_lark_with_input(args, stdin, check=True):
            calls.append(args)
            if "--dry-run" in args:
                return {"ok": True}, "0 whiteboard nodes will be deleted"
            return {"ok": True}, "{}"

        def fake_batch_upsert_records(_config, table, payloads, **_kwargs):
            for payload in payloads:
                records.append((table, payload))

        original_run = wiki_docs.run_lark
        original_run_with_input = wiki_docs.run_lark_with_input
        original_batch_upsert = wiki_docs.batch_upsert_records
        original_update_input = wiki_docs.whiteboard_update_input
        wiki_docs.run_lark = fake_run_lark
        wiki_docs.run_lark_with_input = fake_run_lark_with_input
        wiki_docs.batch_upsert_records = fake_batch_upsert_records
        wiki_docs.whiteboard_update_input = lambda _template, _source: ("{}", "raw")
        try:
            config = {
                "defaults": {"project": "music_agent"},
                "wiki": {"space_id": "space", "root_node_token": "root", "root_url": "https://wiki/root"},
            }
            wiki_docs.create_artifacts(config)
        finally:
            wiki_docs.run_lark = original_run
            wiki_docs.run_lark_with_input = original_run_with_input
            wiki_docs.batch_upsert_records = original_batch_upsert
            wiki_docs.whiteboard_update_input = original_update_input

        created_node_titles = [
            args[args.index("--title") + 1]
            for args in calls
            if args[:2] == ["wiki", "+node-create"]
        ]
        self.assertIn("00 Global", created_node_titles)
        self.assertIn("10 Projects", created_node_titles)
        self.assertIn("music_agent", created_node_titles)

        content_node_creates = [
            args
            for args in calls
            if args[:2] == ["wiki", "+node-create"]
            and args[args.index("--title") + 1] in {"Global: Dev Hub 使用说明", "music_agent: 项目主页"}
        ]
        self.assertTrue(all("--parent-node-token" in args for args in content_node_creates))
        self.assertFalse(any(args[args.index("--parent-node-token") + 1] == "root" for args in content_node_creates))

        artifact_titles = [payload["Title"] for table, payload in records if table == "Artifacts"]
        self.assertIn("Global: Dev Hub 使用说明", artifact_titles)
        self.assertIn("music_agent: 项目主页", artifact_titles)
        self.assertIn("music_agent: 架构图", artifact_titles)
        self.assertIn("Global: PR 写回流程图", artifact_titles)
        self.assertIn("Global: 任务执行闭环图", artifact_titles)
        self.assertIn("music_agent: PR 写回流程图", artifact_titles)
        self.assertIn("music_agent: 任务执行闭环图", artifact_titles)
        self.assertIn("Template: PR 写回流程图", artifact_titles)

        board_updates = [args for args in calls if args[:2] == ["whiteboard", "+update"] and "--dry-run" not in args]
        self.assertGreaterEqual(len(board_updates), 11)

    def test_current_project_uses_cwd_when_config_repo_path_is_different(self):
        original_repo = wiki_docs.DEFAULT_REPO
        wiki_docs.DEFAULT_REPO = Path("/work/lark-cli-devhub-skills")
        try:
            project = wiki_docs.current_project_name(
                {
                    "defaults": {
                        "project": "music_agent",
                        "repo_path": "/work/music_agent",
                    }
                }
            )
        finally:
            wiki_docs.DEFAULT_REPO = original_repo

        self.assertEqual(project, "lark-cli-devhub-skills")

    def test_whiteboard_idempotent_tokens_do_not_collide_for_chinese_titles(self):
        titles = [
            "Global: Bug 排查路径图",
            "Global: PR 写回流程图",
            "Global: 任务执行闭环图",
            "lark-cli-devhub-skills: Bug 排查路径图",
            "lark-cli-devhub-skills: PR 写回流程图",
            "lark-cli-devhub-skills: 任务执行闭环图",
        ]
        tokens = [wiki_docs.idempotent_token(title) for title in titles]

        self.assertEqual(len(tokens), len(set(tokens)))
        self.assertTrue(all(token.startswith("devhub-") for token in tokens))

    def test_svg_conversion_uses_local_cache(self):
        class Result:
            returncode = 0
            stdout = '{"code":0,"data":{"nodes":[]}}'
            stderr = ""

        calls = []
        original_home = wiki_docs.DEVHUB_HOME
        original_run = wiki_docs.subprocess.run

        def fake_run(args, **_kwargs):
            calls.append(args)
            return Result()

        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_docs.DEVHUB_HOME = Path(temp_dir)
            wiki_docs.subprocess.run = fake_run
            try:
                first, first_format = wiki_docs.whiteboard_update_input("map.svg", "<svg></svg>")
                second, second_format = wiki_docs.whiteboard_update_input("map.svg", "<svg></svg>")
            finally:
                wiki_docs.DEVHUB_HOME = original_home
                wiki_docs.subprocess.run = original_run

        self.assertEqual(first, second)
        self.assertEqual(first_format, "raw")
        self.assertEqual(second_format, "raw")
        self.assertEqual(len(calls), 1)

    def test_existing_whiteboard_is_preserved_unless_overwrite_is_enabled(self):
        original_env = wiki_docs.os.environ.get("DEVHUB_WHITEBOARD_OVERWRITE")
        try:
            wiki_docs.os.environ.pop("DEVHUB_WHITEBOARD_OVERWRITE", None)
            self.assertTrue(wiki_docs.should_preserve_existing_whiteboard(newly_created=False))
            self.assertFalse(wiki_docs.should_preserve_existing_whiteboard(newly_created=True))

            wiki_docs.os.environ["DEVHUB_WHITEBOARD_OVERWRITE"] = "1"
            self.assertFalse(wiki_docs.should_preserve_existing_whiteboard(newly_created=False))
        finally:
            if original_env is None:
                wiki_docs.os.environ.pop("DEVHUB_WHITEBOARD_OVERWRITE", None)
            else:
                wiki_docs.os.environ["DEVHUB_WHITEBOARD_OVERWRITE"] = original_env


if __name__ == "__main__":
    unittest.main()
