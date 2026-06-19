## [2026-06-03 19:18:00] [Session ID: omx-1780470665249-tkxhle] 任务名称: Pi 本地 MiniCPM5 provider-local tool-use append prompt

### 任务内容

- 给本地 `local-minicpm5` 模型追加更短、更硬的 tool-use system prompt。
- 约束 `write.path` 必须是相对路径, 禁止 `/Users/...` 绝对路径。
- 禁止口头声称已经调用工具; 写文件必须发真实 `write` tool call。
- 避免重复调用同一个 `write`。

### 完成过程

- 读取 `src/app.rs::build_system_prompt`、`src/main.rs`、`src/sdk.rs`、`src/acp.rs` 的 system prompt 构建链路。
- 在 `src/app.rs` 增加 provider-local helper。
- 在 CLI/RPC 初始 prompt、扩展资源重建 prompt、SDK session prompt、ACP prompt 中接入 helper。
- 添加 4 个聚焦单测。
- 处理 clippy 暴露的当前全仓 lint gate 问题, 让 `cargo clippy --all-targets -- -D warnings` 通过。
- 启动 fast-infer MiniCPM5 server, 用 `pi_minicpm5_tool_regression.py --prompt-style loose --trials 3` 做真实回归。

### 验证证据

- `cargo fmt --check`: 通过。
- `cargo test --package pi_agent_rust --lib -- app::tests::append_provider_local_system_prompt_* --exact --nocapture`: 4 个单测通过。
- `cargo check --all-targets`: 通过。
- `cargo clippy --all-targets -- -D warnings`: 通过。
- `cargo build --bin pi`: 通过。
- 真实 loose 回归证据目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-regression-jopl0lmv`。
- 第二轮真实 loose 回归结果: `tool_success=3/3`。

### 总结感悟

- 这个问题的动态证据显示根因边界在模型参数生成不稳定, 不是 Pi 漏执行工具。
- 对 MiniCPM5-1B 这种小模型, 单纯说“相对路径”不够; 必须明确禁止 prepend CWD 和具体绝对路径前缀。
- provider-local append prompt 比替换全局 system prompt 更稳, 也不会污染其它模型。

## [2026-06-04 00:17:00] [Session ID: omx-1780470665249-tkxhle] 任务名称: MiniCPM5 通用 tool-use path 约束与修复层

### 任务内容

- 将本地 MiniCPM5 的 tool-use 约束从 `write` 个例升级为通用工具路径契约。
- 在 OpenAI provider 中为 `local-minicpm5` 增加 provider-local tool schema path 描述规范化。
- 在 Agent 工具执行前增加保守的 `local-minicpm5` path 参数修复层。
- 用写入样本和非 `write` 的 read 样本做真实回归。

### 完成过程

- 多轮验证 prompt-only 方案, 记录 `path = ."`、`path = .`、绝对路径漂移等失败形态。
- 通过直接 OpenAI-compatible 非 `write` 探针验证 XML parser 并非普遍转坏 path。
- 将 OpenAI tools schema 对 `local-minicpm5` 做 provider-local 改写, 且按文件工具 / 搜索列表工具 / 未知工具分类。
- 在 `execute_tool_calls` 发出 ToolExecutionStart 前修复明显错误 path, 保证事件和执行使用同一份参数。
- 修复层只在 `local-minicpm5` + `minicpm5` + 最近用户文本唯一相对路径候选时生效。

### 验证证据

- `cargo fmt --check`: 通过。
- path repair 聚焦单测 4 个: 通过。
- app/provider 聚焦单测: 通过。
- `cargo check --all-targets`: 通过。
- `cargo clippy --all-targets -- -D warnings`: 通过。
- `cargo build --bin pi`: 通过。
- loose 写入样本: `tool_success=10/10`, 证据目录 `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-regression-86wrdggb`。
- 非 `write` read 样本: `tool_success=3/3`, 证据目录 `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-read-regression-kbgl0q7m`。

### 总结感悟

- MiniCPM5-1B 的 tool-use 稳定性不能只靠 prompt; 在 agent 产品里需要 provider-local 的结构化防护。
- `write` 只是本次测试样本之一, 最终落地的是泛化的 `path` 参数修复和 schema 约束。

## [2026-06-04 10:32:00] [Session ID: omx-1780470665249-tkxhle] 任务名称: 回答 local-minicpm5 path schema 与 read agent_end 续问

### 任务内容

- 复核为什么只对 `local-minicpm5` 改写 OpenAI tools schema 里的 `path.description`。
- 复核非 `write` 的 `read` 样本中 2 次没有最终 `agent_end` 的真实停点。

### 完成过程

- 回读 `task_plan__minicpm5_prompt.md` 与 `notes__minicpm5_prompt.md` 中上一轮动态验证记录。
- 核对 `src/tools.rs` 原始 schema、`src/providers/openai.rs` provider-local conversion、`src/app.rs` provider-local prompt、`src/agent.rs` conservative path repair。
- 解析 read 回归目录下 3 个 `pi-rpc-stdout.jsonl`, 确认 3 次 `read` 工具执行均成功, 2 次卡在 post-tool assistant 文本生成。

### 总结感悟

- `path` 问题要按“模型生成行为与 schema 文案冲突”解释, 不能说成 Pi 字段坏了。
- `agent_end` 缺失要和工具执行成功分开看; 当前证据支持 post-tool 文本生成未收束, 不支持 read 工具或 XML parser 失败。
