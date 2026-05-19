# Search Policy

Search before fixing bugs so agents do not repeat old investigation.

## Query Shape

Use a compact query with:

- product area
- visible symptom
- error keywords
- relevant file or component names
- failed command or endpoint

Good:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" search \
  --project music-agent \
  --query "voice audio ack continuation no speech frontend scheduler"
```

Weak:

```bash
python3 "$DEVHUB_HOME/bin/devhub.py" search --project music-agent --query "bug"
```

## How To Read Results

Read in this order:

1. `Project Facts`: current truths and retired paths.
2. `Pitfalls`: traps and forbidden approaches.
3. `Playbooks`: diagnosis order and evidence requirements.
4. `Bugfixes`: old root causes and verification.
5. `AI Runs`: previous agent actions, evidence, and caveats.
6. `Releases`: what reached the default branch and when.
7. `Decisions`: constraints that explain why the system is shaped this way.
8. `Tasks`: current work state and blockers.
9. `Artifacts`: linked docs, whiteboards, PRs, commits, and files.
10. `Areas`: code paths and risk level.

## When Search Is Optional

Skip search for tiny mechanical edits that cannot plausibly repeat a past bug, such as typo fixes or formatting-only changes. Still write an AI Run or Release when the work reaches a commit or main push gate.
