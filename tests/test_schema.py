import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def field_name(field):
    return field.get("name") or field.get("field_name")


class SchemaTests(unittest.TestCase):
    def test_project_facts_table_exists_with_required_fields(self):
        schema = json.loads((ROOT / "templates" / "base-schema.json").read_text(encoding="utf-8"))
        tables = {table["name"]: table for table in schema["tables"]}
        self.assertIn("Project Facts", tables)
        fields = {field_name(field) for field in tables["Project Facts"]["fields"]}
        self.assertTrue(
            {
                "Title",
                "Project",
                "Area",
                "Status",
                "Fact",
                "Current Truth",
                "Retired Paths",
                "Source",
                "Review Trigger",
                "Last Reviewed At",
                "AI Summary",
                "Search Keywords",
            }.issubset(fields)
        )

    def test_seed_includes_project_facts_key(self):
        seed = json.loads((ROOT / "templates" / "seed.example.json").read_text(encoding="utf-8"))
        self.assertIn("Project Facts", seed)
        self.assertIsInstance(seed["Project Facts"], list)
        self.assertIn("Record Relations", seed)

    def test_schema_is_lightweight_and_has_record_relations(self):
        schema = json.loads((ROOT / "templates" / "base-schema.json").read_text(encoding="utf-8"))
        tables = {table["name"]: table for table in schema["tables"]}
        self.assertIn("Record Relations", tables)

        for table_name, table in tables.items():
            fields = {field_name(field): field for field in table["fields"]}
            self.assertIn("ID", fields)
            if "Source URL" in fields:
                self.assertEqual(fields["Source URL"].get("style"), {"type": "url"})
            for field in fields.values():
                if field.get("type") == "datetime":
                    self.assertEqual(field.get("style"), {"format": "yyyy-MM-dd HH:mm"})
            if table_name not in {"Projects", "Record Relations"}:
                self.assertEqual(fields["Project"]["type"], "text")
            if table_name not in {"Projects", "Areas", "Record Relations"}:
                self.assertEqual(fields["Area"]["type"], "text")
            self.assertFalse(any(name and "Relation" in name for name in fields if table_name != "Record Relations"))
            if table_name != "Record Relations":
                self.assertFalse(any(name and name.startswith("Related ") for name in fields))

        relation_fields = {field_name(field): field for field in tables["Record Relations"]["fields"]}
        self.assertEqual(relation_fields["Relation Type"]["type"], "select")
        self.assertEqual(relation_fields["Source Table"]["type"], "text")
        self.assertEqual(relation_fields["Source Record ID"]["type"], "text")
        self.assertEqual(relation_fields["Target Table"]["type"], "text")
        self.assertEqual(relation_fields["Target Ref"]["type"], "text")

        project_fields = {field_name(field): field for field in tables["Projects"]["fields"]}
        self.assertEqual(project_fields["Repo URL"].get("style"), {"type": "url"})
        self.assertEqual(project_fields["Wiki URL"].get("style"), {"type": "url"})
        task_fields = {field_name(field): field for field in tables["Tasks"]["fields"]}
        self.assertEqual(task_fields["Feishu Task URL"].get("style"), {"type": "url"})


if __name__ == "__main__":
    unittest.main()
