# Domain Map

Use one small domain document per Feishu capability. This keeps the orchestrator skill easy to load and lets each domain evolve independently.

## Split

| Domain | Skill | Use For |
|---|---|---|
| Base | `feishu-devhub-base` | Structured records, schema, views, dashboards, AI-readable database |
| Docs/Wiki | `feishu-devhub-docs-wiki` | Long-form notes, runbooks, design docs, wiki hierarchy |
| Taskflow | `feishu-devhub-taskflow` | Tasks, bug queues, ownership, status, current work |
| Whiteboard | `feishu-devhub-whiteboard` | Architecture maps, dependency maps, flow diagrams |

## Why Split

- Better token economy: the agent reads only the domain it needs.
- Cleaner maintenance: Base fields can change without rewriting Whiteboard guidance.
- Better marketplace packaging: users can install the whole pack or a subset.
- Less conflict with project memory: Dev Hub records factual work; skills only teach how to operate the system.

## When To Add A New Domain

Create another domain skill when the domain has its own commands, safety rules, or repeated mistakes. Good candidates:

- `feishu-devhub-sheets`
- `feishu-devhub-meetings`
- `feishu-devhub-mail`
- `feishu-devhub-approval`
- `feishu-devhub-automation`
