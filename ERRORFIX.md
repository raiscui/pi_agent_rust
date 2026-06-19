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
