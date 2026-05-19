# Marketplaces And Distribution

## GitHub

Primary distribution is GitHub because `npx skills` can install from `owner/repo`:

```bash
npx skills add afengzi/feishu-dev-hub-skills --all
```

List available skills without installing:

```bash
npx skills add afengzi/feishu-dev-hub-skills --list
```

## skills.sh

`skills.sh` indexes public Agent Skills repositories that can be installed with `npx skills`. Once the GitHub repository is public and installable, it can be discovered through the Skills directory ecosystem.

## ClawHub

ClawHub publishes one skill folder at a time. Publish each folder under `skills/`:

```bash
npx -y clawhub@0.16.0 login

npx -y clawhub@0.16.0 publish skills/feishu-dev-hub \
  --slug feishu-dev-hub \
  --name "Feishu Dev Hub" \
  --version 0.1.0 \
  --tags feishu,lark,devtools,knowledge-base,codex,claude-code \
  --clawscan-note "Uses local Python and lark-cli. Network access is delegated to the user's configured lark-cli credentials; no credentials are bundled."

npx -y clawhub@0.16.0 publish skills/feishu-devhub-base \
  --slug feishu-devhub-base \
  --name "Feishu Dev Hub Base" \
  --version 0.1.0 \
  --tags feishu,lark,base,knowledge-base

npx -y clawhub@0.16.0 publish skills/feishu-devhub-docs-wiki \
  --slug feishu-devhub-docs-wiki \
  --name "Feishu Dev Hub Docs Wiki" \
  --version 0.1.0 \
  --tags feishu,lark,docs,wiki,knowledge-base

npx -y clawhub@0.16.0 publish skills/feishu-devhub-taskflow \
  --slug feishu-devhub-taskflow \
  --name "Feishu Dev Hub Taskflow" \
  --version 0.1.0 \
  --tags feishu,lark,tasks,project-management

npx -y clawhub@0.16.0 publish skills/feishu-devhub-whiteboard \
  --slug feishu-devhub-whiteboard \
  --name "Feishu Dev Hub Whiteboard" \
  --version 0.1.0 \
  --tags feishu,lark,whiteboard,diagrams,architecture
```

Publishing requires a ClawHub login. The repository can be prepared and pushed without it.

## Security Notes

Public skills are part of the agent supply chain. Keep the package boring:

- no bundled credentials
- no remote shell installers
- no hidden binary payloads
- clear script behavior
- MIT license at repository root
- validation workflow on every push
