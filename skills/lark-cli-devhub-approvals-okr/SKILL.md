---
name: lark-cli-devhub-approvals-okr
description: Use when connecting Feishu/Lark Approval or OKR data through lark-cli or feishu-cli to development planning, release governance, project health, goals, review tasks, and Dev Hub evidence.
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark CLI Dev Hub Approvals And OKR

Approvals and OKRs connect work to governance and goals. Use this skill when development work needs formal approval, progress reporting, or goal alignment.

Discovery aliases: `feishu-cli approval`, `feishu-cli okr`, `飞书审批`, `飞书 OKR`, `lark-cli approval`, `lark-cli okr`, `release approval`.

## Office Use Cases

- Link release approvals or change requests to Dev Hub `Releases`.
- Track OKR progress with evidence from Dev Hub `Projects`, `Tasks`, `Bugfixes`, and `Releases`.
- Convert quarterly goals into project areas and measurable follow-up tasks.
- Add progress updates with links to artifacts, dashboards, or shipped releases.
- Audit whether a high-risk release had the required approval evidence.

## Routing Rules

- Use Approval when the process is formal and externally governed.
- Use Tasks when the work is internal execution.
- Use OKR when the question is goal progress, impact, or quarterly status.
- Do not create approval or OKR changes without clear user authorization.

## Useful Commands

```bash
lark-cli approval instances list --params '{}' --as user --format json
lark-cli approval tasks list --params '{}' --as user --format json
lark-cli okr +cycle-list --as user --format json
lark-cli okr +cycle-detail --cycle-id "$CYCLE_ID" --as user --format json
lark-cli okr +progress-create --json @progress.json --as user
```

## Dev Hub Suggestions

- Add `Approval URL` or approval IDs to `Releases` when releases require sign-off.
- Use Base dashboards to show goal progress backed by actual Bugfix/Release records.
- Write `Decision` records when approval constraints change engineering choices.
