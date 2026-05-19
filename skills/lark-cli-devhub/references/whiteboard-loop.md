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
