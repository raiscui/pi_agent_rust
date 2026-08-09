## [2026-06-30 15:35:40] [Session ID: omx-1782803182165-j1czn4] 主题: rdog GUI baseline 的关键问题不是 skill 轮数, 而是弱模型不选择 skill/tool 路径

### 发现来源
- 继续 OMX ultragoal G004 Phase 0.5 GUI baseline。
- rdog daemon 与 macOS Accessibility / Screen Recording 已可用。
- Qwen3.5-4B replacement 与 Gemma4 E4B replacement 均未完成 GUI 任务。

### 核心问题
- 原问题假设是: rdog-control skill 可能会让模型走 8-12 轮, 因此要评估是否拆成 MCP 高层工具。
- 当前动态证据显示: 弱本地模型不是 "走 skill 路径太慢", 而是 **根本没有进入 rdog skill/tool 路径**。
- Gemma4 E4B 选择拒绝 GUI 控制能力, Qwen3.5-4B 在 300 秒内没有形成可用 tool/text 成果。

### 为什么重要
- 如果问题是 "skill 太慢", 优化方向是压缩 skill、减少步骤、改 prompt。
- 如果问题是 "skill 不被选中", 优化方向应转为把 GUI 控制变成更显眼、更低决策成本的高层 tool / MCP API。
- 这会直接影响 Phase 1+ 是否应该做, 以及做成什么形态。

### 未来风险
- 继续把精力放在 prompt 里要求弱模型 read `rdog-control.md`, 可能会不断得到 0 收益。
- 只比较耗时会误导决策, 因为未进入 skill 路径时 "轮数低" 不代表方案可用。

### 当前结论
- Phase 1+ 仍值得推进, 但目标应调整为 "让 GUI 控制成为 3-5 个高层语义工具", 而不是单纯减少 skill 文档 token。
- 后续报告或 plan 需要明确这一 framing shift。

### 后续讨论入口
- `docs/discuss/phase0.5-gui-baseline-20260630.md`
- `docs/discuss/rdog-rpc-bench.py`
- `.omx/ultragoal/goals.json` G004 evidence
