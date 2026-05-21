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

## Provisioned Starter Maps

The helper provision flow writes the first usable map set:

- Global Maps: `Global: Dev Hub 总览图`, `Global: Bug 排查路径图`, `Global: PR 写回流程图`, `Global: 任务执行闭环图`.
- Project Maps: `<project>: 架构图`, `<project>: Bug 排查路径图`, `<project>: PR 写回流程图`, `<project>: 任务执行闭环图`.

Local SVG templates live under `templates/whiteboards/` or `$DEVHUB_HOME/templates/whiteboards/` for reusable redraw guidance. Project-specific redraw sources should live in the project repo, preferably `docs/devhub/whiteboards/<project>-<map>.svg`, so the map source is reviewable with the code change. They should not appear as template pages in Feishu Wiki.

Treat these as living maps. Architecture or workflow changes should update the board and the matching Base `Artifacts` summary together.

Existing maps are preserved during normal provision runs. Use `DEVHUB_WHITEBOARD_OVERWRITE=1` only when you intentionally want to redraw starter maps from templates. SVG conversion is cached under `$DEVHUB_HOME/cache/whiteboards/`.

When updating an existing project map, resolve the current page under `10 Projects/<project>/50 Maps` first. Do not write to pages under `90 Archive`, deleted docs, or duplicate legacy Artifact links. If the active Artifact points to a stale URL, repoint that Artifact after the new page is created.
