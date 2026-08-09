## [2026-06-30 15:35:05] [Session ID: omx-1782803182165-j1czn4] 任务名称: 继续 goal / 恢复 OMX ultragoal GUI baseline

### 任务内容
- 响应用户 "继续 goal"。
- 恢复 Codex goal / OMX ultragoal 状态。
- 解除旧 G002 macOS 权限阻塞的真实性检查。
- 新增并执行 G004 Phase 0.5 GUI baseline follow-up。
- 修复 `docs/discuss/rdog-rpc-bench.py` 对当前 Pi RPC event 的解析。
- 写入 `docs/discuss/phase0.5-gui-baseline-20260630.md`。

### 完成过程
- `get_goal` 初始返回 `null`, 说明 Codex goal 工具没有活跃 goal。
- `omx state list-active --json` 显示 `active_modes=["ultragoal"]`。
- `omx ultragoal status --json` 显示旧计划为 G001 complete, G003 complete, G002 failed + steeringBlocked。
- 验证 rdog daemon 已运行, `rdog control @ping @capabilities#1` 返回 `@response "pong"`, Accessibility / Screen Recording 均为 available。
- `rdog control @observe` 返回 AX observation, `permission_status="granted"`, 证明旧 macOS 授权阻塞已经解除。
- 使用 `omx ultragoal steer --kind add_subgoal` 新增 G004。
- 按 handoff 创建 Codex aggregate goal。
- 发现原始 2B/e2B 模型目录缺失, 改为记录 replacement baseline, 不伪装成原始 baseline。
- 启动 fast-infer 18081 server 跑 Qwen3.5-4B replacement, 300 秒 timeout, 13 turns, 0 tool, 0 skill read, 0 rdog bash。
- 重启 18081 为 Gemma4 E4B, 跑 replacement, 300 秒 timeout, 2 turns; 后处理 228 个 RPC event 后恢复到拒绝文本, 0 tool, 0 skill read, 0 rdog bash。
- 最终 rdog observe 显示 Chrome 窗口里没有 xiaohongshu / 小红书页面。
- 修复 benchmark 脚本解析 `message_update.assistantMessageEvent.text_delta/text_end/toolcall_end`。
- `python3 -m py_compile docs/discuss/rdog-rpc-bench.py` 通过。
- `git diff --check` 通过。
- G004 checkpoint complete, 证据中明确标注 strict caveat: 原模型缺失, 本轮是 replacement baseline。

### 当前状态
- `omx ultragoal complete-goals --json` 没有 handoff, 因为 pending=0。
- ultragoal summary: total=4, complete=3, failed=1, steeringBlocked=1。
- Codex aggregate goal 仍为 active, 因为旧 G002 failed/steeringBlocked 让 artifactComplete=false。
- 当前不调用 `update_goal complete`, 因为 aggregate 并未达到官方 clean final gate。

### 总结感悟
- 旧阻塞 "macOS 权限未授权" 已被动态证据推翻。
- 新事实是弱本地模型仍然不会主动选择 rdog-control skill/tool 路径。
- 当前更值得推进的是高层 GUI/MCP tool 形态, 让模型面对 3-5 个语义动作, 而不是依赖模型主动读长 skill 文档。
- Benchmark 脚本必须跟 Pi RPC event schema 同步, 否则会把真实 assistant text 误报为空。
