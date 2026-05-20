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

Use the helper when the draft should actually land in Wiki:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" report-draft \
  --kind weekly \
  --project "$(basename "$PWD")" \
  --records /tmp/devhub-report-records.json \
  --wiki
```

Without `--wiki`, `report-draft` only prints Markdown for review.
With `--wiki`, each report appends a timestamped section to the stable page under `10 Projects/<project>/60 Reports`, such as `Report: <project> weekly`; it does not overwrite the previous report draft or create a duplicate report page.
