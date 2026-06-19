# 任务计划: Pi 本地 MiniCPM5 provider-local tool-use append prompt

## [2026-06-03 18:19:10] [Session ID: omx-1780470665249-tkxhle] [新任务]: 为本地 MiniCPM5 增加更短更硬的写盘工具约束

### 目标

在 Pi 的本地 MiniCPM5 provider/model 路径上追加一段很短的 tool-use 约束, 只约束真实工具调用行为, 不替换全局 system prompt, 并用单测和真实 loose tool-call 回归验证。

### 阶段

- [x] 阶段1: 读取 Pi system prompt 构建链路, 确定 provider-local 注入点。
- [x] 阶段2: 实现 MiniCPM5 专用 append prompt, 且只在本地 MiniCPM5 + write 工具启用时生效。
- [x] 阶段3: 添加聚焦单测, 覆盖追加/不追加/避免重复追加。
- [x] 阶段4: 跑 Rust 格式化、单测、check/clippy。
- [x] 阶段5: 跑真实 MiniCPM5 loose write 回归, 判断绝对路径漂移是否改善。
- [x] 阶段6: 记录交付结果和后续建议。

### 关键问题

1. 这次不改全局 prompt, 避免影响其它 provider/model。
2. 这次不把 Pi 全局 `supportsTools` 再做其它顺手调整。
3. prompt 必须硬性说明 `write.path` 用相对路径, 禁止 `/Users/...`, 禁止口头声称已调用工具, 写文件必须发真实 tool call, 避免重复同一个 write。

### 当前事实

- 之前 `--system-prompt` 替换测试失败, 说明不能走全局替换 prompt。
- 后续 loose 测试已显示模型会真实调用 `write`, 但 path 漂移到 `/Users/cuiluming/...`, 被 Pi 正确拒绝。
- 因此当前候选假设是: provider-local append prompt 能减少 path 参数漂移, 但必须通过动态回归验证。

### 状态

**当前任务已完成** - provider-local prompt 已落地, Rust 质量门与真实 loose 回归均已通过。

## [2026-06-03 18:30:00] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 进入 Rust 验证阶段

### 已完成

- [x] 读取 `src/app.rs::build_system_prompt`、`src/main.rs` 初始化/扩展重建路径、`src/sdk.rs`、`src/acp.rs`。
- [x] 在 `src/app.rs` 增加 provider-local append helper。
- [x] 在 CLI/RPC、SDK、ACP 三类入口接入同一个 helper。
- [x] 在 `src/app.rs` 内部测试模块添加聚焦单测。

### 下一步

- [x] 运行 `cargo fmt` / 聚焦单测 / `cargo check --all-targets` / `cargo clippy --all-targets -- -D warnings`。
- [ ] 如 Rust 验证通过, 再跑真实 MiniCPM5 loose tool-call 回归。

## [2026-06-03 18:58:00] [Session ID: omx-1780470665249-tkxhle] [状态更新]: Rust 验证通过, 进入真实回归

### 验证结果

- [x] `cargo fmt --check`: 通过。
- [x] 4 个 `append_provider_local_system_prompt_*` 聚焦单测: 通过。
- [x] `cargo check --all-targets`: 通过。
- [x] `cargo clippy --all-targets -- -D warnings`: 通过。

### 期间处理

- clippy 最初暴露了若干非本次 prompt helper 引入的基线 lint, 已做局部风格修复。
- 最终仍有 Cargo future-incompat note 指向依赖 `proc-macro-error2`, 不是本次代码 lint/error。

### 下一步

- [ ] 检查 `fast-infer/pi_minicpm5_tool_regression.py` 参数。
- [ ] 构建可执行的 Pi binary。
- [ ] 确认或启动 `18081` MiniCPM5 server。
- [ ] 跑 loose 回归并记录 `tool_success/tool_error/no_tool_call` 结果。

## [2026-06-03 19:08:00] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 第一轮真实 loose 回归部分失败, 准备收紧 prompt

### 动态证据

- 证据目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-regression-5ugy5vta`
- `tool_success=1`, `tool_error=2`。
- 失败样本仍然使用 `/Users/cuiluming/...` 或 `/private/var/...` 绝对路径。
- 失败样本存在重复 `write` 调用。

### 当前结论

- provider-local append prompt 已接入并能保持真实 tool call 路径运行。
- 但规则还不够硬, 需要明确禁止把 CWD 拼到 `write.path`。

### 下一步

- [ ] 收紧 append prompt 文案。
- [ ] 重跑聚焦单测和真实 loose 回归。

## [2026-06-03 19:18:00] [Session ID: omx-1780470665249-tkxhle] [完成记录]: 第二轮 loose 回归通过

### 完成项

- [x] 收紧 provider-local append prompt。
- [x] 重跑 4 个聚焦单测。
- [x] 重新构建 `target/debug/pi`。
- [x] 第二轮真实 loose 回归 `tool_success=3/3`。
- [x] 停止本轮启动的 MiniCPM5 server, `18081` 已无监听。

### 最终状态

**当前任务已完成** - 实现、验证、工作记录和后续建议均已落地。

## [2026-06-03 21:27:56] [Session ID: omx-1780470665249-tkxhle] [修正任务]: 避免把 MiniCPM5 tool-use prompt 做成 write 个例

### 用户提醒

- `write` 只是当前 loose 回归脚本选中的一个测试工具。
- 主要目标不是让 MiniCPM5-1B 专门使用 `write`。
- provider-local prompt 应该是通用 tool-use 纪律, 不应该过拟合某个工具。

### 新阶段

- [x] 阶段7: 将 prompt 从 `write` 专项规则泛化为通用工具调用规则。
- [x] 阶段8: 调整单测, 覆盖非 `write` 工具也会追加 prompt。
- [ ] 阶段9: 跑 Rust 验证和 10 次 loose 回归。
- [ ] 阶段10: 更新记录并交付结论。

### 状态

**目前在阶段9** - 通用 tool-use prompt 和聚焦单测已完成, 正在运行最终质量门与 10 次 loose 回归。

## [2026-06-03 21:42:00] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 10 次 loose 回归暴露泛化 prompt 过度抽象

### 动态证据

- 证据目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-regression-q4mas9f6`
- `tool_error=10`, `tool_success=0`。
- 10 次均是真实 tool call, 但 path 都漂到绝对路径。

### 结论

- “不做 write 个例”的方向正确。
- 但 `path-like arguments` 对 MiniCPM5 太抽象, 不足以约束参数。

### 下一步

- [ ] 读取 built-in tools 的参数名。
- [ ] 改成通用路径参数枚举式 prompt。
- [ ] 重跑单测和 10 次 loose 回归。

## [2026-06-03 22:16:00] [Session ID: omx-1780470665249-tkxhle] [用户约束]: write 只是回归样本, 不得做成工具特例

### 用户提醒

- `write` 只是当前测试脚本随机选中的一个工具样本。
- 目标是 MiniCPM5-1B 的通用 tool-use 能力, 不是专门优化 `write`。
- 后续 prompt 和验证结论都必须围绕“所有工具参数和真实工具调用纪律”来组织。

### 当前计划调整

- [ ] 重新审视当前 provider-local prompt, 去掉只对 `write` 生效或暗示 `write` 优先的表达。
- [ ] 保留具体路径约束, 但表达为“任何名为 path 的工具参数”。
- [ ] 如继续用 loose 回归, 明确它只是抽样验证, 不能把 `write` 成功当成 MiniCPM5 全工具成功。
- [ ] 尽量补充一个不依赖 `write` 的直接 OpenAI-compatible tool-call 探针, 用于观察模型是否能泛化到另一个工具名。

### 状态

**目前在阶段9** - 正在依据用户修正重新收缩 prompt 和验证口径。

## [2026-06-03 22:24:00] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 已去掉 write 特化表达, 改为通用 path 参数契约

### 已完成

- [x] 删除 provider-local prompt 中 `read.path` / `edit.path` / `write.path` 等逐项枚举。
- [x] 改为“任何名为 `path` 的参数都必须使用相对路径”的通用契约。
- [x] 补充“文件名不能写成 `.`”与“目录请求可以使用 `.`”的泛化边界。
- [x] 单测加入 `!prompt.contains("write.path")`, 防止重新滑回 `write` 专项规则。

### 下一步

- [ ] 跑聚焦单测与格式检查。
- [ ] 如通过, 再跑 check/clippy/build 和真实回归。

## [2026-06-03 22:29:00] [Session ID: omx-1780470665249-tkxhle] [验证更新]: 聚焦 Rust 测试通过

### 验证命令

- `cargo fmt --check`
- `cargo test --package pi_agent_rust --lib -- app::tests::append_provider_local_system_prompt_appends_for_local_minicpm5_tool_use --exact --nocapture`
- `cargo test --package pi_agent_rust --lib -- app::tests::append_provider_local_system_prompt_skips_non_local_minicpm5_provider --exact --nocapture`
- `cargo test --package pi_agent_rust --lib -- app::tests::append_provider_local_system_prompt_skips_when_tools_are_disabled --exact --nocapture`
- `cargo test --package pi_agent_rust --lib -- app::tests::append_provider_local_system_prompt_is_idempotent --exact --nocapture`

### 结果

- [x] 4 个聚焦单测全部通过。
- [x] `cargo fmt --check` 通过。
- [ ] 继续运行 `cargo check --all-targets` / `cargo clippy --all-targets -- -D warnings` / `cargo build --bin pi`。

### 备注

- 输出仍有 macOS linker `__eh_frame` warning 和 `proc-macro-error2` future-incompat note, 与本次 prompt helper 逻辑无关, 先记录不作为本次修复目标。

## [2026-06-03 22:35:00] [Session ID: omx-1780470665249-tkxhle] [验证更新]: 完整 Rust 质量门通过

### 验证命令

- `cargo check --all-targets`
- `cargo clippy --all-targets -- -D warnings`
- `cargo build --bin pi`

### 结果

- [x] `cargo check --all-targets` 通过。
- [x] `cargo clippy --all-targets -- -D warnings` 通过。
- [x] `cargo build --bin pi` 通过。

### 下一步

- [ ] 确认或启动 `fast-infer` MiniCPM5 server。
- [ ] 跑 10 次 loose 回归。
- [ ] 加一个非 `write` 的 OpenAI-compatible 直接 tool-call 探针, 避免只用 `write` 样本下结论。

## [2026-06-03 22:39:00] [Session ID: omx-1780470665249-tkxhle] [回归失败]: 通用 path 契约仍不合格, 新失败形态为 `path = ."`

### 动态证据

- 证据目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-regression-97dvczs7`
- `tool_result_mismatch=10/10`。
- 10 次都触发真实 `write` tool call。
- 10 次 `path` 均为 `."`, Pi 因为这是相对文件名所以写入成功, 但不是测试期望文件名。

### 现象 -> 假设

- 现象: 绝对路径漂移消失, 但文件名被错误替换为 `."`。
- 主假设: prompt 中“目录请求可以使用 `.`”被 MiniCPM5 错误套用到文件创建任务。
- 备选解释: MLX shim 的 XML 到 OpenAI tool_calls 转换层在处理引号或标签闭合时产生了 `."`。

### 下一步验证

- [ ] 读取失败样本的 JSONL/日志, 查找是否存在原始 XML 或 assistant delta。
- [ ] 如不能从 Pi 事件判断, 用直接 OpenAI-compatible 请求做最小探针, 同时覆盖一个非 `write` 工具名。
- [ ] 修 prompt 时去掉“目录请求 `.`”这条容易误导的小模型规则, 改为“只有用户明确请求 current directory 才能用 `.`”。

## [2026-06-03 22:44:00] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 第二轮通用 prompt 已修正 `path = ."` 风险

### 已完成

- [x] 增加“tool call first, no prose before tool call”的通用工具调用纪律。
- [x] 增加“工具结果返回后才能说完成”的通用规则。
- [x] 把 `path` 规则改成复制用户请求的相对文件或目录路径。
- [x] 明确“当前目录 + 文件名”时 `path` 是文件名。
- [x] 明确只有请求当前目录本身且没有文件名时才使用 `.`。
- [x] 明确 `path` 里不能包含额外引号字符, 防止 `."`。

### 下一步

- [ ] 重跑 fmt/聚焦单测/check/clippy/build。
- [ ] 重跑 10 次 loose 回归。
- [ ] 保留非 `write` 直接探针证据, 最终结论避免把 `write` 当唯一目标。

## [2026-06-03 22:56:00] [Session ID: omx-1780470665249-tkxhle] [回归失败]: 第二轮 prompt 仍失败, 单靠 append prompt 不足

### 动态证据

- 证据目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-regression-jyxvl20u`
- `tool_result_mismatch=7`, `tool_error=3`, `tool_success=0`。
- 失败参数集中为 `path = ."` 或 `path = .`。
- 没有恢复到 `/Users/...` 绝对路径漂移, 但仍未选中用户指定文件名。

### 回滚口径

- 上一假设“删除目录宽泛规则后即可消除 `path = ."`”不成立。
- 推翻证据: 第二轮 10 次 loose 回归仍有 10/10 错参, 其中 7 次 `."`, 3 次 `.`。

### 新候选假设

- tool schema 的 path 描述仍包含 `relative or absolute`, 与 provider-local prompt 的相对路径约束冲突。
- MiniCPM5 在 Pi 完整请求中更依赖工具 schema 和用户提示里的“当前目录”, 因此持续把 path 抽成当前目录。

### 下一步

- [ ] 读取 OpenAI provider 构造 tools schema 的路径。
- [ ] 判断是否能做 provider-local tool schema 描述规范化, 且泛化到所有 `path` 参数, 不只改 `write`。

## [2026-06-03 23:04:00] [Session ID: omx-1780470665249-tkxhle] [实现更新]: 增加 local-minicpm5 provider-local tool schema 规范化

### 已完成

- [x] 在 `src/providers/openai.rs` 增加 `LOCAL_MINICPM5_PATH_ARGUMENT_DESCRIPTION`。
- [x] OpenAI provider 构造 tools 时, 对 `local-minicpm5` 递归规范化所有名为 `path` 的参数描述。
- [x] 默认 provider 路径仍保留原始 schema, 避免影响普通 OpenAI 和其它 OpenAI-compatible provider。
- [x] 新增单测覆盖默认不改写、本地 MiniCPM5 改写、嵌套 `path` 也改写。

### 下一步

- [ ] 跑格式、app helper 单测、OpenAI schema 单测、check/clippy/build。
- [ ] 重跑 10 次 loose 回归。

## [2026-06-03 23:07:00] [Session ID: omx-1780470665249-tkxhle] [错误记录]: `cargo fmt --check` 发现格式差异

### 现象

- `cargo fmt --check` 在 `src/providers/openai.rs` 新增测试断言处失败。
- 输出只显示 rustfmt 换行格式差异, 没有编译错误。

### 处理

- [x] 运行 `cargo fmt` 应用项目标准格式。
- [ ] 重新运行完整验证。

## [2026-06-03 23:20:00] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 第三轮收紧 path 契约, 取消 `.` 的正向许可

### 动态证据

- 上一轮 provider-local schema 规范化后, 10 次 loose 回归从 `0/10` 提升到 `6/10`。
- 剩余失败仍为 `path = ."`, 说明方向有效但 `.` 仍被小模型当成候选文件路径。

### 修改

- prompt 删除“可使用 `.`”的正向表达。
- prompt 改为: 明确文件名存在时不能使用 `.` / `."` 当前目录标记。
- prompt 增加: 可选 `path` 没有显式路径时应省略 `path`, 不用 `.` 代替。
- provider-local schema 描述同步改为同一套规则。

### 下一步

- [ ] 重跑格式、相关单测、check/clippy/build。
- [ ] 重跑 10 次 loose 回归。

## [2026-06-03 23:36:00] [Session ID: omx-1780470665249-tkxhle] [实现更新]: MiniCPM5 schema 规范化改为工具语义分类

### 已完成

- [x] 增加文件路径描述常量。
- [x] 增加搜索/列表可选路径描述常量。
- [x] 增加未知工具通用路径描述常量。
- [x] provider-local schema 规范化现在接收工具名, 按工具分类改写 `path` 描述。
- [x] prompt 同步写明文件工具集合和搜索/列表工具集合。
- [x] 新增单测覆盖 `write` 文件工具和 `ls` 列表工具使用不同 path 描述。

### 下一步

- [ ] 跑格式、相关单测、check/clippy/build。
- [ ] 重跑 10 次 loose 回归。

## [2026-06-03 23:39:00] [Session ID: omx-1780470665249-tkxhle] [错误记录]: 第四轮 `cargo fmt --check` 格式失败

### 现象

- `src/providers/openai.rs` 的 `serde_json::Value::String(...)` 换行格式与 rustfmt 不一致。

### 处理

- [x] 运行 `cargo fmt`。
- [ ] 重跑验证。

## [2026-06-03 23:58:00] [Session ID: omx-1780470665249-tkxhle] [实现更新]: 增加 local-minicpm5 path 参数保守修复层

### 已完成

- [x] `execute_tool_calls` 在发出 ToolExecutionStart 前, 生成修复后的 tool call 列表。
- [x] 修复层只对 `local-minicpm5` + `minicpm5` 生效。
- [x] 最近用户文本必须提取出唯一明确相对路径候选才修。
- [x] 修复任意工具的 `path` 参数, 不限定 `write`。
- [x] 新增 4 个聚焦单测:
  - `."` -> 用户唯一文件名。
  - 绝对路径 -> 用户唯一相对路径。
  - 非本地 provider 不修。
  - 多候选不修。

### 下一步

- [ ] 跑格式、相关单测、check/clippy/build。
- [ ] 重跑 10 次 loose 回归。

## [2026-06-04 00:01:00] [Session ID: omx-1780470665249-tkxhle] [错误记录]: path repair 测试处格式失败

### 现象

- `cargo fmt --check` 在 `src/agent.rs` 新增测试的长参数行处失败。

### 处理

- [x] 运行 `cargo fmt`。
- [ ] 重跑验证。

## [2026-06-04 00:17:00] [Session ID: omx-1780470665249-tkxhle] [完成记录]: local-minicpm5 path repair 后真实回归通过

### 动态验证

- 10 次 loose 写入样本证据目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-regression-86wrdggb`
  - `tool_success=10/10`。
  - 10 次 `tool_execution_start.args.path` 均为期望相对文件名。
  - 10 个文件均真实落盘, 内容匹配 `PI_MINICPM5_TOOL_OK_XX`。
- 3 次非 `write` read 样本证据目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-read-regression-kbgl0q7m`
  - `tool_success=3/3`。
  - 3 次均调用 `read` 工具, `path` 均为期望相对文件名。
  - 3 次 `read` 工具结果均返回对应 `PI_MINICPM5_READ_OK_XX` 内容。
  - 其中 2 次未等到 `agent_end`, 但 tool execution start/end 均完整且非 error。

### 完成状态

- [x] 通用 provider-local prompt。
- [x] local-minicpm5 provider-local tool schema 规范化。
- [x] local-minicpm5 保守 path repair 层。
- [x] Rust 格式、聚焦单测、check、clippy、build。
- [x] 10 次 loose 写入样本回归。
- [x] 非 `write` 的 read 样本真实工具执行回归。

### 最终状态

**阶段9/10 已完成** - 正在写 WORKLOG / ERRORFIX / LATER_PLANS / EPIPHANY 记录并准备交付。

## [2026-06-04 10:30:45] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 回答 path schema 与 read agent_end 续问

### 用户问题

- 解释为什么只对 local-minicpm5 改写 OpenAI tools schema 中的 path 描述, path 到底哪里有问题。
- 解释非 write 的 read 样本中 2 次没有等到最终 agent_end, 是不是输出长度或其它原因。

### 本轮动作

- [x] 回读支线 task_plan / notes 中的动态证据。
- [ ] 核对 src/app.rs / src/providers/openai.rs / src/agent.rs / src/tools.rs 的静态证据。
- [ ] 核对 read 回归事件文件中 tool_execution 与最后 message_update 形态。
- [ ] 按现象 -> 假设 -> 验证 -> 结论回答用户。

## [2026-06-04 10:31:35] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 续问证据复核完成

### 已完成

- [x] 核对 src/app.rs / src/providers/openai.rs / src/agent.rs / src/tools.rs 的静态证据。
- [x] 核对 read 回归事件文件中 tool_execution 与最后 message_update 形态。
- [x] 将证据摘要追加到 notes__minicpm5_prompt.md。

### 结论准备

- path 问题不是字段实现错误, 是 local MiniCPM5 生成 path 参数不稳定且会受 schema 文案影响。
- 2 次 read 未见 agent_end 的已验证现象是 post-tool assistant 文本生成未收束, 不是 read 工具失败。

## [2026-06-04 10:32:05] [Session ID: omx-1780470665249-tkxhle] [完成记录]: 续问回答准备完成

### 完成项

- [x] 续问证据复核。
- [x] notes 记录。
- [x] WORKLOG 记录。
- [x] EPIPHANY 检查: 没有新增重大风险需要追加。

### 状态

**阶段10/10 已完成** - 准备向用户交付解释。

## [2026-06-05 12:12:40] [Session ID: omx-1780470665249-tkxhle] [任务计划]: MiniCPM5 多工具矩阵与 post-tool 回答约束

### 目标

- 把 `local-minicpm5` 的真实 tool-use 验证从 `write` 单点扩展到 `read`、`grep`、`find`、`ls`、`edit` 小矩阵。
- 增加 provider-local post-tool 回答约束, 防止工具成功后复述/幻化不存在的行号或 JSON 列表。
- 用真实 Pi + 本地 MiniCPM5 server 生成证据, 证明它不是只把 `write` 调通。

### 阶段

- [ ] 阶段1: 复核当前 prompt/schema/agent 工具执行链路。
- [ ] 阶段2: 增加 local-minicpm5 post-tool 回答约束与聚焦单测。
- [ ] 阶段3: 构建并运行 read/grep/find/ls/edit 真实矩阵回归。
- [ ] 阶段4: 运行 Rust 验证门与必要回归。
- [ ] 阶段5: 记录证据并交付结论。

### 当前策略

- 不把 `write` 做成特例。
- 不全局改变其它 provider 的 prompt/schema 行为。
- 优先复用已有 provider-local prompt helper 和真实 Pi RPC 路径。
- 若矩阵脚本只是验证用途, 优先作为临时脚本运行并记录证据; 只有确认值得沉淀时再考虑落盘到项目。

### 状态

**目前在阶段1** - 正在复核当前代码链路和可复用验证入口。

## [2026-06-05 12:18:00] [Session ID: omx-1780470665249-tkxhle] [实现更新]: 增加 local-minicpm5 post-tool 回答约束

### 已完成

- [x] 在 `LOCAL_MINICPM5_TOOL_USE_PROMPT` 中增加工具返回后的回答约束。
- [x] 约束明确要求只基于真实 tool result 回答。
- [x] 约束明确禁止把 `read` 的一行结果扩写为 JSON array / numbered list / 虚构 line records。
- [x] app 层单测增加 post-tool 约束断言。

### 下一步

- [ ] 跑 `cargo fmt --check` 与 app 聚焦单测。
- [ ] 构建并运行 read/grep/find/ls/edit 真实矩阵。

## [2026-06-05 12:23:00] [Session ID: omx-1780470665249-tkxhle] [验证更新]: post-tool prompt 聚焦单测通过

### 命令

- `cargo fmt --check`
- `cargo test --package pi_agent_rust --lib -- app::tests::append_provider_local_system_prompt_appends_for_local_minicpm5_tool_use --exact --nocapture`

### 结果

- app 聚焦单测通过。
- 仅出现已知 macOS linker `__eh_frame` warning 和 `proc-macro-error2` future-incompat note。

### 下一步

- [ ] 查找/复用现有 Pi RPC / MiniCPM5 回归脚本。

## [2026-06-05 12:25:30] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 准备真实矩阵验证

### 决策

- 现有 `fast-infer/pi_minicpm5_tool_regression.py` 只覆盖 `write`。
- 本轮先使用临时 Python 脚本跑 `read/grep/find/ls/edit` 矩阵, 避免在未知结果前扩大脚本表面积。
- 如果矩阵验证结果稳定且值得长期复用, 再考虑修改现有脚本。

### 下一步

- [ ] 构建最新 `target/debug/pi`。
- [ ] 检查 127.0.0.1:18081 MiniCPM5 server 是否 ready。
- [ ] 运行临时矩阵脚本。

## [2026-06-05 12:28:35] [Session ID: omx-1780470665249-tkxhle] [错误记录]: 第一轮多工具矩阵未通过

### 现象

- `read/grep/find/ls` 均没有真实 tool call。
- `edit` 有真实 tool call, 但 `newText` 漏掉 `_OK_` token。

### 证据目录

- `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-tool-matrix-7fr7v0bw`

### 当前判断

- 失败不是 XML parser 解析错误; 多个场景根本没有 tool call。
- 当前 local-minicpm5 prompt 对“文件系统任务必须调用工具”的触发规则仍不够硬。
- 当前 prompt 对 `oldText/newText/pattern/content` 等字面量参数复制约束不够硬。

### 下一步

- [ ] 增加通用文件系统工具触发规则。
- [ ] 增加字面量参数逐字复制规则。
- [ ] 更新 app 单测。
- [ ] 重建 Pi 并重跑矩阵。

## [2026-06-05 12:31:00] [Session ID: omx-1780470665249-tkxhle] [实现更新]: 增加文件系统工具触发与字面量复制规则

### 已完成

- [x] prompt 增加 `File-system facts must come from tools`。
- [x] prompt 明确 `read/grep/find/ls/edit/write` 对应文件系统任务必须真实调用工具。
- [x] prompt 明确不能根据用户请求里的文件名或猜测直接回答文件内容、搜索结果、目录列表或编辑成功。
- [x] prompt 明确 `path/pattern/oldText/newText/content` 必须逐字复制用户请求。
- [x] app 单测断言更新。

### 下一步

- [ ] 跑格式、聚焦单测、重建 Pi。
- [ ] 重跑矩阵。

## [2026-06-05 12:40:05] [Session ID: omx-1780470665249-tkxhle] [验证更新]: focused 矩阵部分通过并暴露三类剩余问题

### 已通过

- [x] `read` 真实 tool call + post-tool 简短回答通过。
- [x] `edit` 真实 tool call + 精确 `newText` + 文件真实修改通过。

### 未通过

- [ ] `grep`: 真实 tool call, 但 `glob="."` 参数导致无结果。
- [ ] `find`: 真实 tool call, 但本机缺少 `fd`。
- [ ] `ls`: 先出现一次 malformed XML parse_error, 后续二轮真实 `ls` 成功。

### 下一步

- [ ] 检查 `fd` 环境。
- [ ] 分析 grep 参数错位是否可用 provider-local schema / repair 处理。
- [ ] 判断 ls parse_error 是否属于 fast-infer parser 容错边界还是 prompt 可改善。

## [2026-06-05 12:45:00] [Session ID: omx-1780470665249-tkxhle] [实现更新]: 增加 local-minicpm5 grep 参数保守修复

### 已完成

- [x] 在 `repair_local_minicpm5_tool_call_arguments` 中串接 path 修复与 grep 参数修复。
- [x] 只在 provider-local repair 已经通过 `local-minicpm5` + `minicpm5` + 用户唯一相对路径候选门槛后处理。
- [x] 针对 `grep` 且 `glob` 为 `.` / `./` 且没有 `path` 的情况, 将用户唯一文件候选写入 `path` 并移除退化 `glob`。
- [x] 新增单测覆盖 `grep.glob="."` 修复为 `path=search.txt`。

### 安全边界

- 非 `grep` 不处理。
- `candidate` 不像文件路径时不处理。
- 已经有 `path` 或 `glob` 非退化时不处理。
- 多候选路径仍由上层门槛跳过。

### 下一步

- [ ] 跑格式、agent grep 修复单测、app prompt 单测、构建。
- [ ] 重跑 focused 矩阵。

## [2026-06-05 12:49:05] [Session ID: omx-1780470665249-tkxhle] [错误记录]: 第三轮矩阵 read 发生 post-tool 幻化

### 现象

- summary 显示 5 个工具均 `tool_success`, 但人工复核 read 最终回答发现幻化行列表。
- read 工具真实只返回一行 `PI_MINICPM5_MATRIX_READ_OK_01`。
- assistant 最终回答却生成 `1→P1` 到 `100→P100`。

### 当前结论

- 工具调用矩阵不能只看 tool_execution 是否成功。
- read 场景必须同时校验 post-tool 最终文本。

### 下一步

- [ ] 收紧临时矩阵 read 分类。
- [ ] 加强 post-tool read 约束。
- [ ] 重跑矩阵。

## [2026-06-05 12:56:00] [Session ID: omx-1780470665249-tkxhle] [验证修正]: 收紧临时矩阵 read 判定

### 修正原因

- 上一轮 summary 把 `read` 归为 `tool_success`, 但人工复核发现最终回答没有包含真实 `PI_MINICPM5_MATRIX_READ_OK_01`, 反而幻化 `P1..P100`。

### 已修正

- [x] `read` 最终回答必须包含真实 expected 文本。
- [x] `read` 最终回答不能出现 `2→` / `3→` / `P2` / `P3` / `line 2` 等扩写迹象。

## [2026-06-05 13:05:00] [Session ID: omx-1780470665249-tkxhle] [实现更新]: 加强 read post-tool 输出约束

### 已完成

- [x] `read` 约束明确说明 `1→TEXT` 中 `1→` 是工具元数据, `TEXT` 才是文件内容。
- [x] 明确禁止把 `1→...` 继续补生成 `2→...`。
- [x] 明确单行 read 结果只能复制返回的 `TEXT` 一次, 或说明已读取。
- [x] 明确禁止幻化 `P1`、`P2`、`P100` 等缩写 token。
- [x] app 单测断言同步更新。

### 下一步

- [ ] 跑 `cargo fmt --check`。
- [ ] 跑 app prompt 聚焦单测。
- [ ] 跑 agent grep 修复聚焦单测。
- [ ] 重建 `target/debug/pi`。
- [ ] 重跑收紧后的 read/grep/find/ls/edit focused 矩阵。

## [2026-06-05 13:12:05] [Session ID: omx-1780470665249-tkxhle] [状态更新]: 准备实现重复工具调用保护

### 当前问题

- `read` 不再是 tool selection 失败。
- `read` 也不是 parser 或 path 失败。
- 当前失败是同一成功工具调用被重复执行, 最终超过工具轮次。

### 下一步

- [ ] 增加 local-minicpm5 重复工具调用检测。
- [ ] 在 run_loop 中, 对重复同一成功工具调用生成 provider-local 最终 assistant 文本。
- [ ] 补单测覆盖重复 read 被转为最终文本。
- [ ] 重跑 Rust 验证与 focused 矩阵。

## [2026-06-05 13:20:00] [Session ID: omx-1780470665249-tkxhle] [行动记录]: 实现重复成功工具调用保护

### 当前证据

- `read` 场景已经能真实调用 `read(path=matrix_read_01.txt)`。
- 工具真实返回 `1→PI_MINICPM5_MATRIX_READ_OK_01`。
- local MiniCPM5 在 post-tool 阶段重复发同一个 `read(path=matrix_read_01.txt)`, 最终超过 `max_tool_iterations=4`。

### 将要做的事

- [ ] 在 agent 层增加 provider-local 重复调用检测函数。
- [ ] 只在 `local-minicpm5` + MiniCPM5 + 单个 tool call + 历史中存在同名同参成功 tool result 时触发。
- [ ] 触发时把重复 tool call 转成最终 assistant 文本, 文本只来自最近成功 tool result。
- [ ] 补单测锁定这个边界。

### 为什么这样做

- 这是结构性防护, 不依赖继续堆 prompt 文案。
- 只拦截重复执行同一成功工具的情况, 不影响新的工具调用和其它 provider。
