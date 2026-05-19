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
        self.assertEqual(payload["visible_fields"], ["Title", "Status", "AI Summary"])


if __name__ == "__main__":
    unittest.main()
