## [2026-06-30 15:35:05] [Session ID: omx-1782803182165-j1czn4] 后续计划: 处理 ultragoal 历史 G002 与 Phase 1+ 方向

### 背景
- 当前 `omx ultragoal status` 为 3/4 complete, 1 failed, 1 steeringBlocked。
- G004 replacement baseline 已完成并 checkpoint。
- G002 是历史 failed + steeringBlocked, 其原始 objective 要求 2B/e2B 模型, 当前目录缺失。
- `complete-goals` 没有 pending handoff, 但 aggregateComplete/artifactComplete 仍为 false。

### 建议后续动作
1. 如果要彻底关闭当前 ultragoal active mode, 需要使用 OMX 官方 cleanup / reconciliation 路径, 不要手改 `.omx/ultragoal/goals.json`。
2. 如果恢复了 `Qwen3.5-2B-OptiQ-4bit` 和 `gemma-4-e2b-it-qat-OptiQ-4bit` 模型目录, 可以再用 `complete-goals --retry-failed` 或新增 G005 严格复跑原始 2B/e2B baseline。
3. 如果不恢复旧模型, 建议开新 goal / 新 OpenSpec, 主题改为 Phase 1+ 高层 rdog GUI/MCP tool 形态, 不再继续要求原始 2B/e2B baseline。
4. 如果继续 benchmark, 先用修复后的 `docs/discuss/rdog-rpc-bench.py`, 并优先缩短 Pi system prompt / profile 注入, 否则本地模型每次 27K prompt 预处理成本过高。
