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

## [2026-08-12 00:45:01] [Session ID: omx-1786418643597-4bz6s9] 阶段 5 完成: 提交与远端同步

### 完成结果

- beads ledger reconciliation 通过,没有 orphan ledger gap 或失配的 gap-tracking bead。
- staged UBS 在 60 秒内完成且没有 finding;staged `git diff --check` 通过。
- 本轮 66 个文件已提交为 `700cd779 feat(cli): rename shipping binary to rpi`。
- `git pull --rebase my main` 成功;`git push my main` 和 `git push my main:master` 成功。
- `HEAD`、`my/main` 与 `my/master` 均为 `700cd779f52a9f61cc3900586ae3cd023b09902a`。

### 保留状态

- 未跟踪的 `legacy_pi_mono_code/pi-mono/pnpm-lock.yaml`、`tests/cross_platform_reports/macos/`、`tests/evidence_bundle/` 是其他会话产物,未修改也未提交。

### 最终待办

- [x] 检查最终 diff,运行 ledger 与 staged UBS,只 stage 本轮文件并提交推送 `my/main`。

### 当前状态

**任务完成** - rpi binary 迁移、认证回归修复、质量门、知识 Capture、上下文续档和远端同步均已完成。

## [2026-08-12 00:50:13] [Session ID: omx-1786418643597-4bz6s9] 新任务: 默认 agent 配置目录迁移到 `.rpi/agent`

### 目标

将当前项目的默认 agent 配置根目录从 `.pi/agent` 改为 `.rpi/agent`,不保留旧目录 fallback 或迁移兼容层。

### 阶段

- [ ] 枚举运行时路径真相源、安装器、测试和当前文档中的 `.pi/agent` 引用,区分历史与外部项目记录。
- [ ] 修改默认配置目录及其关联安装、卸载和 resource discovery 逻辑。
- [ ] 更新最小回归测试和当前用户文档,确认不会创建或读取 `.pi/agent`。
- [ ] 运行定向测试、fmt、all-target check、all-target clippy 和静态扫描。
- [ ] 记录、质量门、scoped commit 与 `my/main` push。

### 当前状态

**正在执行阶段 1** - 先定位全部运行时路径写入点和读取点,再在单一默认路径源处修改。

## [2026-08-12 01:00:43] [Session ID: omx-1786418643597-4bz6s9] 阶段 1 完成: 全局目录路径盘点

### 已验证事实

- 默认全局目录的唯一运行时真相源是 `src/config.rs` 的 `global_dir_from_env()`;未设置 `PI_CODING_AGENT_DIR` 时已返回 `~/.rpi/agent`。
- `src/resources.rs` 与 `src/extensions_js.rs` 的模块缓存已改为从 `Config::global_dir()` 派生,没有独立拼接旧路径。
- 剩余的 `~/.pi/agent` 命中属于源代码和测试注释、错误提示、测试夹具、E2E 脚本以及当前用户文档;项目级 `.pi/` 路径不在变更范围内。
- `.pi/agent` 的 Kimi device ID fallback 已移除,因此不会再读取该旧目录。

### 状态变更

- [x] 枚举运行时路径真相源、安装器、测试和当前文档中的 `.pi/agent` 引用,区分历史与外部项目记录。
- [ ] 修改默认配置目录及其关联安装、卸载和 resource discovery 逻辑。

### 当前状态

**正在执行阶段 2** - 同步剩余源代码、测试和当前文档的全局目录表述,保留项目级 `.pi/` 路径与历史证据。

## [2026-08-12 01:11:21] [Session ID: omx-1786418643597-4bz6s9] 阶段 2 和 3 完成: 目录迁移实施与文档同步

### 已完成

- [x] 修改默认配置目录及其关联安装、卸载和 resource discovery 逻辑。
- [x] 更新最小回归测试和当前用户文档,确认不会创建或读取 `.pi/agent`。

### 实施结论

- 所有全局路径改为 `~/.rpi/agent`;项目级 `.pi/` 保持原样。
- 缓存目录统一通过 `Config::global_dir()` 解析,移除手写 `.pi/agent/cache/modules` 的重复来源。
- 当前文档、错误提示、E2E 脚本和测试夹具均使用新目录。
- `jq empty` 和 `bash -n tests/run_e2e.sh` 已通过;静态扫描只保留项目级 `.pi` 命中。

### 当前状态

**正在执行阶段 4** - 运行默认目录单测、格式化检查、全 target 编译与 clippy,确认改动可构建且无 lint 回归。

## [2026-08-12 01:13:00] [Session ID: omx-1786418643597-4bz6s9] 阶段 4 命令修正: Cargo 测试参数位置

### 遇到的错误

- `cargo test -j 2 --lib config::tests::global_dir_defaults_to_rpi_agent --exact` 在参数解析阶段失败,提示 `--exact` 必须作为测试 harness 参数传入。

### 决议

- 改用 `cargo test -j 2 --lib config::tests::global_dir_defaults_to_rpi_agent -- --exact` 重跑同一测试。该错误未执行测试代码,不代表实现回归。

## [2026-08-12 01:22:52] [Session ID: omx-1786418643597-4bz6s9] 阶段 4 质量门修复: 无意义 Result 包装

### 现象

- `cargo clippy -j 2 --all-targets -- -D warnings` 报 `tests/semantic_workspace_graph_builder.rs:123` 的 `clippy::unnecessary_wraps`。

### 已验证结论

- 静态阅读确认 `canonical_certification_lane_fixture()` 只构造 JSON 并无条件返回 `Ok`。
- clippy 的动态输出指出同一函数和同一 lint;5 个调用点仅用 `?` 解包成功结果。

### 修复计划

- 将该 fixture 改为直接返回 `serde_json::Value`,并移除调用点的无意义 `?`。这不改变 fixture 数据和测试行为。

## [2026-08-12 01:30:34] [Session ID: omx-1786418643597-4bz6s9] 阶段 4 完成: 目录迁移与质量门验证

### 已完成

- [x] 运行定向测试、fmt、all-target check、all-target clippy 和静态扫描。

### 验证结果

- `config::tests::global_dir_defaults_to_rpi_agent`: 1 passed。
- `canonical_dropin_verdict_uses_release_gate_age_limit`: 1 passed。
- `cargo fmt --check`、`cargo check -j 2 --all-targets` 和 `cargo clippy -j 2 --all-targets -- -D warnings`: 通过。
- 旧全局目录静态扫描为零;仅剩项目级 `.pi/agents` 和 `.pi/mcp.json`。

### 已知边界

- `proc-macro-error2 v2.0.1` 的 future-incompat 来自 `charmed-bubbletea-macros`,已记入后续计划。
- macOS 链接大型 lib test 时出现 compact-unwind warning,不影响测试结果,且不应通过修改本仓库发布配置规避。

### 当前状态

**正在执行阶段 5** - 审查完整 diff,运行 ledger 与 staged UBS,只暂存本轮文件并提交推送 `my/main`。

## [2026-08-12 01:32:18] [Session ID: omx-1786418643597-4bz6s9] 审查扩展: 现行文档仍引用已删除的 `pi` CLI

### 现象

- 当前 README、CLI help、错误提示和多份现行运行指南仍将 `pi` 作为可执行命令,与唯一 shipping binary 为 `rpi` 的已验证契约冲突。

### 已验证结论

- 静态扫描确认命中分为两类: 需要修改的 CLI 调用和需要保留的 crate/schema 名称、项目级 `.pi/` 路径、历史 evidence。
- 保留旧命令会使用户复制现行文档后直接失败,因此不能作为本轮提交的遗留项。

### 追加阶段

- [ ] 将现行 source 的用户提示和现行用户文档中的 `pi` CLI 调用统一为 `rpi`。
- [ ] 重新运行静态调用面扫描与全部质量门,再执行提交和推送。

### 当前状态

**正在执行追加修复** - 只替换实际命令调用,不改 crate/schema、项目级 `.pi` 或历史证据。

## [2026-08-12 01:36:03] [Session ID: omx-1786418643597-4bz6s9] 继续: 收敛遗留的 `pi` 命令调用

### 行动目的

- 用户已确认按建议继续。唯一 shipping binary 已是 `rpi`,因此所有当前运行时提示、SDK 默认命令和现行用户文档必须指向 `rpi`。
- 保持单一真相源: 可执行命令统一为 `rpi`;crate 名、协议/schema 标识、NPM 包字段和项目级 `.pi/` 保持不变。

### 执行步骤

- [ ] 阅读每个命中的 source 与文档上下文,分类命令调用和非命令标识。
- [ ] 修改实际 CLI 调用和 SDK 默认 binary,新增或调整最小回归测试。
- [ ] 重新运行静态扫描、定向测试、fmt、all-target check 与 clippy。
- [ ] 更新账本,执行 ledger、staged UBS、scoped commit 与 `my/main`/`my/master` 推送。

### 当前状态

**正在执行追加步骤 1** - 先确认每一个命中是否确实面向用户或实际启动子进程,再开始编辑。

## [2026-08-12 01:46:03] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 1 和 2 完成: 统一 `rpi` 调用面

### 已完成

- [x] 阅读每个命中的 source 与文档上下文,分类命令调用和非命令标识。
- [x] 修改实际 CLI 调用和 SDK 默认 binary,新增或调整最小回归测试。

### 实施结论

- Clap 程序名、空参数预处理和 SDK 子进程默认值均为 `rpi`。
- 运行时错误、doctor remediation、扩展策略 JSON、安装提示和现行操作文档均改为 `rpi`。
- `pi` crate、package manifest `pi` 字段、`pi.*` schema、项目级 `.pi/` 和历史 evidence 保持不变。

### 当前状态

**正在执行追加步骤 3** - 运行静态命中分类、定向单测与 Rust 质量门,确认命令改名没有破坏非命令标识。

## [2026-08-12 02:05:20] [Session ID: omx-1786418643597-4bz6s9] 续档: 恢复追加步骤 3 的最终质量门

### 当前证据

- 默认全局目录、运行时缓存和唯一 shipping CLI 的修改已完成,`git diff --check` 已通过。
- 前一轮的 `cargo fmt --check` 启动后没有保存最终输出,因此本轮会从格式化检查重新开始,再顺序运行编译与 clippy。
- `legacy_pi_mono_code/pi-mono/pnpm-lock.yaml`、`tests/cross_platform_reports/macos/` 和 `tests/evidence_bundle/` 是其他会话的未跟踪产物,继续保持不变且不纳入暂存范围。

### 后续步骤

- [ ] 重新运行 fmt、all-target check 与 all-target clippy。
- [ ] 重跑旧目录静态分类扫描,只允许明确保留的历史材料命中。
- [ ] 更新账本,执行 ledger、scoped staged UBS、提交并推送 `my/main` 与 `my/master`。

### 当前状态

**正在执行追加步骤 3** - 从可重复的格式化检查恢复质量门,随后再进入提交前审查。

## [2026-08-12 02:05:45] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 进度: 格式化检查通过

### 已完成

- [x] `cargo fmt --check` 通过,没有格式化差异。

### 正在进行

- [ ] 运行 `cargo check -j 2 --all-targets`,确认所有编译目标通过。
- [ ] 运行 `cargo clippy -j 2 --all-targets -- -D warnings`,确认没有新增 lint 回归。

### 当前状态

**正在执行追加步骤 3** - 格式化层已通过,开始全目标编译检查。

## [2026-08-12 02:06:10] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 环境记录: RCH 不可用

### 现象

- 尝试执行 `rch exec -- cargo check -j 2 --all-targets` 时, shell 返回 `rch: No such file or directory`。

### 结论

- 当前环境没有安装 RCH,该失败发生在 Cargo 启动之前,不代表源代码或本轮改动失败。
- 继续采用受限并发 `-j 2` 的本地 Cargo 检查,保持既定资源上限。

### 当前状态

**正在执行追加步骤 3** - 改用本地全目标编译检查。

## [2026-08-12 02:06:45] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 进度: 全目标编译通过

### 已完成

- [x] `cargo check -j 2 --all-targets` 通过,没有编译错误。

### 正在进行

- [ ] 运行 `cargo clippy -j 2 --all-targets -- -D warnings`,确认没有新增 lint 回归。

### 当前状态

**正在执行追加步骤 3** - 开始严格 Clippy 检查。

## [2026-08-12 02:07:25] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 进度: 严格 Clippy 通过

### 已完成

- [x] `cargo clippy -j 2 --all-targets -- -D warnings` 通过,没有新增 lint。

### 正在进行

- [ ] 扫描旧的 `~/.pi/agent` 全局目录命中,并核对剩余命中是否全部属于明确保留的历史材料。
- [ ] 扫描现行命令调用面,确保 shipping CLI 始终为 `rpi`。

### 当前状态

**正在执行追加步骤 3** - 开始静态命中分类。

## [2026-08-12 02:08:10] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 发现: 静态扫描暴露遗漏的现行命令引用

### 现象

- 完整扫描发现 `src/cli.rs`、`src/sdk.rs`、`src/subagents.rs` 与多个现行文档仍含 `pi` 作为本项目二进制名。
- 扫描结果也包含 TypeScript Pi、crate/schema 标识、历史讨论、规划材料和 beads 历史,这些不是本轮要修改的运行命令。

### 当前假设与验证计划

- 当前假设是: `src/subagents.rs` 的默认子进程路径和 Rust CLI 测试参数需要改为 `rpi`;现行发布、终端和 swarm 操作文档中的具体命令也需要同步。
- 最强备选解释是: 个别命中属于兼容性或上游引用,替换会改变不属于 Rust CLI 的语义。
- 下一步逐项阅读命中上下文,以“是否实际启动或指导本项目 rpi binary”为唯一分类条件;不满足该条件的引用保持原样。

### 当前状态

**正在执行追加步骤 3 分类修复** - 质量门本身已通过,但静态扫描发现范围遗漏,必须先完成分类与修复后重跑所有门禁。

## [2026-08-12 02:10:20] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 进度: 完成遗漏调用面修复

### 已完成

- [x] 将 SDK 初始化 argv、子代理测试构造、README、发布说明、终端说明、swarm 运行手册、扩展场景与对应 golden 统一为 `rpi`。
- [x] 将两份 Rust-port 规划规格中的全局目录统一为 `~/.rpi/agent`;项目级 `.pi/` 和 `pi` crate/schema 保持原样。
- [x] 修正发布验证矩阵的笔误: 保留的 TypeScript 命令为 `pi`,Rust 命令为 `rpi`。

### 遇到的错误

- 首次静态扫描使用了 lookbehind,但没有传入 `rg --pcre2`,因此在正则解析阶段失败。已改用 `--pcre2` 重跑;该错误没有读取或修改源文件。
- 首次合并追加 task_plan 和 notes 的补丁因 notes 历史锚点不匹配而未应用。随后已读取文件末尾,将以独立追加补丁记录,没有覆盖任何既有内容。

### 接下来

- [ ] 审查本次补丁和 JSON 有效性,确认没有误改历史或外部项目引用。
- [ ] 运行 `cli_metadata_uses_rpi`、`global_dir_defaults_to_rpi_agent`、swarm replay fixture 定向测试,然后重跑 fmt、all-target check 与 clippy。
- [ ] 重跑分类静态扫描,更新 notes 与 WORKLOG,完成 ledger、staged UBS、scoped commit 和双分支 push。

### 当前状态

**正在执行追加步骤 3 验证** - 先验证补丁的语义和数据格式,再进入 Rust 质量门。

## [2026-08-12 02:11:20] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 进度: 补丁审查与数据格式通过

### 已完成

- [x] `git diff --check` 通过。
- [x] 3 个变更后的 swarm JSON golden/fixture 均通过 `jq empty`。
- [x] 审查确认当前 patch 只修改 Rust CLI 的默认 argv、面向用户的命令说明、全局目录规范和对应 golden;保留 TypeScript、crate/schema 和项目级 `.pi/` 语义。

### 正在进行

- [ ] 运行 CLI、配置和 swarm replay 定向回归测试。
- [ ] 重跑 fmt、all-target check、all-target clippy,然后执行最终分类扫描。

### 当前状态

**正在执行追加步骤 3 定向测试** - 先证明公开命令和默认目录契约,再执行完整质量门。

## [2026-08-12 02:12:20] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 进度: 定向回归通过

### 已完成

- [x] `cargo test -j 2 --lib cli::tests::cli_metadata_uses_rpi -- --exact` 通过。
- [x] `cargo test -j 2 --lib config::tests::global_dir_defaults_to_rpi_agent -- --exact` 通过。
- [x] `cargo test -j 2 --test swarm_replay_trace_contract source_inventory_scenario_suite_covers_unavailable_and_malformed_inputs -- --exact` 通过。

### 正在进行

- [ ] 重跑 `cargo fmt --check`、`cargo check -j 2 --all-targets` 与 `cargo clippy -j 2 --all-targets -- -D warnings`。
- [ ] 用已知保留范围重跑旧目录和旧命令静态分类扫描。

### 当前状态

**正在执行追加步骤 3 完整质量门** - 定向契约已确认,开始重跑全目标检查。

## [2026-08-12 02:13:35] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 进度: Rust 质量门通过

### 已完成

- [x] `cargo fmt --check` 通过。
- [x] `cargo check -j 2 --all-targets` 通过。
- [x] `cargo clippy -j 2 --all-targets -- -D warnings` 通过。

### 正在进行

- [ ] 扫描当前运行面中的旧全局目录和旧 Rust CLI 命令,确认残余命中全部属于历史、上游或 TypeScript 语义。
- [ ] 记录最终验证结果,执行 ledger、scoped staged UBS、提交和 `my/main`/`my/master` 推送。

### 当前状态

**正在执行追加步骤 3 最终分类扫描** - Rust 质量门已通过,开始验证文本与路径迁移边界。

## [2026-08-12 02:15:10] [Session ID: omx-1786418643597-4bz6s9] 追加步骤 3 修正: 完成规划规范的剩余调用面迁移

### 已完成

- [x] 同步 `SYNC_STRATEGY.md` 的 lock 路径与计划命令。
- [x] 同步 `EXTENSIONS.md` 的扩展日志路径与 policy 操作命令。
- [x] 同步 `EXISTING_PI_STRUCTURE.md` 的 package 子命令,并同步 recovery runbook 与 performance baseline 的 Rust CLI 文本。

### 验证边界

- `docs/releasing.md` 中保留一条 `pi --version`,它明确说明已存在的 TypeScript 命令在迁移后仍保持不变;相邻行明确要求 `rpi --version` 解析到 Rust build。
- `docs/discuss/`、`docs/EXTENSION_CANDIDATES.md`、`docs/LEGACY_EXTENSION_RUNNER.md`、`docs/evidence/` 和 benchmark 历史材料属于上游、历史或外部比较,不作为当前 Rust CLI 文档替换对象。

### 接下来

- [ ] 重跑全局目录和 CLI 命令分类扫描,确认当前运行面无遗漏。
- [ ] 写入最终账本、运行 ledger 与 staged UBS,完成 scoped commit 和远端同步。

### 当前状态

**正在执行追加步骤 3 最终扫描** - 规划规范已同步,只剩文本边界证明与交付收尾。

## [2026-08-12 02:23:10] [Session ID: omx-1786418643597-4bz6s9] 阶段 5 进度: 提交前门禁通过

### 已完成

- [x] 运行面扫描确认旧全局目录和 Rust `pi` 命令不存在;仅保留明确的 TypeScript、上游和历史语义。
- [x] 变更后的 provider JSON、swarm schema 与 golden 均通过 `jq empty`。
- [x] `./scripts/reconcile_beads_ledger.sh` 通过,没有 orphan gap。
- [x] 已精确暂存本轮 99 个已跟踪文件;其他会话的 3 个未跟踪目录保持未暂存。
- [x] `ubs --staged --only=rust .` 通过,没有 finding。

### 正在进行

- [ ] 运行 staged diff 检查和 Beads 同步,提交并推送 `my/main` 与 `my/master`。

### 当前状态

**正在执行阶段 5 提交** - 所有实现与质量门已完成,只剩 Git 交付。

## [2026-08-12 02:24:30] [Session ID: omx-1786418643597-4bz6s9] 阶段 5 完成: 提交与远端同步

### 完成结果

- [x] 本轮修改已提交为 `817ab928 feat(config): move global agent directory to rpi`。
- [x] `git pull --rebase my main`、`git push my main` 与 `git push my main:master` 全部通过。
- [x] `my/main` 与 `my/master` 均已同步到 `817ab928`。

### 保留状态

- `legacy_pi_mono_code/pi-mono/pnpm-lock.yaml`、`tests/cross_platform_reports/macos/` 与 `tests/evidence_bundle/` 是其他会话的未跟踪产物,未修改也未提交。

### 当前状态

**任务完成** - 默认全局目录、Rust CLI 调用面、当前运行文档、fixture 和 provider 示例已统一为 `.rpi/agent` 与 `rpi`。
