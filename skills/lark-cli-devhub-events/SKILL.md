---
name: lark-cli-devhub-events
description: Use when using Feishu/Lark events through lark-cli or feishu-cli for automation triggers, watchers, notifications, inbox capture, task updates, mail events, meeting events, and Dev Hub writeback loops.
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark CLI Dev Hub Events

Events are the automation layer. Use them when Dev Hub should react to Feishu changes instead of only manual agent commands.

Discovery aliases: `feishu-cli event`, `飞书事件`, `lark-cli event`, `event consume`, `automation`, `watcher`.

## Office Use Cases

- Watch for incoming mail or message events and capture relevant items into a Dev Hub inbox.
- Trigger task updates when Feishu task events arrive.
- React to approval or release workflow events and write evidence to Base.
- Build lightweight notification loops for stale Decisions, blocked Tasks, or failed writebacks.
- Explore event schemas before implementing a long-running automation.

## Routing Rules

- Use Events for triggers. Use domain skills for the actual action: Task, Base, Mail, IM, Calendar, or Docs.
- Do not run long-lived event consumers in a foreground agent session unless the user explicitly asked.
- Store event-derived records with source event type, timestamp, source URL or ID, and a clear summary.

## Useful Commands

```bash
lark-cli event list
lark-cli event schema "$EVENT_KEY"
lark-cli event status
lark-cli event consume "$EVENT_KEY"
lark-cli event stop
```

## Dev Hub Suggestions

- Start with an inbox workflow: event -> short summary -> Base `Tasks` or `Artifacts` -> human review.
- Keep event automations narrow and auditable before making them write to canonical tables.
- Use outbox records for failed event writebacks so automation failures are visible.
