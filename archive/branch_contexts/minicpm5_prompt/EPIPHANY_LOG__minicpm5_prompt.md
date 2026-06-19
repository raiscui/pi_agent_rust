
## [2026-06-04 00:17:00] [Session ID: omx-1780470665249-tkxhle] 主题: 小模型 tool-use 不能只依赖 prompt 约束

### 发现来源

- 本地 MiniCPM5-1B loose tool-call 回归。

### 核心问题

- MiniCPM5-1B 能发真实 OpenAI tool_calls, 但在完整 agent 上下文中会不稳定生成错误 `path` 参数。
- prompt/schema 多轮加固只能改善概率, 无法在当前 10 次 loose 回归里稳定到 10/10。

### 为什么重要

- 如果只看“是否发了 tool call”, 会误判模型可用。
- 对 coding agent 来说, 工具参数正确性和工具执行安全边界同样是一等需求。

### 未来风险

- 其它工具参数也可能出现类似“模型会调用, 但参数错位”的问题。
- 若没有 provider-local 修复/拦截, 小模型可能在真实任务中产生假完成、错误路径或重复失败解释。

### 当前结论

- 对 MiniCPM5 这类本地小模型, 应组合使用 prompt、schema、运行期保守修复/拦截。
- 修复必须 provider-local, 且要有安全边界, 不能全局改变高能力模型的工具行为。

### 后续讨论入口

- 继续扩展多工具矩阵时, 优先检查 `edit`、`grep`、`find`、`ls` 的参数稳定性。
