# Report Loop

Report Loop turns structured Dev Hub records into drafts. It does not publish to IM, Mail, Slides, or stakeholder channels without explicit approval.

## Commands

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" report-draft \
  --kind weekly \
  --project "$(basename "$PWD")" \
  --records /tmp/devhub-report-records.json
```

## Draft Types

- `daily`
- `weekly`
- `release`

## Source Records

Prefer Tasks, Bugfixes, AI Runs, Releases, Decisions, Project Facts, and Artifacts.
