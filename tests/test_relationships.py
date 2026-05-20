import unittest

import scripts.devhub_lib.relationships as relationships


class RelationshipWriteTests(unittest.TestCase):
    def test_build_relation_payloads_from_text_hints(self):
        payloads = relationships.build_relation_payloads(
            "Bugfixes",
            "rec_bug",
            {
                "Title": "Fix login",
                "Project": "demo",
                "Area": "auth",
                "Relation Hints": "Tasks: rec_task",
                "AI Summary": "Fixed auth redirect.",
            },
        )

        self.assertEqual(len(payloads), 1)
        payload = payloads[0]
        self.assertEqual(payload["Source Table"], "Bugfixes")
        self.assertEqual(payload["Source Record ID"], "rec_bug")
        self.assertEqual(payload["Target Table"], "Tasks")
        self.assertEqual(payload["Target Record ID"], "rec_task")
        self.assertEqual(payload["Relation Type"], "fixes")

    def test_write_record_relations_upserts_edge_table(self):
        calls = []

        def fake_upsert_record(config, table, payload, **kwargs):
            calls.append((table, payload, kwargs))
            return {"record_id": "rec_edge"}, "{}"

        original = relationships.upsert_record
        relationships.upsert_record = fake_upsert_record
        try:
            config = {"base": {"tables": {"Record Relations": {"id": "tbl_edges"}}}}
            result = relationships.write_record_relations(
                config,
                "AI Runs",
                "rec_run",
                {
                    "Title": "Codex run",
                    "Project": "demo",
                    "Related Bugfix": "Fix login",
                    "AI Summary": "Investigated and fixed login.",
                },
            )
        finally:
            relationships.upsert_record = original

        self.assertEqual(result, ["rec_edge"])
        self.assertEqual(len(calls), 1)
        table, payload, kwargs = calls[0]
        self.assertEqual(table, "Record Relations")
        self.assertEqual(payload["Relation Type"], "evidence_for")
        self.assertEqual(payload["Target Table"], "Bugfixes")
        self.assertEqual(
            kwargs["match_fields"],
            ["Source Table", "Source Record ID", "Relation Type", "Target Table", "Target Ref"],
        )


if __name__ == "__main__":
    unittest.main()
