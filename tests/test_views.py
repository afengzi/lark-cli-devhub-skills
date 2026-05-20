import json
import unittest

import scripts.devhub_lib.views as views


class BaseViewTests(unittest.TestCase):
    def test_ensure_base_views_creates_view_and_sets_visible_fields(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+view-list"]:
                return {"data": {"items": []}}, "{}"
            if args[:2] == ["base", "+view-create"]:
                return {"view_id": "viw_tasks"}, "{}"
            if args[:2] in (["base", "+view-set-visible-fields"], ["base", "+view-set-filter"]):
                return {"ok": True}, "{}"
            raise AssertionError(args)

        original = views.run_lark
        views.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {
                        "Tasks": {
                            "id": "tbl_tasks",
                            "fields": {"Title": "fld_title", "Status": "fld_status", "AI Summary": "fld_ai"},
                        }
                    },
                }
            }
            changed = views.ensure_base_views(
                config,
                {
                    "Tasks": [
                        {
                            "name": "Task Board",
                            "type": "grid",
                            "visible_fields": ["Title", "Status", "Missing Field", "AI Summary"],
                            "filter": {"logic": "and", "conditions": [["Status", "intersects", ["Doing"]]]},
                        }
                    ]
                },
            )
        finally:
            views.run_lark = original

        self.assertEqual(changed, [{"table": "Tasks", "view": "Task Board", "action": "created"}])
        visible_calls = [args for args in calls if args[:2] == ["base", "+view-set-visible-fields"]]
        self.assertEqual(len(visible_calls), 1)
        payload = json.loads(visible_calls[0][visible_calls[0].index("--json") + 1])
        self.assertEqual(payload["visible_fields"], ["fld_title", "fld_status", "fld_ai"])
        filter_calls = [args for args in calls if args[:2] == ["base", "+view-set-filter"]]
        filter_payload = json.loads(filter_calls[0][filter_calls[0].index("--json") + 1])
        self.assertEqual(filter_payload["conditions"][0][0], "fld_status")

    def test_ensure_base_views_recreates_view_when_type_changes_and_applies_group(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            if args[:2] == ["base", "+view-list"]:
                return {"data": {"views": [{"id": "vew_old", "name": "Task Board", "type": "grid"}]}}, "{}"
            if args[:2] == ["base", "+view-delete"]:
                return {"deleted": True}, "{}"
            if args[:2] == ["base", "+view-create"]:
                return {"view_id": "vew_new"}, "{}"
            if args[:2] in (
                ["base", "+view-set-visible-fields"],
                ["base", "+view-set-filter"],
                ["base", "+view-set-group"],
                ["base", "+view-set-card"],
            ):
                return {"ok": True}, "{}"
            raise AssertionError(args)

        original = views.run_lark
        views.run_lark = fake_run_lark
        try:
            config = {
                "base": {
                    "token": "base-token",
                    "tables": {
                        "Tasks": {
                            "id": "tbl_tasks",
                            "fields": {"Title": "fld_title", "Status": "fld_status"},
                        }
                    },
                }
            }
            views.ensure_base_views(
                config,
                {
                    "Tasks": [
                        {
                            "name": "Task Board",
                            "type": "kanban",
                            "visible_fields": ["Title", "Status"],
                            "group": {"group_config": [{"field": "Status", "desc": False}]},
                            "card": {"cover_field": None},
                        }
                    ]
                },
            )
        finally:
            views.run_lark = original

        self.assertTrue(any(args[:2] == ["base", "+view-delete"] and "--yes" in args for args in calls))
        creates = [args for args in calls if args[:2] == ["base", "+view-create"]]
        payload = json.loads(creates[0][creates[0].index("--json") + 1])
        self.assertEqual(payload["type"], "kanban")
        group_calls = [args for args in calls if args[:2] == ["base", "+view-set-group"]]
        self.assertEqual(len(group_calls), 1)
        group_payload = json.loads(group_calls[0][group_calls[0].index("--json") + 1])
        self.assertEqual(group_payload["group_config"][0]["field"], "fld_status")


if __name__ == "__main__":
    unittest.main()
