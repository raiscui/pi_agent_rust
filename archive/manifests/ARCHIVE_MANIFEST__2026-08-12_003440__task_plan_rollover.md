# 默认任务计划续档清单

## [2026-08-12 00:34:40] [Session ID: omx-1786418643597-4bz6s9] 归档: 默认 `task_plan.md` 超过行数阈值

### 归档范围

| 原路径 | 归档路径 | 原因 |
| --- | --- | --- |
| `task_plan.md` | `archive/default_history/task_plan_2026-08-12_003440.md` | 文件达到 1617 行,超过 1000 行续档阈值。 |

### 已完成的知识处置

- Capture: `docs/solutions/security-issues/macos-system-alias-source-binding.md`。
- Scoped Refresh: `docs/testing-policy.md` 已核对,保持不变。
- AGENTS 索引已加入新 solution 的读取入口。
- 没有新增 self-learning skill。该修复的复现命令与边界都已在 solution 中记录,但尚不构成需要独立执行协议的跨项目流程。

### 本轮事实摘要

- rpi 是唯一 shipping binary;不保留 `pi` alias。
- macOS `/var`、`/tmp` 系统 alias 仅在 root owner 和固定 target 同时满足时允许用于 source binding;用户 symlink 继续 fail-closed。
- drop-in certification fixture 改为自包含的 20-gate fixture,并修正 `opportunity_matrix_integrity` 的严格名称失配。

### 验证证据

- `cargo test -j 2 --test semantic_workspace_graph_builder -- canonical_dropin_verdict_uses_release_gate_age_limit --exact`
- `cargo test -j 2 --test semantic_workspace_graph_builder -- canonical_dropin_verdict_rejects_symlinked_repository_path_components --exact`
- `cargo test -j 2 --test semantic_workspace_graph_builder -- performance_budget_freshness_accepts_clean_head_bound_artifact --exact`
- `cargo fmt --check`
- `cargo check -j 2 --all-targets`
- `cargo clippy -j 2 --all-targets -- -D warnings`

### 保留的活跃文件

- `notes.md`、`WORKLOG.md`、`LATER_PLANS.md`、`ERRORFIX.md`、`EPIPHANY_LOG.md` 均未超过 1000 行,继续作为活跃默认上下文。
- 新的 `task_plan.md` 从本次收尾、quality gate 和提交状态继续记录。
