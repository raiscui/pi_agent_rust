# 任务计划: MiniCPM5 专用 system prompt 写盘测试

## [2026-06-03 14:51:26] [Session ID: current-codex-20260603-minicpm5-prompt-test] [新任务]: 对照测试默认 prompt 与 MiniCPM5 专用短 prompt

### 目标

确认在不修改 Pi Rust 代码的前提下, 通过 `--system-prompt` 收缩本地 MiniCPM5 的 system prompt, 是否能提升真实 Pi `write` 工具写盘成功率。

### 阶段

- [x] 阶段1: 确认 Pi 全局配置与 `18081` 端口状态。
- [x] 阶段2: 创建 MiniCPM5 专用短 system prompt。
- [x] 阶段3: 启动临时 MiniCPM5 OpenAI-compatible server。
- [x] 阶段4: 跑默认 prompt 与短 prompt 写盘对照。
- [x] 阶段5: 汇总成功率和失败形态。

### 当前事实

- `~/.pi/agent/models.json` 已配置 `local-minicpm5`, `baseUrl=http://127.0.0.1:18081/v1`, `supportsTools=true`。
- `~/.pi/agent/settings.json` 默认 provider/model 已指向本地 MiniCPM5。
- 当前 `18081` 没有监听服务, 需要为测试启动临时 server。

### 状态

**当前已完成** - 默认 prompt 5 次中 2 次真实写盘成功; MiniCPM5 专用短 prompt 3 次中 0 次写盘成功, 且全部没有 tool call / tool result。单纯 `--system-prompt` 收缩没有改善, 反而更容易长文本重复退化。

## [2026-06-03 15:16:00] [Session ID: current-codex-20260603-minicpm5-prompt-test] [完成记录]: 对照测试完成

### 结果摘要

- 默认 Pi system prompt:
  - `content_ok=2/5`
  - `tool_results=2/5`
  - `length_stop=2/5`
  - 失败形态包括“口头声称工具已执行但无 tool call”和长文本重复。
- MiniCPM5 专用短 system prompt:
  - `content_ok=0/3`
  - `tool_results=0/3`
  - `assistant_tool_calls=0/3`
  - 3 次都没有真实工具调用, 其中 2 次 `stopReason=length`, 输出文件分别约 70MB / 71MB / 31MB。

### 当前结论

- 候选假设“只用 `--system-prompt` 收缩 Pi prompt 就能明显改善 MiniCPM5 tool call”已被动态证据推翻。
- 当前更像是 MiniCPM5-1B 本身在 Pi 真实工具场景下工具遵循能力不足, 或 MLX server 需要更强的 tool_choice / parser-failure 可观测控制, 而不是 Pi Rust 的 OpenAI tool_calls 累积逻辑漏解析。
