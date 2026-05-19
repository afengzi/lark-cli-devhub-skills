import unittest

from scripts.devhub_lib.search import FULL_RECALL_TABLES, search_devhub


class SearchCoverageTests(unittest.TestCase):
    def test_full_recall_tables_include_v15_records(self):
        self.assertEqual(
            FULL_RECALL_TABLES,
            [
                "Tasks",
                "Bugfixes",
                "AI Runs",
                "Releases",
                "Decisions",
                "Project Facts",
                "Artifacts",
                "Pitfalls",
                "Playbooks",
                "Areas",
            ],
        )

    def test_search_reports_coverage_and_results(self):
        calls = []

        def fake_run_lark(args, check=True):
            calls.append(args)
            table_id = args[args.index("--table-id") + 1]
            return {"items": [{"table": table_id}]}, "{}"

        config = {
            "base": {
                "token": "base-token",
                "tables": {
                    "Tasks": {"id": "tbl_tasks"},
                    "Bugfixes": {"id": "tbl_bugfixes"},
                    "AI Runs": {"id": "tbl_ai_runs"},
                    "Releases": {"id": "tbl_releases"},
                    "Decisions": {"id": "tbl_decisions"},
                    "Project Facts": {"id": "tbl_project_facts"},
                    "Artifacts": {"id": "tbl_artifacts"},
                    "Pitfalls": {"id": "tbl_pitfalls"},
                    "Playbooks": {"id": "tbl_playbooks"},
                    "Areas": {"id": "tbl_areas"},
                },
            }
        }

        result = search_devhub(config, "music-agent", "voice command stream", run_lark_func=fake_run_lark)

        self.assertEqual(result["project"], "music-agent")
        self.assertEqual(result["coverage"], FULL_RECALL_TABLES)
        self.assertEqual(result["missing_for_full_recall"], [])
        self.assertEqual(set(result["results"].keys()), set(FULL_RECALL_TABLES))
        self.assertEqual(len(calls), len(FULL_RECALL_TABLES))


if __name__ == "__main__":
    unittest.main()
