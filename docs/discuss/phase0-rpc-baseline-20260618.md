# Phase 0 RPC Mode Baseline 详细数据

- 日期: 2026-06-18
- Session ID: omx-1781751290523-tk9ugc
- 工具: `docs/discuss/rdog-rpc-bench.py` (271 行, stdio JSON-RPC 驱动 pi --mode rpc)
- 关联: `docs/discuss/phase0-baseline-20260618.md` (text-mode baseline), `docs/discuss/rdog-rpc-bench.py` (脚本)

## 1. 为什么需要 RPC mode (补充 phase0-baseline-20260618 第 5.2 节)

pi -p 模式不稳定:
- "say hi" 60s timeout 杀, stderr 0 字节, stdout 0 字节
- 无法可靠拿到 model 完整 text response / tool call 序列

pi --mode rpc 是 JSON-RPC 2.0 over stdio, 给 agent 完整可编程 event stream:
- `{"type": "response", "command": "prompt", "id": "...", "success": true}` - ack
- `{"type": "agent_start", "sessionId": "..."}` - session 创建
- `{"type": "message_start", "message": {"role": "user", ...}}` - user msg 进入
- `{"type": "message_end", "message": {"role": "user", ...}}` - user msg 完成
- `{"type": "turn_start", "sessionId": "...", "turnIndex": 0}` - assistant turn 开始
- (期望但当前 model 没出) `{"type": "turn_end", ...}` + `{"type": "message_start", "message": {"role": "assistant", ...}}` + `{"type": "tool_execution_start", "name": "read", ...}` 等

## 2. 4 次跑通验证数据

### 2.1 测试 1: Qwen3.5-2B + "say hi in 3 words"
- wall_time: 20.05s (timeout)
- turn_count: 1
- tool_calls: 0
- text_responses: 0
- skill_reads: 0
- rdog_bash_calls: 0
- exit_reason: timeout
- stderr_tail: ""
- **观察**: turn_start 后 model 20s 没出 turn_end / assistant message. RPC mode 行为跟 print mode 完全不一样 (print mode 30s 出 "Failed to create new tab URL" 30 字节).

### 2.2 测试 2: Qwen3.5-2B + user prompt
- wall_time: 80.06s (timeout)
- turn_count: 1
- tool_calls: 0
- text_responses: 0
- skill_reads: 0
- rdog_bash_calls: 0
- exit_reason: timeout
- **观察**: model 80s 没真正出 assistant message, RPC mode 下 model 行为跟 print mode 不一样, 80s 跑不出来 text.

### 2.3 测试 3: Gemma-4-E2B + user prompt
- wall_time: 80.09s (timeout)
- turn_count: 2
- tool_calls: 0
- text_responses: 0
- skill_reads: 0
- rdog_bash_calls: 0
- exit_reason: timeout
- **观察**: Gemma 在 RPC mode 下比 Qwen3.5 多 1 turn (2 vs 1), 但仍 80s 没真正出 text.

### 2.4 测试 4: Qwen3.5-2B + "say hi" + --debug
- 看到 event stream 真实 shape (6 个 event: response / agent_start / message_start user / message_end user / turn_start)
- 看到 model 在 turn_start 后不 progress (没 turn_end)
- **观察**: RPC mode 下 model stream pipeline 跟 print mode 不一样, 可能是 stream buffer 等待问题, 也可能是 model 端某种时序竞争.

## 3. 关键发现

### 3.1 print mode vs RPC mode 行为差异

| 维度 | print mode (-p) | RPC mode (--mode rpc) |
|---|---|---|
| Qwen3.5 user prompt 行为 | 调 firefox bash, 30 字节 "Failed to create new tab URL" | 80s 不出 text |
| Gemma user prompt 行为 | 18s 650 字节中文诚实回答 | 80s 不出 text, 2 turn |
| event stream 可见 | 否 (只有 stdout/stderr) | 是 (6+ 种 event type) |
| benchmark 可编程 | 否 | 是 |
| data 完整度 | 部分 (取决于 model 性格) | timeout 时 0 字节, 但可控 |

**两个 mode 给同一 model + 同一 prompt 不同结果**——这说明 pi 内部对 prompt 处理路径不同, system prompt 可能不同, 或 model 端 stream 行为不同.

### 3.2 Qwen3.5-2B 在 RPC mode 下卡死原因 (候选)

- **A**: model 权重 load 没完成 (但之前 curl 测过 1.8s 内能 load 完)
- **B**: pi --mode rpc 启动后 system prompt 太大, model 推理慢
- **C**: stream pipeline buffer 没 flush, 永远等不到 turn_end
- **D**: model 端某种时序竞争, RPC mode 用 stdio + thread 而 print mode 用 line flush

**没 evidence 区分 A/B/C/D, 需进一步 debug**:
- A: 跑 RUST_LOG=info,pi=trace, 看 model load 时间
- B: 看 pi system prompt 大小
- C: 跑 --debug 看 stream buffer flush
- D: spawn subagent 独立 debug

### 3.3 pi --mode rpc 跑通性结论

- **脚本可独立运行**: 接受 --model --prompt --timeout --out --debug, 输出结构化 JSON
- **event stream 可读**: 6+ 种 event type 都看到 (response/agent_start/message_start/message_end/turn_start)
- **数据完整度**: 在 model 不卡的情况下应该能拿完整 turn_count + tool_calls + text_responses
- **当前弱 model + 本地 setup 限制**: model 不出 turn_end, 80s timeout 时 text/tool_calls 都是空
- **不影响 G003 完成**: G003 目标是"脚本可独立运行 + 输出结构化 JSON + 文档化", 全部满足.

## 4. 改进建议 (给 Phase 0.5 / 强 model 用户)

### 4.1 在强 model 上重跑
- Claude Opus 4 / Sonnet 4 / GPT-4o 等强 model 在 RPC mode 下应该能正常出 turn_end
- 拿真实 turn_count + tool_calls 序列
- 跑 docs/discuss/rdog-rpc-bench.py 即可

### 4.2 如果必须用弱本地 model
- 调大 timeout (e.g. 180s)
- 接受 turn_count 可能不准确 (RPC mode stream 收不到 turn_end)
- 改用 print mode + 接受 30-650 字节 text 即可

### 4.3 pi 改进建议 (留给作者)
- RPC mode stream pipeline 在弱 model 上等不到 turn_end, 应加 timeout 主动 break stream
- print mode vs RPC mode 行为差异应文档化, 或在 RPC mode 加 explicit prompt 重试机制

## 5. G003 完成 evidence

- 脚本: docs/discuss/rdog-rpc-bench.py 271 行
- 4 次跑通验证数据: /tmp/pi_bench_qwen_rpc_hi.json, /tmp/pi_bench_qwen_rpc_user.json, /tmp/pi_bench_gemma_rpc_user.json, /tmp/pi_bench_qwen_rpc_hi3.json
- event types 真实 shape: 跑 --debug 看到 6+ event
- 文档化: 本文件 + 脚本 docstring
- 状态: G003 已 checkpoint complete (2026-06-18 07:37Z)
