import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class SchemaTests(unittest.TestCase):
    def test_project_facts_table_exists_with_required_fields(self):
        schema = json.loads((ROOT / "templates" / "base-schema.json").read_text(encoding="utf-8"))
        tables = {table["name"]: table for table in schema["tables"]}
        self.assertIn("Project Facts", tables)
        fields = {field["name"] for field in tables["Project Facts"]["fields"]}
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


if __name__ == "__main__":
    unittest.main()
