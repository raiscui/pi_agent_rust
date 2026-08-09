# secret_cleanup — 归档索引

## 摘要
- **主题**: DeepSeek API Key 本地与仓库隔离 (脱敏清理闭环)
- **Session ID**: `019f5551-7950-7a21-b33b-617b24f4f8d0` (2026-07-12)
- **归档时间**: 2026-08-09 (Session ID: 1)
- **归档原因**:
  1. 阶段 1-5 已完成 (脱敏盘点 / 清理明文 / .envrc 隔离 / 扫描验证 / 证据记录)。
  2. 阶段 6 部分完成 (history rewrite + reflog + mirror 清理已完成)。
  3. 阶段 6 仍剩 **不可逆外部操作** 与 **不可逆 Git 操作**, 必须由用户明确授权。
  4. LATER_PLANS 中的 4 条 "必做事项" 已转录到主线 `LATER_PLANS.md` 顶部, 不会被这次归档丢失。

## 文件清单
| 文件 | 角色 | 关键结论 |
|---|---|---|
| `task_plan__secret_cleanup.md` | 主计划 | 阶段 1-5 全部完成, 阶段 6 partial |
| `WORKLOG__secret_cleanup.md` | 任务产出 | 隔离清理的具体步骤 + 命中清单 |
| `EPIPHANY_LOG__secret_cleanup.md` | 重大发现 | WORKLOG.md:414-507 完整环境快照含其他凭据, 必须整体移除 |
| `ERRORFIX__secret_cleanup.md` | bug 修复 | WORKLOG.md line 486 / `.omx/logs/turns-2026-06-29.jsonl:3` 真值命中 |
| `LATER_PLANS__secret_cleanup.md` | 后续 | DeepSeek 旧 Key 吊销 + 其他凭据轮换 + 引用清理 |
| `notes__secret_cleanup.md` | 笔记 | 当前树 / Git 跟踪面 / 可达历史的脱敏证据 |

## 现状判断
- **本地 + 当前树**: 已隔离, 真值只在 Git 忽略的 `.envrc`。
- **Git 历史**: `main` + `feature/read-scope-allowlist` 已重写, reflog 与旧对象已清理。
- **待用户授权 (4 条)**:
  1. 在 DeepSeek 控制台吊销旧 Key, 创建新 Key, 更新 `.envrc`。
  2. 评估完整环境快照中出现过的其他凭据, 对仍有效的 token 执行轮换。
  3. (历史已重写, 此条主要是 await 1-2 的执行窗口)。
  4. (任何后续对 `WORKLOG.md` 等敏感引用的二次清理都需用户复检)。

## 重新激活条件
1. 用户显式要求完成 DeepSeek 旧 Key 吊销 + 新 Key 注入 `.envrc`。
2. 用户显式要求对其他凭据做 round-robin 轮换。
3. 任何重新开放 `__secret_cleanup` 的尝试都必须先回看本 INDEX, 不要从零重做盘点。
