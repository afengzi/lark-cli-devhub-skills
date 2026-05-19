# Marketplaces And Distribution

## GitHub

Primary distribution is GitHub because `npx skills` can install from `owner/repo`:

```bash
npx skills add afengzi/lark-cli-devhub-skills --all
```

List available skills without installing:

```bash
npx skills add afengzi/lark-cli-devhub-skills --list
```

## skills.sh

`skills.sh` indexes public Agent Skills repositories that can be installed with `npx skills`. Once the GitHub repository is public and installable, it can be discovered through the Skills directory ecosystem.

## ClawHub

ClawHub publishes one skill folder at a time. These slugs are published:

```bash
npx -y clawhub@0.16.0 search lark-cli-devhub
npx -y clawhub@0.16.0 install lark-cli-devhub
npx -y clawhub@0.16.0 install lark-cli-devhub-base
npx -y clawhub@0.16.0 install lark-cli-devhub-docs-wiki
npx -y clawhub@0.16.0 install lark-cli-devhub-taskflow
npx -y clawhub@0.16.0 install lark-cli-devhub-whiteboard
```

Republish each folder under `skills/` after changes:

```bash
npx -y clawhub@0.16.0 login

npx -y clawhub@0.16.0 publish skills/lark-cli-devhub \
  --slug lark-cli-devhub \
  --name "Lark CLI Dev Hub" \
  --version 0.1.0 \
  --tags feishu,lark,devtools,knowledge-base,codex,claude-code \
  --clawscan-note "Uses local Python and lark-cli. Network access is delegated to the user's configured lark-cli credentials; no credentials are bundled."

npx -y clawhub@0.16.0 publish skills/lark-cli-devhub-base \
  --slug lark-cli-devhub-base \
  --name "Lark CLI Dev Hub Base" \
  --version 0.1.0 \
  --tags feishu,lark,base,knowledge-base

npx -y clawhub@0.16.0 publish skills/lark-cli-devhub-docs-wiki \
  --slug lark-cli-devhub-docs-wiki \
  --name "Lark CLI Dev Hub Docs Wiki" \
  --version 0.1.0 \
  --tags feishu,lark,docs,wiki,knowledge-base

npx -y clawhub@0.16.0 publish skills/lark-cli-devhub-taskflow \
  --slug lark-cli-devhub-taskflow \
  --name "Lark CLI Dev Hub Taskflow" \
  --version 0.1.0 \
  --tags feishu,lark,tasks,project-management

npx -y clawhub@0.16.0 publish skills/lark-cli-devhub-whiteboard \
  --slug lark-cli-devhub-whiteboard \
  --name "Lark CLI Dev Hub Whiteboard" \
  --version 0.1.0 \
  --tags feishu,lark,whiteboard,diagrams,architecture
```

Publishing requires a ClawHub login. The GitHub install path works independently from ClawHub.

## Security Notes

Public skills are part of the agent supply chain. Keep the package boring:

- no bundled credentials
- no remote shell installers
- no hidden binary payloads
- clear script behavior
- MIT license at repository root
- validation workflow on every push
