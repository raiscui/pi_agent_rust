## [2026-06-03 15:16:00] [Session ID: current-codex-20260603-minicpm5-prompt-test] 笔记: MiniCPM5 专用短 system prompt 对照测试

## 现象

- 默认 Pi prompt 在真实 `pi -p --mode json --tools write` 路径下有时能执行 `write`, 但不稳定。
- 专用短 system prompt 原本假设可以减少默认 prompt 干扰, 让 MiniCPM5 更专注工具调用。

## 验证命令形态

- 默认组:
  - `pi -p --mode json --no-session --request-timeout 300 --tools write "<中文写盘指令>"`
- 短 prompt 组:
  - `pi -p --mode json --no-session --request-timeout 300 --tools write --system-prompt minicpm5_tool_system_prompt.md "<中文写盘指令>"`
- 服务端:
  - `fast-infer/.venv/bin/python3 mlx_lm_minicpm5_server.py --model ./models/MiniCPM5-1B --host 127.0.0.1 --port 18081 --temp 0.7 --top-p 0.95 --max-tokens 131072 --chat-template-args '{"force_thinking": false}'`

## 动态证据

- 证据目录:
  - `/tmp/pi_minicpm5_prompt_test_20260603_145327`
- 默认组 5 次:
  - `content_ok=2/5`
  - `file_exists=2/5`
  - `tool_results=2/5`
  - `assistant_tool_calls=2/5`
  - `length_stop=2/5`
- 短 prompt 组 3 次:
  - `content_ok=0/3`
  - `file_exists=0/3`
  - `tool_results=0/3`
  - `assistant_tool_calls=0/3`
  - `length_stop=2/3`

## 失败形态

- 默认组失败样例:
  - 模型输出 `The tool has been executed successfully... TOOL_WRITE_DONE`, 但没有 `toolResult`, 文件未创建。
  - 另一次输出约 71MB 重复文本, `stopReason=length`, 没有工具调用。
- 短 prompt 组失败样例:
  - 输出约 70MB / 71MB / 31MB 的重复文本。
  - 内容重复 `Minicrm expects a path...`, `that the tool returned...`, `(parent) or...` 之类片段。
  - 没有 `tool_execution_start`, 没有 `toolResult`, 没有落盘文件。

## 结论

- “只给 Pi 传 MiniCPM5 专用短 system prompt”没有改善真实写盘, 当前证据反而显示它更容易退化成长文本重复。
- 这不是 Pi 解析遗漏已存在 `delta.tool_calls` 的证据。失败样本里 Pi 的 agent_end 消息没有 tool call 内容, 因此 agent 无法执行工具。
- 下一步如果继续优化, 更应该测试:
  - 服务端降低 `max_tokens`, 避免失败时输出几十 MB。
  - MLX shim 在 parser 失败或 `finish_reason=tool_calls` 但空 tool body 时返回显式错误。
  - 通过 OpenAI `tool_choice` 或模型模板层强制工具选择, 而不是只改 Pi system prompt。
