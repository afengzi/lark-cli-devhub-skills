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
