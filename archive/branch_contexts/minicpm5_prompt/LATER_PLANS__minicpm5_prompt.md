## [2026-06-03 19:18:00] [Session ID: omx-1780470665249-tkxhle] 后续计划: MiniCPM5 tool-use 长稳验证

### 建议

- 如果后续要把 MiniCPM5 作为默认日常 tool-use 模型, 建议把 loose 回归扩展到 10-20 次, 并覆盖 `edit`、`read -> write`、多轮修正等场景。
- Cargo 仍提示依赖 `proc-macro-error2` future-incompat note, 当前不是本次代码错误; 后续依赖维护时可以单独处理。

## [2026-06-04 00:17:00] [Session ID: omx-1780470665249-tkxhle] 后续计划: MiniCPM5 tool-use 长稳和多工具矩阵

### 已覆盖

- 10 次 loose 写入样本。
- 3 次非 `write` read 样本。
- path repair 单测覆盖 `write` 和 `read`, 以及非本地 provider / 多候选不修。

### 建议后续继续覆盖

- `edit` 工具: 先 read 再 edit 的多轮路径继承。
- `grep` / `find` / `ls`: 当前目录可选 path、省略 path 与显式目录 path。
- 多候选路径场景: 确认修复层保持保守, 不自动猜测。
- 低温和高温对比: 当前 server `temp=0.7`, 可后续比较 `temp=0.0/0.2` 的原始模型错参率。
