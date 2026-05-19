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
- Templates: `Template: Bug 排查路径图`, `Template: PR 写回流程图`, `Template: 任务执行闭环图`.

Treat these as living maps. Architecture or workflow changes should update the board and the matching Base `Artifacts` summary together.

Existing maps are preserved during normal provision runs. Use `DEVHUB_WHITEBOARD_OVERWRITE=1` only when you intentionally want to redraw starter maps from templates. SVG conversion is cached under `$DEVHUB_HOME/cache/whiteboards/`.
