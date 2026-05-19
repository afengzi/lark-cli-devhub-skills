---
name: lark-cli-devhub-meetings
description: Use when using Feishu/Lark VC or Minutes through lark-cli or feishu-cli for meeting records, notes, recordings, transcripts, action items, decisions, retrospectives, and follow-up writeback.
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark CLI Dev Hub Meetings

Meetings turn spoken context into durable records. Use this skill for VC records, meeting notes, minutes search, recordings, summaries, decisions, and action items.

Discovery aliases: `feishu-cli minutes`, `feishu-cli vc`, `飞书妙记`, `飞书会议`, `lark-cli minutes`, `lark-cli vc`, `meeting summary`.

## Office Use Cases

- Search meeting records or minutes for project decisions and bug context.
- Pull meeting notes after a design review, retro, bug bash, or release review.
- Convert action items into Feishu Tasks and Dev Hub `Tasks`.
- Convert architectural agreement into a Dev Hub `Decision`.
- Convert incident review conclusions into `Bugfixes`, `Pitfalls`, or `Playbooks`.

## Routing Rules

- Use Calendar skill for scheduling. Use Meetings skill after there is a meeting, meeting ID, calendar event ID, minute token, or recording.
- Meeting summaries should not replace structured writeback. Link the meeting artifact from Base.
- Be careful with privacy: summarize only what is relevant to the project task.

## Useful Commands

```bash
lark-cli vc +search --json @meeting-search.json --as user --format json
lark-cli vc +notes --calendar-event-ids "$EVENT_ID" --as user --format json
lark-cli vc +recording --meeting-ids "$MEETING_ID" --as user --format json
lark-cli minutes +search --query "release review" --as user --format json
lark-cli minutes +download --minute-token "$MINUTE_TOKEN" --output ./minutes --as user
```

## Dev Hub Suggestions

- After important meetings, write one `AI Run` record summarizing what was extracted.
- Create `Decision` records for durable choices; create `Tasks` for action items.
- Link the minute URL as an `Artifact` with a short AI-readable summary.
