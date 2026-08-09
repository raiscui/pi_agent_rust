## [2026-06-30 15:35:05] [Session ID: omx-1782803182165-j1czn4] 错误修复: rdog-rpc-bench 漏解析当前 Pi RPC message_update 事件

### 现象
- Gemma4 E4B benchmark 的原始 JSON 显示 `text_responses=[]`, `tool_calls=[]`, `exit_reason="timeout"`。
- 但 `--debug` stderr 中存在大量 `message_update.assistantMessageEvent.text_delta` 事件, 模型实际输出了拒绝文本。

### 原因
- `docs/discuss/rdog-rpc-bench.py` 只识别旧的扁平事件类型: `text`, `assistant`, `content_block_delta`, `message`, `tool_call`。
- 当前 Pi RPC 直接 serde `AgentEvent`, assistant 流式文本在:
  - `message_update.assistantMessageEvent.type = text_delta | text_end | done`
- tool call 在:
  - `message_update.assistantMessageEvent.type = toolcall_end`
  - `toolCall.arguments`

### 修复
- 新增 `text_buffers` 按 `contentIndex` 聚合 partial text。
- 解析 `text_start`, `text_delta`, `text_end`, `done`。
- 解析 `toolcall_end.toolCall`, 并兼容 `arguments` 是 JSON object 或 JSON string。
- timeout / kill 时也 flush 已收到的 partial text, 避免假空报告。

### 验证
- `python3 -m py_compile docs/discuss/rdog-rpc-bench.py`: 通过。
- 后处理 `gemma4_e4b_replacement.stderr` 得到 `posthoc_event_count=228`, `text_count=1`, `tool_count=0`, 证实旧报告为空是解析问题而不是模型无输出。
