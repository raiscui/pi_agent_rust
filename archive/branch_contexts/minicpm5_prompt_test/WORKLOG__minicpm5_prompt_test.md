## [2026-06-03 15:16:00] [Session ID: current-codex-20260603-minicpm5-prompt-test] 任务名称: MiniCPM5 专用 system prompt 写盘对照测试

### 任务内容

- 按用户要求继续执行测试。
- 不修改 Pi Rust 代码, 只通过 `--system-prompt` 验证 MiniCPM5 专用短 prompt 是否能改善真实 Pi `write` 工具调用。

### 完成过程

- 确认 `~/.pi/agent/models.json` 已将 `local-minicpm5` 指向 `http://127.0.0.1:18081/v1`, 且 `supportsTools=true`。
- 创建 `minicpm5_tool_system_prompt.md` 作为测试 prompt。
- 启动临时 `mlx_lm_minicpm5_server.py` 并通过 `/v1/models` 健康检查。
- 执行默认 prompt 5 次, 短 prompt 3 次。
- 测试进程中断后, 从 `/tmp/pi_minicpm5_prompt_test_20260603_145327` 恢复 stdout 和真实目标文件结果。

### 验证证据

- 默认 prompt:
  - 2/5 真实写盘成功。
  - 2/5 产生 `toolResult`。
  - 3/5 没有真实写盘。
- MiniCPM5 专用短 prompt:
  - 0/3 真实写盘成功。
  - 0/3 产生 `toolResult`。
  - 3/3 没有 assistant tool call。

### 总结感悟

- 单纯收缩 Pi system prompt 不是可靠修复方向。
- 失败的关键不在 Pi 中间层漏解析已有 tool call, 而在模型/服务端没有给 Pi 一个可执行的 tool call 内容。
- 后续更值得验证服务端约束: 降低 `max_tokens`, 增加 parser 失败可观测错误, 或支持 `tool_choice` / 模板层强制工具选择。
