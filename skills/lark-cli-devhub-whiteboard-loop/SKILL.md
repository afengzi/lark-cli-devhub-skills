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

## Required Map Updates

When architecture, module ownership, task execution flow, PR/writeback flow, or a reusable bug investigation path changes, update the matching project map under `10 Projects/<project>/50 Maps`. If the change is reusable across projects, also update the global map under `00 Global/50 Maps`.

Do not leave the map update as an invisible assumption. Either write the board and Artifact, or leave an outbox/explicit note describing why it was skipped.

## Fallback

If Whiteboard rendering is unavailable, create a Markdown or Docs diagram draft and register it as an Artifact.
