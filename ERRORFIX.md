## [2026-06-05 13:25:00] [Session ID: omx-1780470665249-tkxhle] 问题: local-minicpm5 read post-tool 重复调用与最终文本判定

### 问题现象
- 真实 MiniCPM5 `read` 样本中, 工具执行成功后模型会再次发出同名同参 `read` ToolCall, 旧路径会触发 `Maximum tool iterations (4) exceeded`。
- 本轮初次矩阵修复后, `read` 不再超过迭代上限, 但临时矩阵脚本仍分类为 `read_final_missing_expected_text`。

### 原因
- 代码层原因: local MiniCPM5 在成功 ToolResult 后仍可能重复发起同名同参 ToolCall, prompt 无法完全约束。
- 测试层原因: `/tmp/pi_minicpm5_tool_matrix.py` 只收集 `message_update` 的 text delta, 没有读取 final `message_end` / `agent_end` assistant 文本。

### 修复
- 在 `src/agent.rs` 的 `finalize_assistant_message` 前增加 provider-local repeat guard。
- 只在 `local-minicpm5` + MiniCPM5 + 当前 assistant 只有一个 ToolCall + 同轮历史存在同名同参成功 ToolResult 时改写。
- 对 read 的 `1→TEXT` 结果去掉行号元数据, 最终只返回 `TEXT`。
- 修正 `/tmp/pi_minicpm5_tool_matrix.py` 的文本收集逻辑, 优先读取 final assistant message。

### 验证
- focused 单测全部通过。
- 真实 `read / grep / find / ls / edit` 矩阵 `tool_success=5`。
- `cargo check --all-targets`, `cargo clippy --all-targets -- -D warnings`, `cargo fmt --check` 均通过。

## [2026-06-09 16:29:00] [Session ID: omx-1780470665249-tkxhle] 错误修复: my/main 合并后的 clippy blocker 与 staged UBS 空跑

### 问题
- 最新 `my/main` 比原实现基线更新, cherry-pick 后暴露新的 initializer 缺字段和 clippy blocker。
- `cargo clippy --all-targets -- -D warnings` 曾失败在 `map_unwrap_or`, `or_fun_call`, `items_after_statements`, `uninlined_format_args`, `significant_drop_tightening`, doc paragraph 等非功能 blocker。
- 变更 amend 到 commit 后, 直接运行 `python3 scripts/check_ubs_staged_delta.py` 显示 no staged Rust files, 不能作为有效 changed-line gate。

### 原因
- `ModelEntry` / `AgentConfig` 新增字段后, 最新测试/bench/example 中的 initializer 需要显式补默认值。
- clippy blocker 属于最新 `my/main` 基线, 但在 `-D warnings` gate 下必须修复。
- UBS staged delta 脚本读取当前 git index; 已提交状态下没有 staged diff, 所以会空跑。

### 修复
- 在相关 initializer 补 `tool_use_profile: None`, 入口路径 `examples/pi_debug.rs` 保持透传实际 selection profile。
- 对 clippy blocker 做等价替换或格式修复, 不改变业务语义。
- 创建 staged-delta 临时 worktree, 基于 `my/main` 将最终 patch 应用到 index 后重新运行 `check_ubs_staged_delta.py --print-ubs-output`。

### 验证
- `cargo check --all-targets`: exit 0。
- `cargo clippy --all-targets -- -D warnings`: exit 0。
- staged-delta UBS: 50 staged Rust files, 1689 changed lines, 0 warning/critical finding on changed lines。
- SSH push 后远端 `my/main` 指向 `e0cc86895112f5600cb25c96ea5d17a74b39920d`。

## [2026-06-10 15:18:00] [Session ID: omx-1781010799354-k3m6a6] 错误修复: pi 退出后终端残留鼠标上报序列

### 问题
- 用户反馈 `pi` 退出后,终端留下大量类似 `35;23;41M` 的文本。
- 这些文本不是 Pi 的普通输出,而是 SGR mouse report 的尾部。

### 现象 -> 假设 -> 验证 -> 结论
- 现象: 退出后 shell 显示 `35;x;yM` 一类片段。
- 主假设: TUI 默认启用 all-motion + SGR mouse reporting,退出边界可能还有积压 mouse events 回落到 shell。
- 备选解释: 后台任务退出后继续写 stdout。
- 静态验证:
  - `src/interactive.rs` 默认调用 `with_mouse_all_motion()`。
  - `charmed-bubbletea` 启动时写 `EnableMouseCapture`。
  - `crossterm 0.29.0` 的 `EnableMouseCapture` 包含 `?1003h` 和 `?1006h`。
- 动态/构建验证:
  - `cargo test --package pi_agent_rust --lib -- interactive::tests::terminal_restore_sequences_disable_mouse_capture_when_enabled --exact --nocapture`: passed。
  - `cargo test --package pi_agent_rust --lib -- interactive::tests::terminal_restore_sequences_respect_disabled_mouse_capture --exact --nocapture`: passed。
  - `cargo fmt --check`: passed。
  - `cargo check --all-targets`: passed。
  - `cargo clippy --all-targets -- -D warnings`: passed。

### 修复
- 在 `run_interactive` 的 `program.run()` 返回后,无论成功还是错误,先执行 Pi 侧 `restore_interactive_terminal_after_program`。
- 该函数幂等写入终端恢复序列,包含 disable paste / disable focus / disable mouse / show cursor / leave alternate screen。
- 增加零等待、限量的 pending terminal event drain,避免已积压 mouse report 落回 shell。
- 把鼠标捕获禁用判断和光标可见性设置拆成 helper,保持 `run_interactive` 不超过 clippy 行数限制。

### 额外修复
- clippy 质量门暴露了既有阻塞:
  - `extension_dispatcher.rs` 的 io_uring placeholder 函数没有 await,改为同步函数并移除调用点 `.await`。
  - `extensions.rs` native-rust runtime 需要保持 async facade,补充 `clippy::unused_async_trait_impl` allow 和理由。
  - `sdk.rs` RPC transport 需要保持 async public API,补充 `clippy::unused_async_trait_impl` allow 和理由。
  - 两个测试里的无意义 `format!` 改成 `.to_string()`。

### 本轮自身错误
- 我第一次向 `task_plan.md` 追加记录时,把带反引号的 Markdown 放进外层双引号命令,导致 shell 误执行了 `pi` 和 `35;23;41M` 片段。
- 已按 append-only 规则在 `task_plan.md` 追加修正记录。
- 后续凡是正文包含反引号,必须直接使用单引号 heredoc,不能再包在外层双引号里。

### 仍需注意
- 测试构建仍会出现依赖级提醒: `proc-macro-error2 v2.0.1` future-incompat。
- lib test 链接阶段仍会出现 `__eh_frame section too large` linker warning。这不是本次改动引入的 Rust warning,但最终 clippy/check 均通过。

## [2026-06-10 18:44:00] [Session ID: omx-1781010799354-k3m6a6] 错误修复: pi 退出后仍显示 SGR mouse report

### 问题
- 用户在安装上一轮修复后仍复现: `Goodbye!` 之后出现 `^[[<35;x;yM` 一类内容。
- 这说明上一轮只写恢复序列和零等待 drain 并没有覆盖真实退出边界。

### 现象 -> 假设 -> 验证 -> 结论
- 现象: 残留字节出现在 `Goodbye!` 之后,形态是 SGR mouse report。
- 被推翻的旧假设: 只要写 `DisableMouseCapture` 并 `Duration::ZERO` 排空一次就足够。
- 新主假设: 默认 all-motion mouse capture 本身过度。它会把普通鼠标移动变成高频输入,退出时任何延迟事件都可能落回 shell。
- 备选解释: 仍有其它路径重新启用 mouse capture,或终端输入队列存在延迟事件。
- 静态证据: `run_interactive` 默认调用 `program.with_mouse_all_motion()`; `charmed-bubbletea` 会写 `crossterm::event::EnableMouseCapture`; `crossterm` 会启用 `?1003h` all-motion 和 `?1006h` SGR mouse mode。
- 动态证据: 安装后二进制 PTY 验证显示默认路径已经不再输出 `?1006h` 或 `?1003h`,并正常输出 `Goodbye!`。

### 修复
- 将 mouse capture 改为显式 opt-in: 默认不启用 all-motion mouse capture。
- 保留 `disable_mouse_capture: false` 作为用户 opt-in。
- `PI_NO_MOUSE_CAPTURE=1` 继续强制禁用,覆盖持久配置。
- 对 opt-in 路径保留兜底恢复,并将 drain 从零等待改为 quiet-window drain。
- 退出恢复顺序调整为先重新启 raw mode,再写恢复序列和排空输入,最后关闭 raw mode。

### 验证
- 鼠标捕获策略精确单测: passed。
- 终端恢复序列精确单测: passed。
- `cargo fmt --check`: exit 0。
- `cargo build --bin pi`: exit 0,仅第三方 `proc-macro-error2` future-incompat warning。
- `cargo check --all-targets`: exit 0,同上第三方 warning。
- `cargo clippy --all-targets -- -D warnings`: exit 0,原始输出确认只有第三方 future-incompat warning。
- `cargo install --path . --bin pi --force`: exit 0。
- 安装后二进制 PTY 验证: `has_mouse_enable_1006=False`, `has_all_motion_1003=False`, `has_goodbye=True`。

## [2026-06-11 16:58:00] [Session ID: omx-1781010799354-k3m6a6] 错误修复: 默认恢复 pi 鼠标滚轮且避免 all-motion 残留

### 问题
- 用户指出: pi 需要鼠标滚轮支持,上一轮默认关闭 mouse capture 后,滚轮不可用是不正常的。

### 现象 -> 假设 -> 验证 -> 结论
- 现象: `src/interactive.rs` 仍有 `handle_mouse_wheel`,但默认不再启用终端 mouse reporting,所以真实滚轮事件不会进入 TUI。
- 主假设: 需要恢复 mouse reporting,但不应该回到 `Program::with_mouse_all_motion()`。
- 备选解释: `Program::with_mouse_cell_motion()` 可能足够安全。
- 静态验证:
  - `charmed-bubbletea-0.2.0` 的 `with_mouse_cell_motion()` 和 `with_mouse_all_motion()` 都调用 `crossterm::event::EnableMouseCapture`。
  - `crossterm-0.29.0` 的 `EnableMouseCapture` 同时开启 `?1000h`, `?1002h`, `?1003h`, `?1015h`, `?1006h`。
  - 因此直接换成 cell-motion 仍会打开 `?1003h` all-motion,不符合目标。
- 动态验证:
  - 默认安装后二进制 PTY 捕获: `enable_1000h=True`, `enable_1006h=True`, `enable_1003h=False`, `disable_1006l=True`, `disable_1003l=True`, `goodbye=True`。
  - `PI_NO_MOUSE_CAPTURE=1` PTY 捕获: `enable_1000h=False`, `enable_1006h=False`, `enable_1003h=False`, `disable_1006l=False`, `goodbye=True`。

### 修复
- 默认重新启用 Pi 自己管理的精确 mouse reporting。
- 启用序列只写 `?1000h` + `?1006h`,恢复滚轮/按钮 SGR 报告。
- 默认不写 `?1003h`,避免普通鼠标移动持续进入 stdin。
- 保留 `disable_mouse_capture=true` / `--no-mouse-capture` / `PI_NO_MOUSE_CAPTURE=1` 作为彻底关闭鼠标捕获的逃生路径。
- 增加 `InteractiveMouseCaptureGuard`,异常路径兜底关闭 mouse mode。
- 更新配置/CLI 注释和 `EXPERIENCE.md`。

### 验证
- `cargo fmt --check`: passed。
- `cargo test --package pi_agent_rust --lib -- interactive::tests::mouse_capture --nocapture`: 2 passed。
- `cargo test --package pi_agent_rust --lib -- interactive::tests::terminal_mouse_enable_sequences --nocapture`: 1 passed。
- `cargo test --package pi_agent_rust --lib -- interactive::tests::terminal_restore_sequences --nocapture`: 2 passed。
- `cargo check --all-targets`: 0 errors,仅第三方 `proc-macro-error2 v2.0.1` future-incompat warning。
- `cargo clippy --all-targets -- -D warnings`: 0 errors,仅同一个第三方 warning。
- `cargo build --bin pi`: 0 errors,同一个第三方 warning。
- `cargo install --path . --bin pi --force`: installed `/Users/cuiluming/.cargo/bin/pi`。
- 安装后二进制 PTY 验证通过。
## [2026-06-12 17:57:10] [Session ID: codex-20260612-pi-model-max-tokens] 错误修复: OpenAI-compatible 请求忽略模型 maxTokens

### 问题
- `models.json` 中 `local-diffusiongemma-vlm` 的模型条目声明 `maxTokens=512`。
- fast-infer 的 DiffusionGemma server 脚本声明 `--max-tokens 128`。
- 真实 Pi 请求体仍发送 `max_tokens=4096`, 导致本地 VLM server 需要额外 clamp, 且用户无法从配置上理解 `4096` 来源。

### 原因
- `src/app.rs::build_stream_options()` 旧实现没有把 `selection.model_entry.model.max_tokens` 复制到 `StreamOptions.max_tokens`。
- `src/providers/openai.rs` 在 `options.max_tokens=None` 时按设计回退到 `DEFAULT_MAX_TOKENS=4096`。
- 因此 `models.json` 的 `maxTokens` 只显示在模型列表中, 没有进入真实请求预算。

### 修复
- 在 `build_stream_options()` 中设置 `max_tokens: Some(selection.model_entry.model.max_tokens)`。
- 新增单测 `build_stream_options_uses_selected_model_max_tokens`, 锁定 app 层模型预算传播。

### 验证
- 旧行为红灯: `left: None`, `right: Some(512)`。
- 修复后聚焦单测通过。
- OpenAI provider 请求体测试通过。
- `cargo fmt --check` 通过。
- `cargo build --bin pi` 通过, 只有第三方 future-incompat warning。
- `cargo install --path . --bin pi --force --locked` 成功替换 `/Users/cuiluming/.cargo/bin/pi`。
- 已安装 `pi` mock server 抓包显示 `max_tokens=512`, 不再是 `4096`。
- `cargo check --all-targets` 通过, 只有第三方 future-incompat warning。
- `cargo clippy --all-targets -- -D warnings` 通过。

## [2026-06-12 19:05:28] [Session ID: codex-20260612-rich-rust-install-e0119] 错误修复: cargo install 无锁解析到 rich_rust-0.2.1 后 E0119

### 问题

- 用户运行 `cargo install --path . --bin pi --force` 时, Cargo 解析到 `rich_rust-0.2.1`。
- 编译失败点在第三方 crate `rich_rust-0.2.1`:
  - `impl<S: Into<String>> From<S> for Choice`
  - `impl<T: Into<Text>> From<T> for Cell`
- 当前 nightly 判定这些 blanket impl 与 `time` crate 的 `HourBase` 相关 `From` 实现存在冲突风险,报 E0119。

### 原因

- 项目依赖写的是 `rich_rust = { version = "0.2.0", features = ["markdown"] }`。
- 这个版本约束不是精确 pin,无 `--locked` 安装时可以升级到 `0.2.1`。
- `cargo install --path . --bin pi --force --locked` 能成功,说明锁文件中原本可用的 `0.2.0` 组合没有这个编译错误。

### 修复

- 将 `Cargo.toml` 中 `rich_rust` 依赖改为精确版本:
  - `rich_rust = { version = "=0.2.0", features = ["markdown"] }`
- 更新 `Cargo.lock`,使锁文件回到 `rich_rust v0.2.0`。
- 保留 Cargo 自动解析出的 transitive lock 变化,没有手工伪造 lock。

### 验证

- `cargo tree -p rich_rust --locked`: 当前为 `rich_rust v0.2.0`。
- `cargo metadata --format-version 1 --locked --no-deps`: passed。
- `cargo install --path . --bin pi --force`: succeeded, replaced `/Users/cuiluming/.cargo/bin/pi`。
- `cargo fmt --check`: passed。
- `cargo check --all-targets`: 0 errors, 1 third-party `proc-macro-error2 v2.0.1` future-incompat warning。
- `cargo clippy --all-targets -- -D warnings`: 0 errors, 1 third-party future-incompat warning。

## [2026-08-11 12:55:00] [Session ID: omx-1786418643597-4bz6s9] 修复: merge 后 ToolUseProfile 加载缺失和 test-target 编译失败

### 现象
- `ModelEntry.tool_use_profile` 始终为 `None`,models.json 的 `toolUseProfiles` 和 `toolUseProfile` 未进入加载路径。
- `cargo check --bin pi` 通过,但首次 `cargo test --lib` 报 10 个编译错误。

### 原因
- merge 后 `src/models.rs` 只恢复了早期 ToolUseProfile 类型,未恢复加载、校验、继承逻辑。
- 同一文件还遗漏后续已合入的 `tools`、`skills`、`extensions` 字段和测试隔离加载入口,导致 lib test target 与其他模块契约不一致。

### 修复
- 在 `ModelsConfig`、`ProviderConfig`、`ModelConfig` 恢复 profile 配置字段。
- 在统一配置加载入口验证全部引用,在统一 custom model 应用路径解析 provider 默认和 model 覆盖。
- generated catalog 的临时 `ModelsConfig` 明确使用空 profile 表。
- 恢复 3 个 profile 扩展字段、`load_isolated` 及其他 test-target 构造器遗漏字段。

### 验证
- red: provider default 测试在 profile 为 `None` 时失败。
- green: provider default、model override、unknown reference、empty reference 共 4 条定向测试通过。
- 完整 fmt/check/clippy/workspace 结果待阶段4追加。

## [2026-08-11 13:48:42] [Session ID: omx-1786418643597-4bz6s9] 调查中: release_readiness 缺少编译期 evidence

### 现象
- `cargo check --all-targets -j 2` 在 `tests/release_readiness.rs:4804` 和 `tests/release_readiness.rs:7421` 失败。
- `include_str!` 引用的 `tests/perf/reports/budget_summary.json` 与 `tests/full_suite_gate/full_suite_verdict.json` 不存在。

### 候选假设
- 主假设: 这两个文件是被 `.gitignore` 排除的生成产物,本地未运行对应生成链,因此 all-target 编译依赖了缺失的外部 artifact。
- 备选解释: merge 删除了本应存在的受控 fixture,或者测试错误地把运行期 artifact 设成编译期硬依赖。
- 推翻主假设的证据: Git 历史显示文件本应受版本控制,或测试契约明确要求仓库 checkout 自带这两个文件。

### 验证计划
- 检查文件历史、`.gitignore`、`release_readiness` 的断言语义和 workflow/测试生成链。
- 只接受真实生成结果或正确的测试边界修复,不创建空内容和伪造认证 evidence。

## [2026-08-11 14:23:00] [Session ID: omx-1786418643597-4bz6s9] 修复: release_readiness 编译期依赖 ignored evidence

### 原因
- 两条独立历史线在 merge 后形成不一致契约: 一侧停止跟踪生成目录,另一侧新增 `include_str!` 编译期引用。
- 因此 clean checkout 即使不运行 release gate,编译 `release_readiness` test target 也会失败。

### 修复
- 性能 claim fixture 改为代码内构造 canonical 19 项预算定义与通过结果,保留 schema、inventory hash、计数和 source-binding 校验。
- full-suite fixture 改为代码内构造 20 个 gate,保留原 `17/20` 失败汇总断言。
- 没有恢复 ignored artifact,也没有伪造 release evidence。

### 验证
- `cargo test --package pi_agent_rust --test release_readiness -j 2 -- performance_budget_v2_claim_ready_contract_passes --exact`: 1 passed。
- `cargo test --package pi_agent_rust --test release_readiness -j 2 -- full_suite_gate_reads_current_total_gates_field --exact`: 1 passed。

## [2026-08-11 14:47:00] [Session ID: omx-1786418643597-4bz6s9] 追加修复: semantic graph 的 sibling evidence 引用

### 现象
- all-target check 继续报缺少 `tests/perf/reports/budget_summary.json`,位置为 `tests/semantic_workspace_graph_builder.rs:1021`。

### 原因修正
- 上一轮只处理了最初编译器报告的两个调用点,没有先用多行模式搜索全部 `include_str!` sibling。
- semantic graph 与 release readiness 都依赖完整 canonical budget inventory,直接复制定义会制造第二份测试真相源。

### 修复计划
- 将 canonical budget definitions 放入共享 test-support 模块,两份 integration test 共同调用。
- 保留各自对 result、claim readiness、inventory hash 和防伪行为的独立测试。

## [2026-08-11 21:42:00] [Session ID: omx-1786418643597-4bz6s9] 调查中: all-target clippy 的 10 个 merge 后错误

### 现象
- all-target check 已通过,但 clippy 在 `-D warnings` 下报 10 个错误。
- 错误集中于 `src/interactive.rs` 与 `src/tools.rs`,不是 `ToolUseProfile` 新逻辑产生。

### 验证计划
- 逐处读取调用上下文,优先采用等价标准库写法和正确类型转换。
- 对只因测试体量触发的 `too_many_lines`,在确认无法通过小幅重排降低复杂度后使用最窄范围 allow。
- 修复后重跑 fmt、相关定向测试、all-target check 和 clippy。

## [2026-08-12 00:34:40] [Session ID: omx-1786418643597-4bz6s9] 修复: rpi 迁移后 drop-in lane fixture 失配

### 现象
- `canonical_dropin_verdict_uses_release_gate_age_limit` 预期 `Current`,实际为 `Malformed`。

### 原因
- 自包含 fixture 的 `opportunity_matrix_integrity` gate 名称为 `Opportunity matrix integrity`。
- production 的严格契约要求 `Opportunity matrix artifact integrity`,任何 identity 字段不一致都会产生 `dropin_verdict_source_lane_invalid`。

### 修复
- 只修正 fixture 的 gate 名称,不放宽 `validate_dropin_certification_lane`。

### 验证
- 修复前: 同一精确测试失败为 `Some(Malformed)`。
- 修复后: age-limit、用户 symlink 拒绝、performance source binding 三条 semantic graph 精确测试均通过。

## [2026-08-12 01:30:34] [Session ID: omx-1786418643597-4bz6s9] 修复: clippy 拒绝无错误路径的测试 fixture

### 问题

- `cargo clippy -j 2 --all-targets -- -D warnings` 报 `tests/semantic_workspace_graph_builder.rs:123` 的 `clippy::unnecessary_wraps`。

### 原因

- `canonical_certification_lane_fixture()` 仅构造 `serde_json::Value`,没有任何可能返回错误的操作,但返回类型仍是 `TestResult<serde_json::Value>`。
- 5 个调用点都用 `?` 解包一个永远成功的结果,使测试辅助函数的错误边界与真实行为不一致。

### 修复

- 函数直接返回 `serde_json::Value`。
- 调用点移除对应的 `?`,保留 fixture JSON 和所有断言不变。

### 验证

- `cargo test -j 2 --test semantic_workspace_graph_builder canonical_dropin_verdict_uses_release_gate_age_limit -- --exact`: 1 passed。
- `cargo clippy -j 2 --all-targets -- -D warnings`: passed。

## [2026-08-12 13:28:19] [Session ID: omx-1786418643597-4bz6s9] 质量门环境错误: `/data` 临时目录不可写

### 问题

- `cargo fmt --check && cargo check -j 2 --all-targets && cargo clippy -j 2 --all-targets -- -D warnings` 未进入编译,`sccache` 在 `/data/tmp/pi_agent_rust_cargo/cuiluming/tmp` 创建临时文件时失败。

### 原因

- 当前 macOS 环境的 `/data` 为只读挂载,无法作为 Cargo target 或临时目录。

### 修复

- 使用可写的 `/private/tmp/pi_agent_rust_cargo_omx-1786418643597-4bz6s9` 与 `/private/tmp/pi_agent_rust_tmp_omx-1786418643597-4bz6s9` 重跑相同质量门。

### 验证

- 后续质量门结果将以可写临时目录下的实际输出为准。

## [2026-08-12 02:17:00] [Session ID: omx-1786418643597-4bz6s9] 修复: 默认目录与 shipping CLI 文档残留

### 现象
- 默认目录已改为 `~/.rpi/agent`,但静态扫描仍发现少量现行 Rust CLI 文档、provider 示例和 swarm fixture 使用旧路径或 `pi` 命令。

### 原因
- 前一轮扫描范围只覆盖了核心 source 与部分文档,没有覆盖所有 provider JSON 和规划规范。

### 修复
- 统一当前运行面到 `~/.rpi/agent` 与 `rpi`,并保留 TypeScript、crate/schema、项目 `.pi/` 和历史材料。

### 验证
- 精确 Rust 测试、fmt、all-target check、严格 clippy、JSON 解析和分类静态扫描均通过。
