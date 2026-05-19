# Lark CLI Dev Hub V1.5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the V1.5 Dev Hub workflow layer so AI IDEs/CLIs can search prior development memory, write reliable Feishu/Lark evidence, and progressively add hooks, PR writeback, report drafts, and Whiteboard drafts.

**Architecture:** Keep the current small orchestrator skill plus focused domain skills. Add workflow skills and helper modules that compose existing Base/Docs/Task/Whiteboard behavior without making domain skills depend on each other. Every write path must produce a receipt or outbox item, and every search path must disclose which record types it covered.

**Tech Stack:** Markdown Agent Skills, Python 3.10+ standard library, `lark-cli`, Feishu/Lark Base/Docs/Wiki/Whiteboard, Git hooks, GitHub Actions templates, cron-compatible shell commands.

---

## Scope Check

The V1.5 spec spans search, schema, receipts, workflow skills, GitHub templates, report drafts, and Whiteboard drafts. These are connected by one reliability contract: `manual or automated trigger -> write attempt -> receipt or outbox`. Keep them in one plan, but land them as small commits so the reliable baseline is shippable before automation layers are enabled.

## File Structure

Create or modify these files:

```text
tests/
  test_validate.py
  test_search.py
  test_records.py
  test_report_draft.py
  test_schema.py

scripts/
  validate.py
  devhub.py
  devhub_lib/
    cli.py
    commands.py
    records.py
    search.py
    reports.py
    whiteboard.py

templates/
  base-schema.json
  seed.example.json
  github-pr-writeback.yml
  cron-report.yml
  whiteboard-draft.md
  report-daily.md
  report-weekly.md
  report-release.md

skills/
  lark-cli-devhub/
    SKILL.md
    references/
      knowledge-model.md
      search-policy.md
      writeback-flows.md
      automation-patterns.md
      report-loop.md
      whiteboard-loop.md
  lark-cli-devhub-code-loop/SKILL.md
  lark-cli-devhub-report-loop/SKILL.md
  lark-cli-devhub-pr-writeback/SKILL.md
  lark-cli-devhub-whiteboard-loop/SKILL.md

docs/
  architecture.md
  marketplaces.md
  lark-cli-capability-map.md
  superpowers/specs/2026-05-20-lark-cli-devhub-v15-design.md
```

Keep Python logic in focused modules:

- `search.py`: record-type coverage, query construction, table search.
- `records.py`: receipt/outbox format and record writes.
- `reports.py`: deterministic Markdown report drafts from structured records.
- `whiteboard.py`: deterministic Markdown/Whiteboard draft generation.
- `commands.py`: CLI command orchestration only.

## Task 1: Add A Test Harness And Validation Hygiene

**Files:**
- Create: `tests/test_validate.py`
- Modify: `scripts/validate.py`

- [ ] **Step 1: Create validation tests**

Create `tests/test_validate.py`:

```python
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
```

- [ ] **Step 2: Run the failing validation tests**

Run:

```bash
python3 -m unittest tests/test_validate.py -v
```

Expected: one test fails because `.superpowers/` is currently scanned.

- [ ] **Step 3: Add ignored local directories**

In `scripts/validate.py`, add this near the constants:

```python
IGNORED_DIRS = {".git", ".superpowers", "__pycache__"}
```

Replace the `scan_forbidden()` loop with:

```python
def is_ignored_path(path: Path) -> bool:
    return any(part in IGNORED_DIRS for part in path.relative_to(ROOT).parts)


def scan_forbidden() -> list[str]:
    errors: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or is_ignored_path(path):
            continue
        if path == Path(__file__).resolve():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern, label in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                errors.append(f"{path.relative_to(ROOT)} contains forbidden content: {label}")
    return errors
```

- [ ] **Step 4: Verify validation tests pass**

Run:

```bash
python3 -m unittest tests/test_validate.py -v
```

Expected: both tests pass.

- [ ] **Step 5: Run repository validation**

Run:

```bash
python3 scripts/validate.py
```

Expected: `ok`.

- [ ] **Step 6: Commit**

```bash
git add scripts/validate.py tests/test_validate.py
git commit -m "test: cover validation ignore rules" # reviewed
```

## Task 2: Add Search Coverage Metadata And Full V1.5 Table Set

**Files:**
- Create: `scripts/devhub_lib/search.py`
- Create: `tests/test_search.py`
- Modify: `scripts/devhub_lib/commands.py`

- [ ] **Step 1: Write search tests**

Create `tests/test_search.py`:

```python
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
```

- [ ] **Step 2: Run the failing search tests**

Run:

```bash
python3 -m unittest tests/test_search.py -v
```

Expected: import fails because `scripts/devhub_lib/search.py` does not exist.

- [ ] **Step 3: Implement `search.py`**

Create `scripts/devhub_lib/search.py`:

```python
from __future__ import annotations

import json
from typing import Any, Callable

from .lark import run_lark


FULL_RECALL_TABLES = [
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
]

SEARCH_FIELDS = ["Title", "AI Summary", "Search Keywords"]
SELECT_FIELDS = ["Title", "Project", "Area", "Status", "AI Summary", "Search Keywords", "Source URL"]


def build_record_search_query(query: str) -> dict[str, Any]:
    return {
        "keyword": query,
        "search_fields": SEARCH_FIELDS,
        "select_fields": SELECT_FIELDS,
        "limit": 10,
    }


def search_devhub(
    config: dict[str, Any],
    project: str,
    query: str,
    *,
    tables: list[str] | None = None,
    run_lark_func: Callable[..., tuple[dict[str, Any], str]] = run_lark,
) -> dict[str, Any]:
    base = config.get("base", {})
    token = base.get("token")
    if not token:
        raise RuntimeError("Dev Hub Base is not configured yet.")

    requested = tables or FULL_RECALL_TABLES
    results: dict[str, Any] = {}
    for table in requested:
        table_id = base.get("tables", {}).get(table, {}).get("id", table)
        try:
            data, stdout = run_lark_func(
                [
                    "base",
                    "+record-search",
                    "--as",
                    "user",
                    "--base-token",
                    token,
                    "--table-id",
                    table_id,
                    "--json",
                    json.dumps(build_record_search_query(query), ensure_ascii=False),
                    "--format",
                    "json",
                ],
                check=False,
            )
            results[table] = data if data else stdout.strip()
        except Exception as exc:
            results[table] = {"error": str(exc)}

    missing = [table for table in FULL_RECALL_TABLES if table not in requested]
    return {
        "project": project,
        "query": query,
        "coverage": requested,
        "missing_for_full_recall": missing,
        "results": results,
    }
```

- [ ] **Step 4: Update `command_search` to delegate**

In `scripts/devhub_lib/commands.py`, add:

```python
from .search import search_devhub
```

Replace `command_search()` with:

```python
def command_search(args: Any) -> int:
    config = load_config()
    try:
        result = search_devhub(config, args.project, args.query)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0
```

- [ ] **Step 5: Verify search tests pass**

Run:

```bash
python3 -m unittest tests/test_search.py -v
```

Expected: tests pass.

- [ ] **Step 6: Verify CLI help still works**

Run:

```bash
python3 scripts/devhub.py --help
```

Expected: help lists existing commands.

- [ ] **Step 7: Commit**

```bash
git add scripts/devhub_lib/search.py scripts/devhub_lib/commands.py tests/test_search.py
git commit -m "feat: report devhub search coverage" # reviewed
```

## Task 3: Add Project Facts To Schema And Seed Data

**Files:**
- Create: `tests/test_schema.py`
- Modify: `templates/base-schema.json`
- Modify: `templates/seed.example.json`
- Modify: `skills/lark-cli-devhub/references/knowledge-model.md`
- Modify: `skills/lark-cli-devhub/references/search-policy.md`

- [ ] **Step 1: Write schema tests**

Create `tests/test_schema.py`:

```python
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
```

- [ ] **Step 2: Run failing schema tests**

Run:

```bash
python3 -m unittest tests/test_schema.py -v
```

Expected: fails because `Project Facts` is not in the schema.

- [ ] **Step 3: Add the Project Facts table**

In `templates/base-schema.json`, add this table after `Decisions` and before `Releases`:

```json
{
  "name": "Project Facts",
  "fields": [
    {"type": "text", "name": "Title"},
    {"type": "text", "name": "Project"},
    {"type": "text", "name": "Area"},
    {
      "type": "select",
      "name": "Status",
      "multiple": false,
      "options": [
        {"name": "Current", "hue": "Green", "lightness": "Light"},
        {"name": "Needs Review", "hue": "Orange", "lightness": "Light"},
        {"name": "Retired", "hue": "Gray", "lightness": "Light"}
      ]
    },
    {"type": "text", "name": "Tags"},
    {"type": "text", "name": "AI Summary"},
    {"type": "text", "name": "Search Keywords"},
    {"type": "text", "name": "Source URL"},
    {"type": "datetime", "name": "Last Reviewed At"},
    {"type": "text", "name": "Fact"},
    {"type": "text", "name": "Current Truth"},
    {"type": "text", "name": "Retired Paths"},
    {"type": "text", "name": "Source"},
    {"type": "text", "name": "Review Trigger"},
    {"type": "text", "name": "Related Decisions"},
    {"type": "text", "name": "Related Artifacts"}
  ]
}
```

- [ ] **Step 4: Add seed data key**

In `templates/seed.example.json`, add this top-level key near `Decisions`:

```json
"Project Facts": [
  {
    "Title": "Project Facts store current implementation truth",
    "Project": "Global",
    "Area": "Dev Hub",
    "Status": "Current",
    "Fact": "Project-specific current truths and retired paths live in Project Facts, not in public skills.",
    "Current Truth": "Agents should search Project Facts before relying on old code paths or stale architecture notes.",
    "Retired Paths": "Project-specific retired endpoints, modules, or workflows should be recorded here.",
    "Source": "Dev Hub V1.5 design",
    "Review Trigger": "Review after architecture changes, PR review feedback, or repeated stale-agent behavior.",
    "AI Summary": "Project Facts prevent stale AI behavior by storing current implementation truth and retired paths.",
    "Search Keywords": "project facts current truth retired paths stale AI"
  }
]
```

Keep JSON syntax valid by adding commas around neighboring keys.

- [ ] **Step 5: Update knowledge model docs**

In `skills/lark-cli-devhub/references/knowledge-model.md`, ensure the Base row and core tables include `Project Facts`. Add this bullet:

```markdown
- `Project Facts`: current implementation truths, retired paths, invariants, source, and review trigger. Use this before trusting older docs or old bug paths.
```

- [ ] **Step 6: Update search policy docs**

In `skills/lark-cli-devhub/references/search-policy.md`, update the read order to:

```markdown
1. `Project Facts`: current truths and retired paths.
2. `Pitfalls`: traps and forbidden approaches.
3. `Playbooks`: diagnosis order and evidence requirements.
4. `Bugfixes`: old root causes and verification.
5. `AI Runs`: previous agent actions, evidence, and caveats.
6. `Releases`: what reached the default branch and when.
7. `Decisions`: constraints that explain why the system is shaped this way.
8. `Tasks`: current work state and blockers.
9. `Artifacts`: linked docs, whiteboards, PRs, commits, and files.
10. `Areas`: code paths and risk level.
```

- [ ] **Step 7: Verify schema tests**

Run:

```bash
python3 -m unittest tests/test_schema.py -v
python3 -m json.tool templates/base-schema.json >/tmp/devhub-schema.json
python3 -m json.tool templates/seed.example.json >/tmp/devhub-seed.json
```

Expected: tests pass and JSON formatting commands succeed.

- [ ] **Step 8: Commit**

```bash
git add templates/base-schema.json templates/seed.example.json tests/test_schema.py skills/lark-cli-devhub/references/knowledge-model.md skills/lark-cli-devhub/references/search-policy.md
git commit -m "feat: add project facts model" # reviewed
```

## Task 4: Upgrade Receipt And Outbox Shape

**Files:**
- Create: `tests/test_records.py`
- Modify: `scripts/devhub_lib/records.py`
- Modify: `skills/lark-cli-devhub/references/writeback-flows.md`

- [ ] **Step 1: Write record format tests**

Create `tests/test_records.py`:

```python
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.devhub_lib.records import write_outbox, write_receipt


class RecordEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cwd = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_write_receipt_uses_v15_shape(self):
        with patch("scripts.devhub_lib.records.repo_runtime_dir", return_value=self.cwd / ".devhub" / "receipts"):
            path = write_receipt(
                self.cwd,
                "record-ai-run",
                "rec123",
                "AI run summary",
                {
                    "table": "AI Runs",
                    "payload_title": "Investigated voice command stream",
                    "source": {"type": "manual", "commit": "abc123", "pr": ""},
                },
            )

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["operation"], "record-ai-run")
        self.assertEqual(data["target"]["table"], "AI Runs")
        self.assertEqual(data["target"]["record_id"], "rec123")
        self.assertEqual(data["source"]["type"], "manual")
        self.assertEqual(data["summary"], "AI run summary")

    def test_write_outbox_uses_v15_shape(self):
        with patch("scripts.devhub_lib.records.repo_runtime_dir", return_value=self.cwd / ".devhub" / "outbox"):
            path = write_outbox(
                self.cwd,
                "record-release",
                {"table": "Releases", "payload": {"Title": "Release"}},
                "missing scope",
            )

        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(data["operation"], "record-release")
        self.assertEqual(data["error"], "missing scope")
        self.assertEqual(data["payload"]["table"], "Releases")
        self.assertEqual(data["retry_count"], 0)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run failing record tests**

Run:

```bash
python3 -m unittest tests/test_records.py -v
```

Expected: receipt/outbox assertions fail because the current shape uses `kind`.

- [ ] **Step 3: Add structured receipt data**

In `scripts/devhub_lib/records.py`, update `write_receipt()` to this shape while keeping `kind` for backward compatibility:

```python
def write_receipt(cwd: Path, kind: str, record_url: str, summary: str, extra: dict[str, Any] | None = None) -> Path:
    receipts = repo_runtime_dir(cwd, "receipt_dir")
    receipts.mkdir(parents=True, exist_ok=True)
    extra = extra or {}
    source = extra.get("source") or {"type": "manual", "commit": "", "pr": ""}
    target = {
        "type": "base-record",
        "table": extra.get("table", ""),
        "record_id": record_url,
    }
    data = {
        "kind": kind,
        "operation": kind,
        "created_at": now_iso(),
        "record_url": record_url,
        "target": target,
        "source": source,
        "summary": summary,
        "payload_title": extra.get("payload_title", ""),
    }
    digest = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    path = receipts / f"{now_iso().replace(':', '-')}-{kind}-{digest}.json"
    write_json(path, data)
    return path
```

- [ ] **Step 4: Add structured outbox data**

Replace `write_outbox()` with:

```python
def write_outbox(cwd: Path, kind: str, payload: dict[str, Any], error: str) -> Path:
    outbox = repo_runtime_dir(cwd, "outbox_dir")
    outbox.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    path = outbox / f"{now_iso().replace(':', '-')}-{kind}-{digest}.json"
    write_json(
        path,
        {
            "kind": kind,
            "operation": kind,
            "created_at": now_iso(),
            "error": error,
            "payload": payload,
            "retry_count": 0,
            "retry_hint": f"python3 \"$DEVHUB_HOME/bin/devhub.py\" sync-outbox --cwd \"$PWD\"",
        },
    )
    return path
```

- [ ] **Step 5: Verify record tests pass**

Run:

```bash
python3 -m unittest tests/test_records.py -v
```

Expected: tests pass.

- [ ] **Step 6: Update writeback docs**

In `skills/lark-cli-devhub/references/writeback-flows.md`, add a `Receipt Format` section:

```markdown
## Receipt Format

Every successful write must create `.devhub/receipts/*.json` with:

- `operation`
- `created_at`
- `target.type`
- `target.table`
- `target.record_id`
- `source.type`
- `summary`

Every failed write must create `.devhub/outbox/*.json` with:

- `operation`
- `created_at`
- `error`
- `payload`
- `retry_count`
- `retry_hint`

Do not claim success from a push, PR event, merge, or cron run unless a receipt exists.
```

- [ ] **Step 7: Commit**

```bash
git add scripts/devhub_lib/records.py tests/test_records.py skills/lark-cli-devhub/references/writeback-flows.md
git commit -m "feat: structure devhub receipts and outbox" # reviewed
```

## Task 5: Add Record Commands For V1.5 Tables

**Files:**
- Modify: `scripts/devhub_lib/cli.py`
- Modify: `skills/lark-cli-devhub/references/writeback-flows.md`
- Modify: `README.md`

- [ ] **Step 1: Add parser tests to `tests/test_records.py`**

Append this test class:

```python
from scripts.devhub_lib.cli import build_parser


class ParserRecordCommandTests(unittest.TestCase):
    def test_v15_record_commands_exist(self):
        parser = build_parser()
        for command in [
            "record-task",
            "record-bugfix",
            "record-ai-run",
            "record-release",
            "record-decision",
            "record-artifact",
            "record-project-fact",
        ]:
            args = parser.parse_args([command, "--payload", "/tmp/payload.json"])
            self.assertTrue(callable(args.func))
```

- [ ] **Step 2: Run failing parser test**

Run:

```bash
python3 -m unittest tests/test_records.py -v
```

Expected: parser rejects the new commands.

- [ ] **Step 3: Add commands to parser**

In `scripts/devhub_lib/cli.py`, replace the record command loop with:

```python
    record_tables = [
        ("record-task", "Tasks"),
        ("record-bugfix", "Bugfixes"),
        ("record-ai-run", "AI Runs"),
        ("record-release", "Releases"),
        ("record-decision", "Decisions"),
        ("record-artifact", "Artifacts"),
        ("record-project-fact", "Project Facts"),
    ]
    for name, table in record_tables:
        item = sub.add_parser(name)
        item.add_argument("--payload", required=True)
        item.set_defaults(func=lambda ns, n=name, t=table: record_command(n, t, Path(ns.payload), Path.cwd()))
```

- [ ] **Step 4: Verify parser tests pass**

Run:

```bash
python3 -m unittest tests/test_records.py -v
python3 scripts/devhub.py --help
```

Expected: tests pass and help lists the new commands.

- [ ] **Step 5: Document new commands**

In `README.md` under Daily Workflow, add command examples:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" record-task --payload /tmp/devhub-task.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-decision --payload /tmp/devhub-decision.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-artifact --payload /tmp/devhub-artifact.json
python3 "$DEVHUB_HOME/bin/devhub.py" record-project-fact --payload /tmp/devhub-project-fact.json
```

In `skills/lark-cli-devhub/references/writeback-flows.md`, add payload sections for Task, Decision, Artifact, and Project Fact using the field names from `templates/base-schema.json`.

- [ ] **Step 6: Commit**

```bash
git add scripts/devhub_lib/cli.py tests/test_records.py README.md skills/lark-cli-devhub/references/writeback-flows.md
git commit -m "feat: add v15 record commands" # reviewed
```

## Task 6: Add Workflow Skills

**Files:**
- Create: `skills/lark-cli-devhub-code-loop/SKILL.md`
- Create: `skills/lark-cli-devhub-report-loop/SKILL.md`
- Create: `skills/lark-cli-devhub-pr-writeback/SKILL.md`
- Create: `skills/lark-cli-devhub-whiteboard-loop/SKILL.md`
- Create: `skills/lark-cli-devhub/references/automation-patterns.md`
- Modify: `skills/lark-cli-devhub/SKILL.md`
- Modify: `skills/lark-cli-devhub/references/domain-map.md`
- Modify: `README.md`
- Modify: `docs/architecture.md`

- [ ] **Step 1: Create code-loop skill**

Create `skills/lark-cli-devhub-code-loop/SKILL.md`:

```markdown
---
name: lark-cli-devhub-code-loop
description: Use when an AI coding agent is fixing or investigating a bug and should search old Dev Hub records, write Bugfix and AI Run evidence, and leave receipt or outbox proof.
metadata:
  requires:
    bins: ["python3", "lark-cli", "git"]
---

# Lark CLI Dev Hub Code Loop

Use this workflow when work involves a bug, regression, incident, risky refactor, or repeated investigation path.

## Before Fixing

1. Extract project, area, symptom, error keywords, and relevant file paths.
2. Run `devhub.py search` with those terms.
3. Read Project Facts, Pitfalls, Playbooks, Bugfixes, AI Runs, Releases, Decisions, Tasks, Artifacts, and Areas when present.
4. Let old records guide the investigation only when they match current evidence.

## After Fixing

1. Write `record-bugfix` for the root cause, fix, verification, and regression risk.
2. Write `record-ai-run` for what the agent did and what evidence it checked.
3. Write `record-project-fact` if the work changes the current truth or retires an old path.
4. Write `record-artifact` for linked docs, diagrams, PRs, commits, or screenshots.
5. Mention receipt paths or outbox paths in the final work summary.

## Reliability

No receipt means no confirmed Feishu/Lark write. Failed writes must remain in `.devhub/outbox/`.
```

- [ ] **Step 2: Create report-loop skill**

Create `skills/lark-cli-devhub-report-loop/SKILL.md`:

```markdown
---
name: lark-cli-devhub-report-loop
description: Use when a user asks for daily, weekly, monthly, bugfix, release, or project reports from Dev Hub records in Feishu/Lark.
metadata:
  requires:
    bins: ["python3", "lark-cli"]
---

# Lark CLI Dev Hub Report Loop

Use this workflow to turn structured Dev Hub records into report drafts.

## Inputs

Collect Tasks, Bugfixes, AI Runs, Releases, Decisions, Project Facts, Artifacts, Pitfalls, Playbooks, and Areas.

## Draft Types

- Daily: completed work, blockers, risks, next actions.
- Weekly: bugfixes, releases, decisions, risks, progress, next week.
- Bugfix brief: symptom, root cause, fix, verification, risk, related records.
- Release brief: included fixes, verification, rollback note, known risk.
- Project brief: milestone progress, project health, decisions, blockers.

## Publishing Rule

Write Docs/Wiki drafts first. Publishing to IM, Mail, Slides, or stakeholder channels requires explicit approval.
```

- [ ] **Step 3: Create pr-writeback skill**

Create `skills/lark-cli-devhub-pr-writeback/SKILL.md`:

```markdown
---
name: lark-cli-devhub-pr-writeback
description: Use when GitHub PR or CI events should write AI Runs, Decisions, Bugfix candidates, Tasks, or Releases into Feishu/Lark through Dev Hub.
metadata:
  requires:
    bins: ["python3", "lark-cli", "git"]
---

# Lark CLI Dev Hub PR Writeback

Use this workflow for PR and CI event writeback.

## Event Map

- PR created or updated: write `AI Runs`.
- PR reviewed: write `Decisions` or `Bugfixes`.
- PR merged to the default branch: write `Releases`.
- CI failed: write a Bugfix candidate or `Tasks`.

## Reliability

A GitHub event is only a trigger. The workflow succeeds only when a receipt exists. On failure, keep the outbox item and report its path.

## Safe Default

Run in draft or shadow mode until the project confirms the mapping is useful.
```

- [ ] **Step 4: Create whiteboard-loop skill**

Create `skills/lark-cli-devhub-whiteboard-loop/SKILL.md`:

```markdown
---
name: lark-cli-devhub-whiteboard-loop
description: Use when architecture changes, complex bug investigations, or workflow maps should produce Feishu/Lark Whiteboard or Doc diagram drafts linked back to Dev Hub artifacts.
metadata:
  requires:
    bins: ["python3", "lark-cli"]
---

# Lark CLI Dev Hub Whiteboard Loop

Use this workflow for architecture maps, dependency maps, complex bug maps, release maps, and knowledge graphs.

## Safe Path

1. Generate a draft.
2. Run dry-run when the Whiteboard tool supports it.
3. Ask for approval before writing the board.
4. Link the board or fallback Doc diagram through an `Artifacts` record.

## Fallback

If Whiteboard rendering is unavailable, create a Markdown or Docs diagram draft and register it as an Artifact.
```

- [ ] **Step 5: Add automation reference**

Create `skills/lark-cli-devhub/references/automation-patterns.md`:

```markdown
# Automation Patterns

## Manual Command

Manual command is the reliable baseline. It must work even when hooks, GitHub Actions, cron, and Whiteboard tooling are not configured.

## Local Git Hook

Use local hooks to remind users about knowledge writeback. Hooks may warn or block depending on mode, but they must accept receipts, outbox items, or `# kb-skip: reason`.

## GitHub Action

Use GitHub Actions to map PR and CI events to Dev Hub record writes. A completed workflow run is not write success; receipt or outbox evidence is required.

## Cron

Use cron or scheduled workflows to generate report drafts. Publish drafts only after explicit approval.

## Whiteboard Workflow

Use draft and dry-run first. Final boards must be linked through Artifacts records.
```

- [ ] **Step 6: Update root skill routing**

In `skills/lark-cli-devhub/SKILL.md`, add workflow routing bullets:

```markdown
## Workflow Routing

- Use `lark-cli-devhub-code-loop` for bug investigation and fix evidence.
- Use `lark-cli-devhub-report-loop` for daily, weekly, bugfix, release, and project reports.
- Use `lark-cli-devhub-pr-writeback` for PR and CI event writeback.
- Use `lark-cli-devhub-whiteboard-loop` for architecture, workflow, and bug investigation diagrams.
```

- [ ] **Step 7: Update README and architecture lists**

Add the four workflow skills to `README.md`, `docs/architecture.md`, and `skills/lark-cli-devhub/references/domain-map.md`.

- [ ] **Step 8: Validate skills**

Run:

```bash
python3 scripts/validate.py
```

Expected: `ok`.

- [ ] **Step 9: Commit**

```bash
git add skills/lark-cli-devhub-code-loop skills/lark-cli-devhub-report-loop skills/lark-cli-devhub-pr-writeback skills/lark-cli-devhub-whiteboard-loop skills/lark-cli-devhub/SKILL.md skills/lark-cli-devhub/references/automation-patterns.md skills/lark-cli-devhub/references/domain-map.md README.md docs/architecture.md
git commit -m "feat: add devhub workflow skills" # reviewed
```

## Task 7: Add Report Draft Command And Templates

**Files:**
- Create: `scripts/devhub_lib/reports.py`
- Create: `tests/test_report_draft.py`
- Create: `templates/report-daily.md`
- Create: `templates/report-weekly.md`
- Create: `templates/report-release.md`
- Modify: `scripts/devhub_lib/cli.py`
- Modify: `scripts/devhub_lib/commands.py`
- Modify: `skills/lark-cli-devhub/references/report-loop.md`

- [ ] **Step 1: Write report draft tests**

Create `tests/test_report_draft.py`:

```python
import unittest
from scripts.devhub_lib.reports import draft_report


class ReportDraftTests(unittest.TestCase):
    def test_weekly_report_contains_core_sections(self):
        records = {
            "Tasks": [{"Title": "Fix voice stream", "Status": "Done", "AI Summary": "Closed stream bug"}],
            "Bugfixes": [{"Title": "Voice command ack fixed", "AI Summary": "Ack path corrected"}],
            "AI Runs": [{"Title": "Codex run", "Verification Result": "python3 -m unittest passed"}],
            "Releases": [{"Title": "Release 2026-05-20", "Summary": "Voice fix"}],
            "Decisions": [{"Title": "Use command stream", "Decision": "Keep command ack path"}],
        }

        text = draft_report("weekly", "music-agent", records)

        self.assertIn("# Weekly Report: music-agent", text)
        self.assertIn("## Completed Work", text)
        self.assertIn("Fix voice stream", text)
        self.assertIn("Voice command ack fixed", text)
        self.assertIn("Use command stream", text)

    def test_release_report_contains_release_sections(self):
        records = {"Releases": [{"Title": "Release 2026-05-20", "Rollback Notes": "Revert commit abc"}]}

        text = draft_report("release", "music-agent", records)

        self.assertIn("# Release Brief: music-agent", text)
        self.assertIn("## Rollback Notes", text)
        self.assertIn("Revert commit abc", text)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run failing report tests**

Run:

```bash
python3 -m unittest tests/test_report_draft.py -v
```

Expected: import fails because `reports.py` does not exist.

- [ ] **Step 3: Implement report drafting**

Create `scripts/devhub_lib/reports.py`:

```python
from __future__ import annotations

from typing import Any


def _titles(records: list[dict[str, Any]], fallback_key: str = "AI Summary") -> list[str]:
    values: list[str] = []
    for record in records:
        title = record.get("Title") or record.get(fallback_key) or ""
        if title:
            values.append(str(title))
    return values


def _bullets(values: list[str]) -> str:
    if not values:
        return "- No records found."
    return "\n".join(f"- {value}" for value in values)


def draft_report(kind: str, project: str, records: dict[str, list[dict[str, Any]]]) -> str:
    if kind == "daily":
        return "\n".join(
            [
                f"# Daily Report: {project}",
                "",
                "## Completed Work",
                _bullets(_titles(records.get("Tasks", [])) + _titles(records.get("Bugfixes", []))),
                "",
                "## Blockers",
                _bullets([str(item.get("Blocker")) for item in records.get("Tasks", []) if item.get("Blocker")]),
                "",
                "## Next Actions",
                _bullets([str(item.get("Next Action")) for item in records.get("Tasks", []) if item.get("Next Action")]),
                "",
            ]
        )
    if kind == "weekly":
        return "\n".join(
            [
                f"# Weekly Report: {project}",
                "",
                "## Completed Work",
                _bullets(_titles(records.get("Tasks", [])) + _titles(records.get("Bugfixes", []))),
                "",
                "## AI Evidence",
                _bullets(_titles(records.get("AI Runs", []), "Verification Result")),
                "",
                "## Releases",
                _bullets(_titles(records.get("Releases", []), "Summary")),
                "",
                "## Decisions",
                _bullets(_titles(records.get("Decisions", []), "Decision")),
                "",
                "## Risks And Next Week",
                "- Review open blockers, failed CI records, and stale Project Facts.",
                "",
            ]
        )
    if kind == "release":
        rollback = [str(item.get("Rollback Notes")) for item in records.get("Releases", []) if item.get("Rollback Notes")]
        return "\n".join(
            [
                f"# Release Brief: {project}",
                "",
                "## Included Releases",
                _bullets(_titles(records.get("Releases", []), "Summary")),
                "",
                "## Related Bugfixes",
                _bullets(_titles(records.get("Bugfixes", []))),
                "",
                "## Verification",
                _bullets([str(item.get("Verification Result")) for item in records.get("Releases", []) if item.get("Verification Result")]),
                "",
                "## Rollback Notes",
                _bullets(rollback),
                "",
            ]
        )
    raise ValueError(f"unsupported report kind: {kind}")
```

- [ ] **Step 4: Add CLI command**

In `scripts/devhub_lib/cli.py`, import `command_report_draft`:

```python
from .commands import command_preflight, command_provision, command_report_draft, command_search
```

Add parser command:

```python
    report = sub.add_parser("report-draft")
    report.add_argument("--kind", choices=["daily", "weekly", "release"], required=True)
    report.add_argument("--project", required=True)
    report.add_argument("--records", required=True)
    report.set_defaults(func=command_report_draft)
```

In `scripts/devhub_lib/commands.py`, add:

```python
from .reports import draft_report
```

Add command:

```python
def command_report_draft(args: Any) -> int:
    records = load_json(Path(args.records))
    print(draft_report(args.kind, args.project, records))
    return 0
```

Ensure `Path` is imported in `commands.py`:

```python
from pathlib import Path
```

- [ ] **Step 5: Add report templates**

Create `templates/report-daily.md`, `templates/report-weekly.md`, and `templates/report-release.md` with the same section headings emitted by `draft_report()`. Keep the templates short and use bracketed labels such as `[project]`, `[date]`, and `[records summary]`.

- [ ] **Step 6: Add report-loop reference**

Create `skills/lark-cli-devhub/references/report-loop.md`:

```markdown
# Report Loop

Report Loop turns structured Dev Hub records into drafts. It does not publish to IM, Mail, Slides, or stakeholder channels without explicit approval.

## Commands

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" report-draft \
  --kind weekly \
  --project "$(basename "$PWD")" \
  --records /tmp/devhub-report-records.json
```

## Draft Types

- `daily`
- `weekly`
- `release`

## Source Records

Prefer Tasks, Bugfixes, AI Runs, Releases, Decisions, Project Facts, and Artifacts.
```

- [ ] **Step 7: Verify report tests and CLI**

Run:

```bash
python3 -m unittest tests/test_report_draft.py -v
python3 scripts/devhub.py report-draft --kind weekly --project example --records templates/seed.example.json >/tmp/devhub-weekly.md
```

Expected: tests pass and `/tmp/devhub-weekly.md` contains `# Weekly Report: example`.

- [ ] **Step 8: Commit**

```bash
git add scripts/devhub_lib/reports.py scripts/devhub_lib/cli.py scripts/devhub_lib/commands.py tests/test_report_draft.py templates/report-daily.md templates/report-weekly.md templates/report-release.md skills/lark-cli-devhub/references/report-loop.md
git commit -m "feat: add devhub report drafts" # reviewed
```

## Task 8: Add GitHub Action And Cron Templates

**Files:**
- Create: `templates/github-pr-writeback.yml`
- Create: `templates/cron-report.yml`
- Modify: `skills/lark-cli-devhub/references/automation-patterns.md`
- Modify: `docs/marketplaces.md`

- [ ] **Step 1: Add GitHub PR writeback template**

Create `templates/github-pr-writeback.yml`:

```yaml
name: Dev Hub PR Writeback

on:
  pull_request:
    types: [opened, synchronize, reopened, closed]
  pull_request_review:
    types: [submitted]
  workflow_run:
    types: [completed]

jobs:
  writeback:
    runs-on: ubuntu-latest
    if: ${{ github.event_name != 'pull_request' || github.event.pull_request.head.repo.full_name == github.repository }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install Dev Hub helper
        run: |
          python3 scripts/devhub.py --help
      - name: Build AI Run payload for PR update
        if: ${{ github.event_name == 'pull_request' && github.event.action != 'closed' }}
        run: |
          mkdir -p .devhub/outbox
          cat > .devhub/outbox/pr-ai-run-${{ github.event.pull_request.number }}.json <<'JSON'
          {
            "operation": "record-ai-run",
            "source": "github-action",
            "event": "pull_request",
            "pr": "${{ github.event.pull_request.html_url }}",
            "note": "Configure lark-cli credentials before enabling real Feishu/Lark writes."
          }
          JSON
      - name: Build Release payload for merged PR
        if: ${{ github.event_name == 'pull_request' && github.event.pull_request.merged == true }}
        run: |
          mkdir -p .devhub/outbox
          cat > .devhub/outbox/pr-release-${{ github.event.pull_request.number }}.json <<'JSON'
          {
            "operation": "record-release",
            "source": "github-action",
            "event": "pull_request_merged",
            "pr": "${{ github.event.pull_request.html_url }}",
            "merge_commit_sha": "${{ github.event.pull_request.merge_commit_sha }}",
            "note": "Configure lark-cli credentials before enabling real Feishu/Lark writes."
          }
          JSON
      - name: Upload Dev Hub outbox
        uses: actions/upload-artifact@v4
        with:
          name: devhub-outbox
          path: .devhub/outbox/*.json
          if-no-files-found: ignore
```

This template creates outbox evidence by default. A later implementation can replace the outbox creation step with real `devhub.py record-*` calls after credentials and scopes are configured.

- [ ] **Step 2: Add cron report template**

Create `templates/cron-report.yml`:

```yaml
name: Dev Hub Scheduled Report Draft

on:
  schedule:
    - cron: "0 1 * * 1"
  workflow_dispatch:

jobs:
  report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Create report records input
        run: |
          cat > /tmp/devhub-report-records.json <<'JSON'
          {
            "Tasks": [],
            "Bugfixes": [],
            "AI Runs": [],
            "Releases": [],
            "Decisions": [],
            "Project Facts": [],
            "Artifacts": []
          }
          JSON
      - name: Generate weekly report draft
        run: |
          python3 scripts/devhub.py report-draft \
            --kind weekly \
            --project "${{ github.repository }}" \
            --records /tmp/devhub-report-records.json > devhub-weekly-report.md
      - uses: actions/upload-artifact@v4
        with:
          name: devhub-weekly-report
          path: devhub-weekly-report.md
```

- [ ] **Step 3: Document templates**

In `skills/lark-cli-devhub/references/automation-patterns.md`, add:

```markdown
## Templates

- `templates/github-pr-writeback.yml` starts in outbox mode and maps PR/CI triggers to Dev Hub operations.
- `templates/cron-report.yml` generates a weekly report draft artifact without publishing it.
```

In `docs/marketplaces.md`, mention that templates are examples and do not include credentials.

- [ ] **Step 4: Verify YAML files are readable**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
for path in [Path("templates/github-pr-writeback.yml"), Path("templates/cron-report.yml")]:
    text = path.read_text(encoding="utf-8")
    assert "name:" in text
    assert "on:" in text
    assert "jobs:" in text
print("ok")
PY
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add templates/github-pr-writeback.yml templates/cron-report.yml skills/lark-cli-devhub/references/automation-patterns.md docs/marketplaces.md
git commit -m "docs: add devhub automation templates" # reviewed
```

## Task 9: Add Whiteboard Draft Support

**Files:**
- Create: `scripts/devhub_lib/whiteboard.py`
- Create: `templates/whiteboard-draft.md`
- Modify: `scripts/devhub_lib/cli.py`
- Modify: `scripts/devhub_lib/commands.py`
- Modify: `skills/lark-cli-devhub/references/whiteboard-loop.md`

- [ ] **Step 1: Add whiteboard draft tests**

Append to `tests/test_report_draft.py`:

```python
from scripts.devhub_lib.whiteboard import draft_whiteboard


class WhiteboardDraftTests(unittest.TestCase):
    def test_architecture_draft_contains_artifact_instruction(self):
        text = draft_whiteboard(
            "architecture",
            "music-agent",
            "voice command stream replaces retired audio ack path",
        )
        self.assertIn("# Whiteboard Draft: music-agent", text)
        self.assertIn("## Diagram Nodes", text)
        self.assertIn("voice command stream", text)
        self.assertIn("Create an Artifacts record", text)
```

- [ ] **Step 2: Run failing whiteboard test**

Run:

```bash
python3 -m unittest tests/test_report_draft.py -v
```

Expected: import fails because `whiteboard.py` does not exist.

- [ ] **Step 3: Implement whiteboard draft helper**

Create `scripts/devhub_lib/whiteboard.py`:

```python
from __future__ import annotations


def draft_whiteboard(kind: str, project: str, summary: str) -> str:
    return "\n".join(
        [
            f"# Whiteboard Draft: {project}",
            "",
            f"Kind: {kind}",
            "",
            "## Purpose",
            summary,
            "",
            "## Diagram Nodes",
            "- Current system",
            "- Changed component",
            "- Related Project Facts",
            "- Related Decisions",
            "- Related Artifacts",
            "",
            "## Links To Add After Approval",
            "- Create an Artifacts record for the final board or fallback Doc diagram.",
            "- Link related Bugfixes, AI Runs, Decisions, and Project Facts.",
            "",
            "## Safety",
            "- Draft first.",
            "- Run dry-run when the Whiteboard tool supports it.",
            "- Write final board only after explicit approval.",
            "",
        ]
    )
```

- [ ] **Step 4: Add CLI command**

In `scripts/devhub_lib/cli.py`, add:

```python
    board = sub.add_parser("whiteboard-draft")
    board.add_argument("--kind", required=True)
    board.add_argument("--project", required=True)
    board.add_argument("--summary", required=True)
    board.set_defaults(func=command_whiteboard_draft)
```

Import `command_whiteboard_draft` from `commands.py`.

In `scripts/devhub_lib/commands.py`, add:

```python
from .whiteboard import draft_whiteboard
```

Add:

```python
def command_whiteboard_draft(args: Any) -> int:
    print(draft_whiteboard(args.kind, args.project, args.summary))
    return 0
```

- [ ] **Step 5: Add template and reference**

Create `templates/whiteboard-draft.md`:

```markdown
# Whiteboard Draft: [project]

## Purpose

[summary]

## Diagram Nodes

- Current system
- Changed component
- Related Project Facts
- Related Decisions
- Related Artifacts

## Links To Add After Approval

- Create an Artifacts record for the final board or fallback Doc diagram.
- Link related Bugfixes, AI Runs, Decisions, and Project Facts.

## Safety

- Draft first.
- Run dry-run when the Whiteboard tool supports it.
- Write final board only after explicit approval.
```

Create `skills/lark-cli-devhub/references/whiteboard-loop.md`:

```markdown
# Whiteboard Loop

Whiteboard Loop creates architecture, workflow, dependency, and bug investigation drafts. Whiteboard is visual context; Base Artifacts are the durable AI-readable link.

## Command

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" whiteboard-draft \
  --kind architecture \
  --project "$(basename "$PWD")" \
  --summary "what changed and why"
```

## Safety

Generate a draft first, run dry-run when available, ask for approval, then write the final board and create an Artifacts record.
```

- [ ] **Step 6: Verify whiteboard tests and command**

Run:

```bash
python3 -m unittest tests/test_report_draft.py -v
python3 scripts/devhub.py whiteboard-draft --kind architecture --project example --summary "command stream map" >/tmp/devhub-board.md
```

Expected: tests pass and `/tmp/devhub-board.md` contains `# Whiteboard Draft: example`.

- [ ] **Step 7: Commit**

```bash
git add scripts/devhub_lib/whiteboard.py scripts/devhub_lib/cli.py scripts/devhub_lib/commands.py tests/test_report_draft.py templates/whiteboard-draft.md skills/lark-cli-devhub/references/whiteboard-loop.md
git commit -m "feat: add whiteboard draft workflow" # reviewed
```

## Task 10: Final Documentation, Install Script Output, And Validation

**Files:**
- Modify: `scripts/install-devhub.sh`
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/lark-cli-capability-map.md`
- Modify: `docs/marketplaces.md`

- [ ] **Step 1: Update install script output**

In `scripts/install-devhub.sh`, extend the `Skills:` list in the final message:

```bash
  $SKILLS_HOME/lark-cli-devhub-code-loop
  $SKILLS_HOME/lark-cli-devhub-report-loop
  $SKILLS_HOME/lark-cli-devhub-pr-writeback
  $SKILLS_HOME/lark-cli-devhub-whiteboard-loop
```

Extend the `Next:` block:

```bash
  python3 "$DEVHUB_HOME/bin/devhub.py" search --project "$(basename "$PWD")" --query "area symptom"
  python3 "$DEVHUB_HOME/bin/devhub.py" report-draft --kind weekly --project "$(basename "$PWD")" --records "$DEVHUB_HOME/templates/seed.example.json"
```

- [ ] **Step 2: Update README**

Ensure README contains:

- the four workflow skills in the skill table;
- dependency checklist for Python, git, `lark-cli`, Node/npx, GitHub Actions, cron, and Whiteboard CLI;
- search scope note naming Tasks, Bugfixes, AI Runs, Releases, Decisions, Project Facts, Artifacts, Pitfalls, Playbooks, and Areas;
- automation roadmap with manual command, local hook, PR writeback, cron reports, and Whiteboard workflow.

- [ ] **Step 3: Update docs**

In `docs/architecture.md`, add workflow skills to repository shape and explain the workflow/domain boundary.

In `docs/lark-cli-capability-map.md`, add a V1.5 section that maps:

```text
Base -> records, search, dashboards
Docs/Wiki -> report drafts and long-form context
Whiteboard -> drafts and architecture maps
GitHub Actions -> PR/CI triggers
cron -> scheduled report drafts
```

In `docs/marketplaces.md`, add the four workflow skills to publication notes and discovery keywords:

```text
lark-cli-devhub-code-loop
lark-cli-devhub-report-loop
lark-cli-devhub-pr-writeback
lark-cli-devhub-whiteboard-loop
```

- [ ] **Step 4: Run all local tests**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/devhub.py --help
git diff --check
```

Expected:

```text
unittest: OK
validate: ok
devhub help: lists all commands
git diff --check: no output
```

- [ ] **Step 5: Verify skill discovery locally**

Run:

```bash
npx skills add . --list --full-depth
```

Expected: output includes all existing domain skills plus:

```text
lark-cli-devhub-code-loop
lark-cli-devhub-report-loop
lark-cli-devhub-pr-writeback
lark-cli-devhub-whiteboard-loop
```

- [ ] **Step 6: Commit**

```bash
git add scripts/install-devhub.sh README.md docs/architecture.md docs/lark-cli-capability-map.md docs/marketplaces.md
git commit -m "docs: finish devhub v15 rollout docs" # reviewed
```

## Task 11: Final Review And Release Preparation

**Files:**
- Review: entire repository

- [ ] **Step 1: Inspect final diff**

Run:

```bash
git status --short --branch
git log --oneline -8
```

Expected: branch contains the V1.5 implementation commits and only local visual companion files remain untracked if the brainstorming server is still present.

- [ ] **Step 2: Run final validation**

Run:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
npx skills add . --list --full-depth
```

Expected: tests and validation pass, and skill discovery lists the workflow skills.

- [ ] **Step 3: Prepare release summary**

Write a release summary in the final implementation report with:

```text
Implemented:
- Search coverage metadata
- Project Facts schema
- Structured receipts/outbox
- V1.5 record commands
- Workflow skills
- Report draft command
- GitHub/cron templates
- Whiteboard draft command

Verified:
- python3 -m unittest discover -s tests -v
- python3 scripts/validate.py
- python3 scripts/devhub.py --help
- npx skills add . --list --full-depth

Not included:
- Unattended IM publishing
- Whiteboard write without approval
- Organization-wide approvals/OKR automation
```

- [ ] **Step 4: Ask before push**

Because this repository has protected main behavior and the current branch may already be ahead of origin, ask the user before pushing. If the user explicitly approves a cloud main push, run:

```bash
git push origin main # user-approved
```

Expected: remote `main` receives the V1.5 commits.
