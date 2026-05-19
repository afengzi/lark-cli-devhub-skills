# AI 写入规则

## 写入前

1. 确认当前项目名，不要写到其他项目目录。
2. 如果没有原生 Feishu Task，先创建任务；已有任务则更新状态。
3. 读取 Base 字段清单，不猜字段名、不猜类型。
4. 搜索历史记录，避免重复踩坑。
5. 明确本次写入对象：Task、AI Run、Bugfix、Release、Artifact、Decision、Pitfall、Playbook。

## 写入中

| 表 | 必填意图 | 关键字段 |
|---|---|---|
| Tasks | 当前工作状态 | Title、Project、Area、Status、Feishu Task URL/GUID、Next Action |
| AI Runs | Agent 行动轨迹 | Actions Taken、Evidence Checked、Verification Commands、Writeback Status |
| Bugfixes | Bug 修复事实 | Symptom、Evidence、Root Cause、Fix Summary、Verification Result |
| Releases | main/PR 发布证据 | Branch、Commit SHA、Verification Result、Rollback Notes |
| Artifacts | Doc / Whiteboard / 报告索引 | Artifact Type、Source URL、Summary、AI Summary |
| Decisions | 决策和取舍 | Decision、Context、Alternatives、Tradeoffs、Review Trigger |
| Pitfalls | 可复用踩坑提醒 | Trigger Condition、Wrong Approach、Correct Approach、Next Time Check |
| Playbooks | 可复用流程 | Scenario、Diagnosis Order、Must Check Evidence、Commands |

## 关联字段

- 文档里说“单向关联 / 双向关联”。
- Base 官方底层类型：单向关联是 `18`，双向关联是 `21`。
- lark-cli shortcut 读写时可能显示 `type: "link"` 和 `bidirectional`，这是 CLI 表达，不是文档里给用户看的概念。
- 只有知道目标 `record_id` 时才写 `... Relation` 字段。
- 不知道目标时，用 `Related Tasks`、`Related Bugfixes`、`Search Keywords` 等文本字段承载可检索线索。

## 写入后

1. 用 `record-get` 或 `record-search` 验证关键字段。
2. 检查 `.devhub/receipts/` 是否有新 receipt。
3. 若失败，检查 `.devhub/outbox/` 是否有可重试记录。
4. 更新 Feishu Task 状态。
5. 最终回复用户时说明：写了哪些表、哪些关系、哪些验证通过、哪些未做。

## 禁止事项

- 不要把 secrets、token、完整 `.env` 写入知识库。
- 不要把任务只写在 Base 而不创建/更新原生 Feishu Task。
- 不要只写 Wiki，不写 Base Artifact。
- 不要只画白板，不写 Artifact 摘要。
- 不要把旧字段名当新字段名继续传播。
- 不要为了通过 hook 伪造 receipt。
