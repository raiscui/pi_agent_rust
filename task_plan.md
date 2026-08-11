# 任务计划: rpi binary 迁移收尾

## [2026-08-12 00:34:40] [Session ID: omx-1786418643597-4bz6s9] 续档: 从默认任务计划历史恢复

### 目标

项目的唯一 shipping CLI 是 `rpi`。所有当前构建、安装、测试、发布和用户文档使用该名称，不保留 `pi` alias。完成相关 semantic graph 回归修复、质量门与 scoped commit/push。

### 历史

- 上一份计划已移动到 `archive/default_history/task_plan_2026-08-12_003440.md`。
- 归档与知识分流记录在 `archive/manifests/ARCHIVE_MANIFEST__2026-08-12_003440__task_plan_rollover.md`。

### 阶段

- [x] 迁移唯一 Cargo binary target、运行路径、安装器、CI、测试和当前用户文档到 `rpi`。
- [x] 修复并验证 drop-in lane fixture 和 macOS system alias source binding 回归。
- [x] 完成 rpi 定向测试、installer regression、fmt、all-target check、all-target clippy 与静态调用面扫描。
- [x] 执行 Compound Capture 和 Scoped Refresh,续档超过 1000 行的旧任务计划。
- [ ] 检查最终 diff,运行 ledger 与 staged UBS,只 stage 本轮文件并提交推送 `my/main`。

### 已验证事实

- `rpi` 是 `Cargo.toml` 中唯一 shipping `[[bin]]` target。
- `pi_legacy_capture` 是 feature-gated 内部 conformance utility,不属于 shipping binary。
- QuickJS 的 `process.execPath` fallback 已指向 `/usr/bin/rpi`。
- 所有相关定向回归与 Rust 质量门已在续档前通过。

### 当前状态

**正在执行阶段 5** - 先审查和界定本轮 diff,然后运行提交前质量门。任何其他会话的未跟踪目录保持原样且不 stage。

## [2026-08-12 00:37:54] [Session ID: omx-1786418643597-4bz6s9] 阶段 5 更新: 完成记录与提交范围确认

### 已完成

- WORKLOG、ERRORFIX、notes 与 archive manifest 已记录当前证据、修复和续档路径。
- LATER_PLANS 已补充 `rpi` 本地安装说明;旧 Cargo `pi` 未删除,因为未获得删除授权。
- EPIPHANY_LOG 已回顾。没有发现需要脱离当前任务立即处理的新架构风险,因此不追加。

### 接下来

- [ ] 运行 beads ledger reconciliation。
- [ ] 精确 stage 本轮 tracked 与新长期文件,不 stage 3 个其他会话的未跟踪目录。
- [ ] 运行 staged UBS,提交并推送 `my/main`。

### 当前状态

**正在运行提交前质量门** - 质量门通过后再暂存本轮已审查文件。
