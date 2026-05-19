---
name: lark-cli-devhub-communications
description: Use when using Feishu/Lark IM or Mail through lark-cli or feishu-cli for project communication, chat search, message summaries, announcements, email triage, drafts, replies, and sharing Dev Hub artifacts.
metadata:
  requires:
    bins: ["lark-cli"]
---

# Lark CLI Dev Hub Communications

Communications cover IM and Mail. Use this skill when project knowledge is in chats, threads, bookmarks, email conversations, or announcements.

Discovery aliases: `feishu-cli im`, `feishu-cli mail`, `飞书消息`, `飞书邮件`, `lark-cli im`, `lark-cli mail`, `chat summary`, `email triage`.

## Office Use Cases

- Search chat history for bug reports, decisions, acceptance criteria, or incident context.
- Turn important chat threads into Dev Hub Bugfixes, Decisions, Tasks, or Artifacts.
- Send release announcements or status summaries to a group after a verified push.
- Triage email, create draft replies, and link important threads to project records.
- Share Dev Hub Docs, Sheets, or Base records to a chat when a team needs context.

## Routing Rules

- Ask before sending messages or emails. Draft first when tone, recipients, or content are uncertain.
- Use IM for team visibility; use Mail for formal external or longer-form communication.
- Do not treat chat as the durable source of truth. Summarize important outcomes into Base or Docs.
- When reading messages, preserve sender/time/channel as evidence when relevant.

## Useful Commands

```bash
lark-cli im +chat-search --query "project name" --as user --format json
lark-cli im +messages-search --query "error keyword" --as user --format json
lark-cli im +messages-send --chat-id "$CHAT_ID" --text "Release verified" --as user
lark-cli mail +triage --query "project OR incident" --as user --format json
lark-cli mail +reply --message-id "$MESSAGE_ID" --body-file ./reply.md --as user
```

## Dev Hub Suggestions

- Store only summaries and links, not noisy full chat dumps.
- Convert repeated user complaints into `Pitfalls` or `Playbooks`.
- Convert agreement in a thread into a `Decision` record with context and consequences.
