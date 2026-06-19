## [2026-06-03 19:18:00] [Session ID: omx-1780470665249-tkxhle] 问题: 本地 MiniCPM5 loose write 会把 path 漂移到绝对路径

### 现象

- 普通 loose 写盘会真实触发 Pi `write` tool call。
- 但 MiniCPM5 常把 `write.path` 生成成 `/Users/cuiluming/...` 或 `/private/var/...`。
- Pi 正确拒绝这些路径: `Cannot write outside the working directory`。

### 原因

- 不是 Pi 漏解析 tool call, 也不是 MiniCPM5 XML parser 失败。
- 已观察到真实 `tool_execution_start` 事件, 但参数不满足 Pi 写盘安全约束。
- 模型会受到 prompt 中 `Current working directory` 绝对路径影响, 倾向把 CWD 拼进 `write.path`。

### 修复

- 在 `src/app.rs` 增加 provider-local append prompt helper。
- 仅当 provider 为 `local-minicpm5`、model id/name 包含 `minicpm5`、且 `write` 工具启用时追加。
- 规则明确要求:
  - 写文件必须发真实 `write` tool call。
  - `write.path` 必须是用户请求的相对路径。
  - 禁止 prepend CWD。
  - 禁止 `/Users/...` 和 `/private/...`。
  - 同一 requested file/content 不重复调用 `write`。
- CLI/RPC、扩展资源重建、SDK、ACP 都复用同一个 helper。

### 验证

- 4 个聚焦单测覆盖 append、provider 门控、write 工具门控、幂等。
- `cargo fmt --check`: 通过。
- `cargo check --all-targets`: 通过。
- `cargo clippy --all-targets -- -D warnings`: 通过。
- 第二轮真实 loose 回归: `tool_success=3/3`, 三次 `write.path` 都是相对路径。

## [2026-06-04 00:17:00] [Session ID: omx-1780470665249-tkxhle] 问题: MiniCPM5 普通 tool-use 会生成退化或越界 path 参数

### 现象

- 普通 loose 自然语言请求下, MiniCPM5 会真实发 tool call。
- 但 `path` 可能变成 `."`、`.` 或 `/Users/ciluming/.pi/...` 这类错误值。
- `write` 样本只是用于观察这一类 path 参数问题, 不是唯一修复对象。

### 原因

- 已验证不是 Pi 完全漏执行工具: 多轮都有 `tool_execution_start`。
- 直接 OpenAI-compatible 非 `write` 探针能正确返回相对路径, 所以不支持“XML parser 普遍转坏 path”。
- 更准确的判断是: MiniCPM5-1B 在 Pi 完整上下文 + loose 中文提示中, 对 `path` 参数抽取不稳定; prompt/schema 可改善但不能完全稳定。

### 修复

- `src/app.rs`: provider-local MiniCPM5 tool-use prompt, 明确文件工具和搜索/列表工具的 path 契约。
- `src/providers/openai.rs`: 仅对 `local-minicpm5` 改写 OpenAI tools schema 中的 `path` 描述, 且按工具语义分类。
- `src/agent.rs`: 在工具执行前做保守 provider-local path repair:
  - 只对 `local-minicpm5` + `minicpm5` 生效。
  - 用户文本中必须有唯一明确相对路径候选。
  - 只修复明显错误的 `path`, 如绝对路径、多余引号、文件工具的 `.`。
  - 多候选或非本地 provider 不修。

### 验证

- Rust 质量门全部通过。
- loose 写入样本 10/10 成功。
- 非 `write` read 样本 3/3 工具执行成功。
