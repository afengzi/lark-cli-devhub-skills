# Bug 排查路径模板

## 入口

| 字段 | 内容 |
|---|---|
| Project |  |
| Area |  |
| Symptom |  |
| First Seen |  |
| Task |  |

## 排查地图

1. 明确症状和影响范围。
2. 搜索历史 Bugfix / Pitfall / Playbook。
3. 找到真实证据，不用猜。
4. 区分根因、触发条件和偶发现象。
5. 最小修复。
6. 验证。
7. 写回知识库。

## 证据清单

| 层 | 要看什么 | 结果 |
|---|---|---|
| 用户输入 | 原始需求、截图、复现步骤 |  |
| 前端 | 状态、请求、控制台、组件边界 |  |
| API | 请求体、响应、错误码、trace |  |
| 后端 | 日志、业务分支、异常栈 |  |
| 数据库 | 真实记录、状态、幂等键 |  |
| 第三方 | 权限、scope、远端返回 |  |
| 测试 | 失败用例、覆盖缺口 |  |

## 分支判断

| 判断 | 去哪里 |
|---|---|
| 历史有同类问题 | 先读旧 Bugfix/Pitfall |
| 权限或 scope 可疑 | 先做 auth check |
| 写入失败 | 检查 outbox，不伪造 receipt |
| UI 现象不稳定 | 查真实状态流和 API contract |
| 数据不一致 | 查 record_id / idempotency / source_event_id |

## 收尾

- [ ] Task 更新
- [ ] AI Run 写入
- [ ] Bugfix 写入
- [ ] Pitfall 或 Playbook 更新
- [ ] 关联字段已回填
- [ ] receipt 存在
