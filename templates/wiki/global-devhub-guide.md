# Dev Hub 使用说明

## 目标

Dev Hub 是给开发者和 AI Agent 共用的项目知识系统。它不替代代码仓库，也不替代 Agent memory；它保存可复查、可检索、可关联的开发事实。

## 分层

| 层 | 用途 | AI 读取方式 |
|---|---|---|
| Feishu Base | 结构化事实、任务镜像、Bugfix、AI Run、Release、Artifact、Decision | 先搜 Base，再打开必要文档 |
| Wiki / Docs | 长文、模板、复盘、设计说明、报告 | 通过 Artifact 记录或目录进入 |
| Whiteboard | 架构图、流程图、排查路径、知识图谱 | 必须配套 Artifact 文本摘要 |
| Feishu Task | 原生任务执行、提醒、状态流转 | Base Tasks 保存 URL/GUID 镜像 |
| Receipts / Outbox | 写入凭证和失败补偿 | 每次写入后必须检查 |

## 推荐日常流程

1. 开始修 bug 前：搜索 `Bugfixes`、`Pitfalls`、`Playbooks`、`Decisions`、`Areas`。
2. 没有任务时：先创建 Feishu Task，再在 Base `Tasks` 创建镜像。
3. 修复中：把关键证据、命令、失败路径记录到 AI Run 草稿。
4. 修复后：写 `Bugfixes`、`AI Runs`，必要时补 `Pitfalls` 或 `Playbooks`。
5. PR 创建或更新：写 `AI Runs`。
6. PR Review：写 `Decisions` 或 `Bugfixes`。
7. 合并 main：写 `Releases`。
8. 架构或流程变化：更新 Whiteboard，并写 `Artifacts` 摘要。

## 写入纪律

- 不要伪造 receipt。
- 写 Base 成功后，必须在 `.devhub/receipts/` 留凭证。
- 写入失败时，必须在 `.devhub/outbox/` 留可重试项。
- `push` / `PR` 成功不等于知识库写入成功。
- 跨记录关系写入 `Record Relations`；业务表保持轻量，用标题、关键词和证据字段帮助检索。

## AI 回看顺序

1. `Tasks`: 当前目标、状态、Feishu Task URL/GUID。
2. `AI Runs`: 上次 Agent 做了什么、查了什么、验证了什么。
3. `Bugfixes`: 症状、证据、根因、修复、验证。
4. `Pitfalls`: 下次优先排除的坑。
5. `Playbooks`: 可重复排查路径。
6. `Decisions`: 为什么这样做，以及何时重新评审。
7. `Artifacts`: Docs、Whiteboards、报告和外部链接。

## 维护节奏

| 节奏 | 动作 |
|---|---|
| 每次任务完成 | Task 状态更新为 Verify 或 Done；写 AI Run |
| 每次 bug 修复 | 写 Bugfix，更新 Pitfall/Playbook |
| 每次架构变化 | 更新 Whiteboard 和 Artifact |
| 每周 | 生成周报，归档过期任务，标记 Stale |
| 每月 | 回看高频 Pitfalls，沉淀通用经验 |
