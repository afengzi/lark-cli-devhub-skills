# Agent Notes

This repository publishes Agent Skills for Lark CLI Dev Hub.

## Editing Rules

- Keep each `SKILL.md` focused and short.
- Move detailed domain guidance into `references/`.
- Do not commit real Feishu Base tokens, Wiki node tokens, app secrets, access tokens, or private keys.
- Run `python3 scripts/validate.py` before committing.
- Keep helper scripts portable. Do not hardcode personal paths.

## Release Checklist

1. Run validation.
2. Confirm `npx skills add <owner/repo> --list` can discover skills after push.
3. Publish individual skill folders to ClawHub only after `clawhub whoami` succeeds.
