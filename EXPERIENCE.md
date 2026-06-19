# EXPERIENCE.md

项目级经验沉淀。这里记录已经在本仓库验证过、未来容易再次踩坑的工作方式和判断口径。

## TUI 终端鼠标捕获与退出恢复

- 默认不要启用 all-motion mouse capture。`crossterm::event::EnableMouseCapture` 会启用 SGR mouse mode 和 all-motion tracking,终端会把普通鼠标移动转成 `ESC [ < 35 ; x ; y M` 一类输入字节。
- Pi 的交互 TUI 默认需要鼠标滚轮支持。正确策略不是关闭全部 mouse capture,而是由 Pi 自己开启精确序列 `?1000h` + `?1006h`,保留滚轮/按钮 SGR 报告,但默认不写 `?1003h`。
- `disable_mouse_capture: true` / `--no-mouse-capture` / `PI_NO_MOUSE_CAPTURE=1` 是用户遇到复制粘贴或终端兼容问题时的逃生路径,必须能完全关闭 Pi 自己的鼠标捕获。
- 如果路径确实启用了 mouse capture,退出恢复需要尽早回到 raw mode,写 disable mouse / disable paste / show cursor / leave alt screen,再用 quiet-window drain 消费延迟到达的 terminal events,最后才把终端交还给 shell。
- 仅验证“disable 序列存在”不够。必须用 PTY 捕获原始字节,至少确认默认路径有 `?1000h` / `?1006h`,没有 `?1003h`,并确认 `Goodbye!` 后没有继续由 Pi 默认策略制造鼠标报告。
- 向 Markdown 上下文文件写入包含反引号的内容时,必须使用单引号 heredoc。否则 shell 会把反引号里的内容当命令执行,可能误启动 `pi` 或污染计划文件。

## Profile 字段的两层语义：OpenAI schema + ToolRegistry

- `~/.pi/agent/models.json` 的 `toolUseProfile.tools` 字段如果只过滤 OpenAI request 的 `tools` 数组（schema 层），不算"profile 真正生效"。
- 必须同时改 `src/main.rs` 路径上的 `ToolRegistry` 实际注册（registry 层），让 model 即使想 emit schema 外的 `tool_call`，Pi 客户端也找不到该 tool。
- 判断方法: profile.tools 改完后，跑 `pi --tools <A,B,C> --print` 配 profile.tools=[A,B]，如果 model 仍能 emit `toolCall name='X'`，说明 registry 层没过滤，是软限制。
- 验证证据: `__rdog_bash_profile` 阶段 6 + M 方向修复（`src/main.rs` line 1394 后插入 14 行 profile.tools 硬过滤逻辑）+ 3 次 write smoke `0/3` 出现 write toolCall + read 工具 smoke 通过。

## 改完代码不重 build 装是隐形 bug

- `src/**/*.rs` 改动后,用户/agent 看到的仍是 `~/.cargo/bin/pi` 旧 binary 的行为,除非 `cargo install --path . --force` 装新 binary。
- 之前所有 smoke (reg_0..4, reg_*, f_*) 数据可能因旧 binary 无效，因为 profile filter 代码根本没编译进去。
- 每次 source 改动后必须 `cargo install --path . --force`，并用 `which pi` + 验证 `~/.cargo/bin/pi` 的 mtime 确认。
- 推荐做法: 改完 source 立刻 `cargo install --path . --force`，然后再跑 smoke; 避免"代码看起来对了但行为没变" 的循环。

## 小模型 tool-use 不能只依赖 prompt 约束

- MiniCPM5-1B / gemma-2B 这类本地弱模型,即使配了"必须发真实 tool call / 不许口头声称 / 路径用相对路径"等 provider-local append prompt,仍可能在完整 agent 上下文中生成错误参数、重复成功调用、长文本退化。
- 修复必须组合: prompt append + OpenAI tools schema 改写 + 运行期保守拦截（path repair / 重复成功工具转最终文本）。单层修复不够。
- 修复必须 provider-local,不能全局影响其它高能力模型。`append_provider_local_system_prompt_*` helper 模式可以复用。
- path repair 边界: 多候选不修 / 非本地 provider 不修 / 只修明显错误（绝对路径、多余引号、文件工具的 `.`）。保守 > 智能。
- 重复成功工具调用保护: 在 run_loop 中检测"同一成功工具连续 N 次被调用",转 provider-local 最终 assistant 文本,避免超过工具轮次。
- 判断小模型"是否可用" 不能只看"是否发了 tool call",工具参数正确性、工具执行安全边界是一等需求。

## loose 回归 vs focused 修复不能混算

- loose: 自然语言弱约束,统计 `no_tool_call` / `wrong_tool` / `parse_error` / `tool_error` / `post_tool_runaway` / `repeated_same_tool` / `final_answer_mismatch` 等漂移率。
- focused: 硬约束 prompt + 单工具子集,统计 `tool_success` 率。
- 两者口径严格分开,不能用 loose 66% 漂移率否定 focused 5/5 成功,反之亦然。
- 报告里要明确写"loose 弱约束下"或"focused 硬约束下"前缀,不要混算到"小模型可用性" 这个笼统指标。
- 真实 production 体验更接近 loose,但 regression 验证更接近 focused。两者并存,各自看自己的数据。

## `--system-prompt` 短 prompt 反而更差

- 候选假设: "收缩 Pi 默认 system prompt, 给 MiniCPM5 一个专用短 prompt, 减少 prompt 干扰, 应能改善 tool call 写盘率" → 被动态证据推翻。
- 实测: 默认 prompt 5 次中 2 次写盘成功; MiniCPM5 专用短 prompt 3 次中 0 次写盘成功,反而退化为 70MB/71MB/31MB 重复文本, `stopReason=length`。
- 短 prompt 没有改善 tool call 遵从度,反而让模型在弱上下文下更易走"长文本重复"退化路径。
- 失败不在 Pi 中间层漏解析 `delta.tool_calls`,而在模型/服务端没发出可执行 tool call 内容 (agent_end 消息中没有 tool call)。
- 后续真要修,优先方向: (1) 服务端降低 `max_tokens` 避免失败时输出几十 MB, (2) MLX shim 在 parser 失败 / `finish_reason=tool_calls` 但空 tool body 时返回显式错误, (3) `tool_choice` 或模型模板层强制工具选择,而不是只改 Pi system prompt。
- 教训: 改 system prompt 是"看起来干净"的修复路径,但不一定有效。每次做这种假设要设计可证伪实验,失败就回滚,不要继续在 prompt 上叠层。
