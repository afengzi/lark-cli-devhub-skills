import unittest
import tempfile
from pathlib import Path

import scripts.devhub_lib.wiki_docs as wiki_docs
import scripts.devhub_lib.wiki_common as wiki_common
import scripts.devhub_lib.wiki_whiteboards as wiki_whiteboards
import scripts.devhub_lib.wiki_writeback as wiki_writeback


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
                if "--markdown" in args and '<whiteboard type="blank"></whiteboard>' in args:
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

        original_common_run = wiki_common.run_lark
        original_common_run_with_input = wiki_common.run_lark_with_input
        original_whiteboard_run = wiki_whiteboards.run_lark
        original_whiteboard_run_with_input = wiki_whiteboards.run_lark_with_input
        original_batch_upsert = wiki_docs.batch_upsert_records
        original_update_input = wiki_docs.whiteboard_update_input
        wiki_common.run_lark = fake_run_lark
        wiki_common.run_lark_with_input = fake_run_lark_with_input
        wiki_whiteboards.run_lark = fake_run_lark
        wiki_whiteboards.run_lark_with_input = fake_run_lark_with_input
        wiki_docs.batch_upsert_records = fake_batch_upsert_records
        wiki_docs.whiteboard_update_input = lambda _template, _source: ("{}", "raw")
        try:
            config = {
                "defaults": {"project": "music_agent"},
                "wiki": {"space_id": "space", "root_node_token": "root", "root_url": "https://wiki/root"},
            }
            wiki_docs.create_artifacts(config)
        finally:
            wiki_common.run_lark = original_common_run
            wiki_common.run_lark_with_input = original_common_run_with_input
            wiki_whiteboards.run_lark = original_whiteboard_run
            wiki_whiteboards.run_lark_with_input = original_whiteboard_run_with_input
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
            and args[args.index("--title") + 1] in {"Global: Dev Hub 使用说明"}
        ]
        self.assertTrue(all("--parent-node-token" in args for args in content_node_creates))
        self.assertFalse(any(args[args.index("--parent-node-token") + 1] == "root" for args in content_node_creates))

        artifact_titles = [payload["Title"] for table, payload in records if table == "Artifacts"]
        self.assertIn("Global: Dev Hub 使用说明", artifact_titles)
        self.assertIn("00 Overview", artifact_titles)
        self.assertIn("20 Bugfix Retros", artifact_titles)
        self.assertIn("30 Playbooks", artifact_titles)
        self.assertIn("40 Decisions", artifact_titles)
        self.assertIn("60 Reports", artifact_titles)
        self.assertIn("music_agent: 架构图", artifact_titles)
        self.assertIn("Global: PR 写回流程图", artifact_titles)
        self.assertIn("Global: 任务执行闭环图", artifact_titles)
        self.assertIn("music_agent: PR 写回流程图", artifact_titles)
        self.assertIn("music_agent: 任务执行闭环图", artifact_titles)
        self.assertIn("Template: PR 写回流程图", artifact_titles)

        board_updates = [args for args in calls if args[:2] == ["whiteboard", "+update"] and "--dry-run" not in args]
        self.assertGreaterEqual(len(board_updates), 11)

    def test_project_numbered_page_cleanup_archives_children_except_maps(self):
        moved = []
        child_nodes = {
            "root": [],
            "global": [],
            "overview": [
                {"node_token": "untitled", "title": "Untitled"},
                {"node_token": "old_home", "title": "music_agent: 项目主页"},
            ],
            "bugfix": [{"node_token": "old_bug", "title": "Bugfix Retro: old"}],
            "playbooks": [{"node_token": "old_playbook", "title": "Playbook: old"}],
            "decisions": [{"node_token": "old_decision", "title": "Decision: old"}],
            "maps": [{"node_token": "map", "title": "music_agent: 架构图"}],
            "reports": [{"node_token": "old_release", "title": "Release: old"}],
        }

        def fake_list_child_nodes(_config, parent):
            return child_nodes.get(parent, [])

        def fake_archive_node(_config, node, archive_parent_token):
            moved.append((node["node_token"], archive_parent_token))

        original_list = wiki_common.list_child_nodes
        original_archive = wiki_common.archive_node
        original_ensure = wiki_common.ensure_wiki_node
        wiki_common.list_child_nodes = fake_list_child_nodes
        wiki_common.archive_node = fake_archive_node
        wiki_common.ensure_wiki_node = lambda *_args, **_kwargs: {"node_token": "archive"}
        try:
            wiki_common.cleanup_wiki_noise(
                {"wiki": {"root_node_token": "root"}},
                {
                    "archive": {"node_token": "archive_root"},
                    "global_root": {"node_token": "global"},
                    "project_overview": {"node_token": "overview"},
                    "project_bugfixes": {"node_token": "bugfix"},
                    "project_playbooks": {"node_token": "playbooks"},
                    "project_decisions": {"node_token": "decisions"},
                    "project_maps": {"node_token": "maps"},
                    "project_reports": {"node_token": "reports"},
                },
            )
        finally:
            wiki_common.list_child_nodes = original_list
            wiki_common.archive_node = original_archive
            wiki_common.ensure_wiki_node = original_ensure

        moved_tokens = {token for token, _archive in moved}
        self.assertEqual(moved_tokens, {"untitled", "old_home", "old_bug", "old_playbook", "old_decision", "old_release"})

    def test_current_project_uses_cwd_when_config_repo_path_is_different(self):
        original_repo = wiki_common.DEFAULT_REPO
        wiki_common.DEFAULT_REPO = Path("/work/lark-cli-devhub-skills")
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
            wiki_common.DEFAULT_REPO = original_repo

        self.assertEqual(project, "lark-cli-devhub-skills")

    def test_write_wiki_artifact_creates_doc_and_artifact_index(self):
        calls = []
        records = []
        written_docs = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["wiki", "+node-list"]:
                return {"data": {"items": []}}, "{}"
            if args[:2] == ["wiki", "+node-create"]:
                title = args[args.index("--title") + 1]
                token = "node_" + title.replace(" ", "_").replace("/", "_")
                return {"node_token": token, "obj_token": "doc_" + token, "url": f"https://wiki/{token}"}, "{}"
            if args[:2] == ["docs", "+fetch"]:
                return {"data": {"document": {"content": "<title>old</title>"}}}, "{}"
            if args[:2] == ["docs", "+update"]:
                return {"ok": True}, "{}"
            raise AssertionError(args)

        def fake_run_lark_with_input(args, stdin, check=True):
            calls.append(args)
            written_docs.append(stdin)
            return {"ok": True}, "{}"

        def fake_batch_upsert_records(_config, table, payloads, **_kwargs):
            for payload in payloads:
                records.append((table, payload))

        def fake_upsert_record(_config, table, payload, **_kwargs):
            records.append((table, payload))
            return {"data": {"record": {"record_id": "rec_artifact"}}}, "{}"

        original_run = wiki_common.run_lark
        original_run_with_input = wiki_common.run_lark_with_input
        original_batch_upsert = wiki_docs.batch_upsert_records
        original_upsert = wiki_writeback.upsert_record
        original_relations = wiki_writeback.write_record_relations
        original_now_iso = wiki_writeback.now_iso
        wiki_common.run_lark = fake_run_lark
        wiki_common.run_lark_with_input = fake_run_lark_with_input
        wiki_docs.batch_upsert_records = fake_batch_upsert_records
        wiki_writeback.upsert_record = fake_upsert_record
        wiki_writeback.write_record_relations = lambda *_args, **_kwargs: ["rec_relation"]
        wiki_writeback.now_iso = lambda: "2026-05-20T19:58:12+08:00"
        try:
            config = {
                "defaults": {"project": "music_agent"},
                "wiki": {"space_id": "space", "root_node_token": "root", "root_url": "https://wiki/root"},
            }
            result = wiki_docs.write_wiki_artifact(
                config,
                "Bugfixes",
                {
                    "Title": "Voice command ack mismatch",
                    "Project": "music_agent",
                    "Area": "voice",
                    "Symptom": "Command ack was routed to the wrong endpoint.",
                    "Root Cause": "Old flow audio ack assumptions were still present.",
                    "Fix Summary": "Use the current command stream ack path.",
                    "AI Summary": "Fixed command ack mismatch.",
                    "Search Keywords": "voice command ack",
                },
                base_record_id="rec_bug",
            )
        finally:
            wiki_common.run_lark = original_run
            wiki_common.run_lark_with_input = original_run_with_input
            wiki_docs.batch_upsert_records = original_batch_upsert
            wiki_writeback.upsert_record = original_upsert
            wiki_writeback.write_record_relations = original_relations
            wiki_writeback.now_iso = original_now_iso

        self.assertEqual(result["title"], "20 Bugfix Retros")
        self.assertEqual(result["entry_title"], "2026-05-20 19:58:12 - Bugfix Retro: Voice command ack mismatch (rec_bug)")
        self.assertEqual(result["mode"], "append")
        self.assertEqual(
            result["path"],
            "Dev Knowledge Hub / 10 Projects / music_agent / 20 Bugfix Retros",
        )
        self.assertTrue(result["url"].startswith("https://wiki/"))
        self.assertEqual(result["artifact_record_id"], "rec_artifact")
        self.assertEqual(result["artifact_relation_records"], ["rec_relation"])
        self.assertTrue(any("Write time: `2026-05-20 19:58:12`" in body for body in written_docs))
        self.assertTrue(any("Base record: `rec_bug`" in body for body in written_docs))
        self.assertTrue(any("## 2026-05-20 19:58:12 - Bugfix Retro: Voice command ack mismatch (rec_bug)" in body for body in written_docs))
        self.assertTrue(any("### 症状" in body and "Command ack was routed to the wrong endpoint." in body for body in written_docs))
        self.assertTrue(any("### 根因" in body and "Old flow audio ack assumptions were still present." in body for body in written_docs))
        self.assertFalse(any("### Bugfix 复盘模板" in body for body in written_docs))
        artifact_titles = [payload["Title"] for table, payload in records if table == "Artifacts"]
        self.assertIn("20 Bugfix Retros", artifact_titles)

    def test_write_report_wiki_artifact_creates_report_doc_and_artifact(self):
        records = []
        written_docs = []

        def fake_run_lark(args, check=True):
            if args[:2] == ["wiki", "+node-list"]:
                return {"data": {"items": []}}, "{}"
            if args[:2] == ["wiki", "+node-create"]:
                title = args[args.index("--title") + 1]
                token = "node_" + title.replace(" ", "_").replace("/", "_")
                return {"node_token": token, "obj_token": "doc_" + token, "url": f"https://wiki/{token}"}, "{}"
            if args[:2] == ["docs", "+fetch"]:
                return {"data": {"document": {"content": "<title>old</title>"}}}, "{}"
            if args[:2] == ["docs", "+update"]:
                return {"ok": True}, "{}"
            raise AssertionError(args)

        def fake_run_lark_with_input(_args, stdin, check=True):
            written_docs.append(stdin)
            return {"ok": True}, "{}"

        def fake_upsert_record(_config, table, payload, **_kwargs):
            records.append((table, payload))
            return {"data": {"record": {"record_id": "rec_report"}}}, "{}"

        original_run = wiki_common.run_lark
        original_run_with_input = wiki_common.run_lark_with_input
        original_upsert = wiki_writeback.upsert_record
        original_now_iso = wiki_writeback.now_iso
        wiki_common.run_lark = fake_run_lark
        wiki_common.run_lark_with_input = fake_run_lark_with_input
        wiki_writeback.upsert_record = fake_upsert_record
        wiki_writeback.now_iso = lambda: "2026-05-20T20:01:03+08:00"
        try:
            config = {
                "defaults": {"project": "music_agent"},
                "wiki": {"space_id": "space", "root_node_token": "root", "root_url": "https://wiki/root"},
            }
            result = wiki_docs.write_report_wiki_artifact(
                config,
                kind="weekly",
                project="music_agent",
                body="# Weekly Report: music_agent\n\n## Completed Work\n\n- Fixed voice command ack.\n",
            )
        finally:
            wiki_common.run_lark = original_run
            wiki_common.run_lark_with_input = original_run_with_input
            wiki_writeback.upsert_record = original_upsert
            wiki_writeback.now_iso = original_now_iso

        self.assertEqual(result["title"], "60 Reports")
        self.assertEqual(result["entry_title"], "2026-05-20 20:01:03 - Weekly Report")
        self.assertEqual(result["mode"], "append")
        self.assertEqual(
            result["path"],
            "Dev Knowledge Hub / 10 Projects / music_agent / 60 Reports",
        )
        self.assertEqual(result["artifact_record_id"], "rec_report")
        self.assertTrue(any("## 2026-05-20 20:01:03 - Weekly Report" in body for body in written_docs))
        self.assertTrue(any("### Completed Work" in body for body in written_docs))
        artifact_payloads = [payload for table, payload in records if table == "Artifacts"]
        self.assertEqual(artifact_payloads[0]["Status"], "Draft")

    def test_release_wiki_writeback_appends_to_stable_report_page(self):
        records = []
        written_docs = []

        def fake_run_lark(args, check=True):
            if args[:2] == ["wiki", "+node-list"]:
                return {"data": {"items": []}}, "{}"
            if args[:2] == ["wiki", "+node-create"]:
                title = args[args.index("--title") + 1]
                token = "node_" + title.replace(" ", "_").replace("/", "_")
                return {"node_token": token, "obj_token": "doc_" + token, "url": f"https://wiki/{token}"}, "{}"
            if args[:2] == ["docs", "+fetch"]:
                return {"data": {"document": {"content": "<title>old</title>"}}}, "{}"
            if args[:2] == ["docs", "+update"]:
                return {"ok": True}, "{}"
            raise AssertionError(args)

        def fake_run_lark_with_input(_args, stdin, check=True):
            written_docs.append(stdin)
            return {"ok": True}, "{}"

        def fake_upsert_record(_config, table, payload, **_kwargs):
            records.append((table, payload))
            return {"data": {"record": {"record_id": "rec_artifact"}}}, "{}"

        original_run = wiki_common.run_lark
        original_run_with_input = wiki_common.run_lark_with_input
        original_upsert = wiki_writeback.upsert_record
        original_relations = wiki_writeback.write_record_relations
        original_now_iso = wiki_writeback.now_iso
        wiki_common.run_lark = fake_run_lark
        wiki_common.run_lark_with_input = fake_run_lark_with_input
        wiki_writeback.upsert_record = fake_upsert_record
        wiki_writeback.write_record_relations = lambda *_args, **_kwargs: []
        wiki_writeback.now_iso = lambda: "2026-05-20T20:20:00+08:00"
        try:
            config = {
                "defaults": {"project": "music_agent"},
                "wiki": {"space_id": "space", "root_node_token": "root", "root_url": "https://wiki/root"},
            }
            result = wiki_docs.write_wiki_artifact(
                config,
                "Releases",
                {
                    "Title": "Release 2026-05-20",
                    "Project": "music_agent",
                    "Area": "Release / Main Push",
                    "Summary": "Published Wiki append behavior.",
                    "Search Keywords": "release wiki append",
                },
                base_record_id="rec_release",
            )
        finally:
            wiki_common.run_lark = original_run
            wiki_common.run_lark_with_input = original_run_with_input
            wiki_writeback.upsert_record = original_upsert
            wiki_writeback.write_record_relations = original_relations
            wiki_writeback.now_iso = original_now_iso

        self.assertEqual(result["title"], "60 Reports")
        self.assertEqual(result["path"], "Dev Knowledge Hub / 10 Projects / music_agent / 60 Reports")
        self.assertEqual(result["entry_title"], "2026-05-20 20:20:00 - Release: Release 2026-05-20 (rec_release)")
        self.assertTrue(any("### 发布摘要" in body and "Published Wiki append behavior." in body for body in written_docs))
        self.assertFalse(any("### Release 写回模板" in body for body in written_docs))
        artifact_titles = [payload["Title"] for table, payload in records if table == "Artifacts"]
        self.assertIn("60 Reports", artifact_titles)

    def test_playbook_wiki_writeback_appends_to_stable_playbook_page(self):
        calls = []
        records = []
        written_docs = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["wiki", "+node-list"]:
                return {"data": {"items": []}}, "{}"
            if args[:2] == ["wiki", "+node-create"]:
                title = args[args.index("--title") + 1]
                token = "node_" + title.replace(" ", "_").replace("/", "_")
                return {"node_token": token, "obj_token": "doc_" + token, "url": f"https://wiki/{token}"}, "{}"
            if args[:2] == ["docs", "+fetch"]:
                return {"data": {"document": {"content": "<title>old</title>"}}}, "{}"
            if args[:2] == ["docs", "+update"]:
                return {"ok": True}, "{}"
            raise AssertionError(args)

        def fake_run_lark_with_input(_args, stdin, check=True):
            written_docs.append(stdin)
            return {"ok": True}, "{}"

        def fake_upsert_record(_config, table, payload, **_kwargs):
            records.append((table, payload))
            return {"data": {"record": {"record_id": "rec_artifact"}}}, "{}"

        original_run = wiki_common.run_lark
        original_run_with_input = wiki_common.run_lark_with_input
        original_upsert = wiki_writeback.upsert_record
        original_relations = wiki_writeback.write_record_relations
        original_now_iso = wiki_writeback.now_iso
        wiki_common.run_lark = fake_run_lark
        wiki_common.run_lark_with_input = fake_run_lark_with_input
        wiki_writeback.upsert_record = fake_upsert_record
        wiki_writeback.write_record_relations = lambda *_args, **_kwargs: []
        wiki_writeback.now_iso = lambda: "2026-05-21T01:10:00+08:00"
        try:
            config = {
                "defaults": {"project": "music_agent"},
                "wiki": {"space_id": "space", "root_node_token": "root", "root_url": "https://wiki/root"},
            }
            result = wiki_docs.write_wiki_artifact(
                config,
                "Playbooks",
                {
                    "Title": "Voice command debugging",
                    "Project": "music_agent",
                    "Area": "Voice",
                    "Scenario": "Voice command stream fails",
                    "Diagnosis Order": "Check command stream, then ack result, then Volc update callback.",
                    "Commands": "pytest tests/test_voice_commands.py",
                    "Search Keywords": "voice command playbook",
                },
                base_record_id="rec_playbook",
            )
        finally:
            wiki_common.run_lark = original_run
            wiki_common.run_lark_with_input = original_run_with_input
            wiki_writeback.upsert_record = original_upsert
            wiki_writeback.write_record_relations = original_relations
            wiki_writeback.now_iso = original_now_iso

        self.assertEqual(result["title"], "30 Playbooks")
        self.assertEqual(result["entry_title"], "2026-05-21 01:10:00 - Playbook: Voice command debugging (rec_playbook)")
        self.assertTrue(any("### 适用场景" in body and "Voice command stream fails" in body for body in written_docs))
        self.assertTrue(any("pytest tests/test_voice_commands.py" in body for body in written_docs))
        self.assertFalse(any("### Playbook 模板" in body for body in written_docs))
        artifact_titles = [payload["Title"] for table, payload in records if table == "Artifacts"]
        self.assertIn("30 Playbooks", artifact_titles)

    def test_wiki_writeback_body_marks_missing_fields_without_raw_template(self):
        body = wiki_writeback.wiki_writeback_body(
            "Decisions",
            {"Title": "Keep append-only pages", "Project": "music_agent"},
            entry_title="2026-05-21 01:20:00 - Decision: Keep append-only pages",
            base_title="Decision: Keep append-only pages",
            base_record_id="rec_decision",
            write_time="2026-05-21 01:20:00",
        )

        self.assertIn("### 决策", body)
        self.assertIn("未提供", body)
        self.assertIn("### 原始结构化字段", body)
        self.assertNotIn("Decision 决策模板", body)

    def test_append_doc_content_uses_legacy_markdown_fallback(self):
        calls = []

        def fake_run_lark_with_input(_args, _stdin):
            raise RuntimeError("--command is required")

        def fake_run_lark(args, **_kwargs):
            calls.append(args)
            return {"ok": True}, "{}"

        original_run = wiki_common.run_lark
        original_run_with_input = wiki_common.run_lark_with_input
        wiki_common.run_lark = fake_run_lark
        wiki_common.run_lark_with_input = fake_run_lark_with_input
        try:
            wiki_common.append_doc_content("doc_123", "## Entry\n\nBody")
        finally:
            wiki_common.run_lark = original_run
            wiki_common.run_lark_with_input = original_run_with_input

        self.assertEqual(calls[0][calls[0].index("--command") + 1], "append")
        self.assertEqual(calls[0][calls[0].index("--doc-format") + 1], "markdown")
        self.assertEqual(calls[0][calls[0].index("--content") + 1], "## Entry\n\nBody")

    def test_whiteboard_idempotent_tokens_do_not_collide_for_chinese_titles(self):
        titles = [
            "Global: Bug 排查路径图",
            "Global: PR 写回流程图",
            "Global: 任务执行闭环图",
            "lark-cli-devhub-skills: Bug 排查路径图",
            "lark-cli-devhub-skills: PR 写回流程图",
            "lark-cli-devhub-skills: 任务执行闭环图",
        ]
        tokens = [wiki_whiteboards.idempotent_token(title) for title in titles]

        self.assertEqual(len(tokens), len(set(tokens)))
        self.assertTrue(all(token.startswith("devhub-") for token in tokens))

    def test_svg_conversion_uses_local_cache(self):
        class Result:
            returncode = 0
            stdout = '{"code":0,"data":{"nodes":[]}}'
            stderr = ""

        calls = []
        original_home = wiki_whiteboards.DEVHUB_HOME
        original_run = wiki_whiteboards.subprocess.run

        def fake_run(args, **_kwargs):
            calls.append(args)
            return Result()

        with tempfile.TemporaryDirectory() as temp_dir:
            wiki_whiteboards.DEVHUB_HOME = Path(temp_dir)
            wiki_whiteboards.subprocess.run = fake_run
            try:
                first, first_format = wiki_whiteboards.whiteboard_update_input("map.svg", "<svg></svg>")
                second, second_format = wiki_whiteboards.whiteboard_update_input("map.svg", "<svg></svg>")
            finally:
                wiki_whiteboards.DEVHUB_HOME = original_home
                wiki_whiteboards.subprocess.run = original_run

        self.assertEqual(first, second)
        self.assertEqual(first_format, "raw")
        self.assertEqual(second_format, "raw")
        self.assertEqual(len(calls), 1)

    def test_existing_whiteboard_is_preserved_unless_overwrite_is_enabled(self):
        original_env = wiki_whiteboards.os.environ.get("DEVHUB_WHITEBOARD_OVERWRITE")
        try:
            wiki_whiteboards.os.environ.pop("DEVHUB_WHITEBOARD_OVERWRITE", None)
            self.assertTrue(wiki_whiteboards.should_preserve_existing_whiteboard(newly_created=False))
            self.assertFalse(wiki_whiteboards.should_preserve_existing_whiteboard(newly_created=True))

            wiki_whiteboards.os.environ["DEVHUB_WHITEBOARD_OVERWRITE"] = "1"
            self.assertFalse(wiki_whiteboards.should_preserve_existing_whiteboard(newly_created=False))
        finally:
            if original_env is None:
                wiki_whiteboards.os.environ.pop("DEVHUB_WHITEBOARD_OVERWRITE", None)
            else:
                wiki_whiteboards.os.environ["DEVHUB_WHITEBOARD_OVERWRITE"] = original_env


if __name__ == "__main__":
    unittest.main()
