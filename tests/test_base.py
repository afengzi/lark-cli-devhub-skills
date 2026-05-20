import json
import unittest

import scripts.devhub_lib.base as base_module


class BaseProvisionTests(unittest.TestCase):
    def test_existing_live_field_is_hydrated_and_not_recreated(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+field-list"]:
                return {
                    "data": {
                        "fields": [
                            {"name": "Title", "id": "fld_title", "type": "text"},
                            {"name": "Related Release Relation", "id": "fld_link", "type": "link", "bidirectional": False},
                        ]
                    }
                }, "{}"
            if args[:2] == ["base", "+field-create"]:
                return {"field": {"field_id": "fld_created"}}, "{}"
            raise AssertionError(args)

        original = base_module.run_lark
        base_module.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {"Tasks": {"id": "tbl_tasks", "fields": {}}},
                }
            }
            schema = {
                "tables": [
                    {
                        "name": "Tasks",
                        "fields": [
                            {"type": "text", "name": "Title"},
                            {
                                "type": 18,
                                "field_name": "Related Release Relation",
                                "property": {"multiple": True, "table_id": "Releases"},
                            },
                            {"type": "text", "name": "Next Action"},
                        ],
                    }
                ]
            }
            base_module.create_tables_and_fields(config, schema)
        finally:
            base_module.run_lark = original

        field_creates = [args for args in calls if args[:2] == ["base", "+field-create"]]
        self.assertEqual(len(field_creates), 1)
        self.assertIn("Next Action", " ".join(field_creates[0]))
        self.assertEqual(config["base"]["tables"]["Tasks"]["fields"]["Related Release Relation"], "fld_link")

    def test_relation_field_target_table_names_are_resolved_and_translated_before_create(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+field-list"]:
                return {"data": {"fields": []}}, "{}"
            if args[:2] == ["base", "+field-create"]:
                return {"field": {"field_id": "fld_relation"}}, "{}"
            raise AssertionError(args)

        original = base_module.run_lark
        base_module.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {
                        "Tasks": {"id": "tbl_tasks", "fields": {}},
                        "Releases": {"id": "tbl_releases", "fields": {}},
                    },
                }
            }
            schema = {
                "tables": [
                    {
                        "name": "Tasks",
                        "fields": [
                            {
                                "type": 18,
                                "field_name": "Related Release Relation",
                                "property": {"multiple": True, "table_id": "Releases"},
                            }
                        ],
                    }
                ]
            }
            base_module.create_tables_and_fields(config, schema)
        finally:
            base_module.run_lark = original

        field_creates = [args for args in calls if args[:2] == ["base", "+field-create"]]
        self.assertEqual(len(field_creates), 1)
        payload = json.loads(field_creates[0][field_creates[0].index("--json") + 1])
        self.assertEqual(payload["type"], "link")
        self.assertEqual(payload["name"], "Related Release Relation")
        self.assertEqual(payload["link_table"], "tbl_releases")
        self.assertFalse(payload["bidirectional"])

    def test_upsert_record_can_match_existing_record_by_title_and_project(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+record-search"]:
                return {
                    "data": {
                        "fields": ["Title", "Project"],
                        "data": [["Template: PR 写回流程图", "Global"]],
                        "record_id_list": ["rec_existing"],
                    }
                }, "{}"
            if args[:2] == ["base", "+record-upsert"]:
                return {"record_id": "rec_existing"}, "{}"
            raise AssertionError(args)

        original = base_module.run_lark
        base_module.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {"Artifacts": {"id": "tbl_artifacts", "fields": {}}},
                }
            }
            base_module.upsert_record(
                config,
                "Artifacts",
                {"Title": "Template: PR 写回流程图", "Project": "Global", "Status": "Active"},
                match_fields=["Title", "Project"],
            )
        finally:
            base_module.run_lark = original

        upserts = [args for args in calls if args[:2] == ["base", "+record-upsert"]]
        self.assertEqual(len(upserts), 1)
        self.assertIn("--record-id", upserts[0])
        self.assertEqual(upserts[0][upserts[0].index("--record-id") + 1], "rec_existing")

    def test_batch_upsert_records_creates_missing_records_in_one_batch(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+record-list"]:
                return {
                    "data": {
                        "fields": ["Title", "Project", "Status"],
                        "data": [],
                        "record_id_list": [],
                        "has_more": False,
                    }
                }, "{}"
            if args[:2] == ["base", "+record-batch-create"]:
                return {"record_id_list": ["rec_a", "rec_b"]}, "{}"
            raise AssertionError(args)

        original = base_module.run_lark
        base_module.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {"Artifacts": {"id": "tbl_artifacts", "fields": {}}},
                }
            }
            base_module.batch_upsert_records(
                config,
                "Artifacts",
                [
                    {"Title": "A", "Project": "Global", "Status": "Active"},
                    {"Title": "B", "Project": "Global", "Status": "Active"},
                ],
                match_fields=["Title", "Project"],
            )
        finally:
            base_module.run_lark = original

        batch_creates = [args for args in calls if args[:2] == ["base", "+record-batch-create"]]
        self.assertEqual(len(batch_creates), 1)
        payload = json.loads(batch_creates[0][batch_creates[0].index("--json") + 1])
        self.assertEqual(payload["fields"], ["Title", "Project", "Status"])
        self.assertEqual(len(payload["rows"]), 2)

    def test_batch_upsert_records_skips_unchanged_existing_records(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+record-list"]:
                return {
                    "data": {
                        "fields": ["Title", "Project", "Status"],
                        "data": [["A", "Global", ["Active"]]],
                        "record_id_list": ["rec_existing"],
                        "has_more": False,
                    }
                }, "{}"
            raise AssertionError(args)

        original = base_module.run_lark
        base_module.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {"Artifacts": {"id": "tbl_artifacts", "fields": {}}},
                }
            }
            base_module.batch_upsert_records(
                config,
                "Artifacts",
                [{"Title": "A", "Project": "Global", "Status": "Active"}],
                match_fields=["Title", "Project"],
            )
        finally:
            base_module.run_lark = original

        self.assertFalse(any(args[:2] == ["base", "+record-upsert"] for args in calls))
        self.assertFalse(any(args[:2] == ["base", "+record-batch-create"] for args in calls))

    def test_upsert_record_filters_unknown_fields_when_schema_is_lightweight(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+record-search"]:
                return {"data": {"fields": ["Title"], "data": [], "record_id_list": []}}, "{}"
            if args[:2] == ["base", "+record-upsert"]:
                return {"record_id": "rec_bug"}, "{}"
            raise AssertionError(args)

        original = base_module.run_lark
        base_module.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {
                        "Projects": {"id": "tbl_projects", "fields": {"Title": "fld", "Project": "fld"}},
                        "Tasks": {"id": "tbl_tasks", "fields": {"Title": "fld", "Project": "fld"}},
                        "Bugfixes": {
                            "id": "tbl_bugs",
                            "fields": {
                                "Title": "fld",
                                "Project": "fld",
                                "Status": "fld",
                            },
                        },
                    },
                }
            }
            base_module.upsert_record(
                config,
                "Bugfixes",
                {
                    "Title": "Login fixed",
                    "Project": "demo-project",
                    "Related Task": "Fix login",
                    "Related Task Relation": [{"id": "rec_task"}],
                    "Status": "Fixed",
                },
                match_fields=["Title", "Project"],
            )
        finally:
            base_module.run_lark = original

        upserts = [args for args in calls if args[:2] == ["base", "+record-upsert"]]
        self.assertEqual(len(upserts), 1)
        payload = json.loads(upserts[0][upserts[0].index("--json") + 1])
        self.assertEqual(payload, {"Title": "Login fixed", "Project": "demo-project", "Status": "Fixed"})

    def test_cleanup_deprecated_relation_fields_deletes_only_relation_columns(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+field-list"]:
                return {
                    "data": {
                        "fields": [
                            {"name": "Title", "id": "fld_title", "type": "text"},
                            {"name": "Project Relation", "id": "fld_project", "type": "link"},
                            {"name": "Related Task Relation", "id": "fld_task", "type": "link"},
                            {"name": "Related Areas Link", "id": "fld_area_link", "type": "link"},
                            {"name": "Related Task", "id": "fld_task_text", "type": "text"},
                        ]
                    }
                }, "{}"
            if args[:2] == ["base", "+field-delete"]:
                return {"deleted": True}, "{}"
            raise AssertionError(args)

        original = base_module.run_lark
        base_module.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {
                        "Bugfixes": {
                            "id": "tbl_bugs",
                            "fields": {
                                "Title": "fld_title",
                                "Project Relation": "fld_project",
                                "Related Task Relation": "fld_task",
                                "Related Areas Link": "fld_area_link",
                                "Related Task": "fld_task_text",
                            },
                        },
                        "Record Relations": {"id": "tbl_edges", "fields": {"Title": "fld_title"}},
                    },
                }
            }
            removed = base_module.cleanup_deprecated_relation_fields(config)
        finally:
            base_module.run_lark = original

        self.assertEqual(
            [item["field"] for item in removed],
            ["Project Relation", "Related Task Relation", "Related Areas Link", "Related Task"],
        )
        deletes = [args for args in calls if args[:2] == ["base", "+field-delete"]]
        self.assertEqual(len(deletes), 4)
        self.assertTrue(all("--yes" in args for args in deletes))
        self.assertNotIn("Project Relation", config["base"]["tables"]["Bugfixes"]["fields"])
        self.assertNotIn("Related Task", config["base"]["tables"]["Bugfixes"]["fields"])


if __name__ == "__main__":
    unittest.main()
