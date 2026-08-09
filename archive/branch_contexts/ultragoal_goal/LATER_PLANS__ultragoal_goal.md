## [2026-06-30 16:24:00] [Session ID: omx-1782803182165-j1czn4] 后续计划: Phase 1+ 高层 GUI / MCP tool 研究

### 背景
- Replacement baseline 表明 Qwen3.5-4B / Gemma4 E4B 在当前 Pi prompt + skill/profile 下都没有稳定进入 rdog skill/tool 路径。
- 原始 Qwen3.5-2B / Gemma4 E2B 模型目录当前缺失, 本轮不能声称严格复现原计划。

### 建议
- 后续新开计划时, 目标应从减少 rdog-control skill 轮数, 调整为让 GUI 控制以 3-5 个高层语义工具暴露。
- 候选工具形态: open_browser, observe_gui, find_web_text, click_web_text, wait_for_page_state。
- 如果恢复原始 2B/e2B 模型目录, 可以单独复跑 strict baseline, 但不要覆盖本轮 replacement baseline 的结论边界。

