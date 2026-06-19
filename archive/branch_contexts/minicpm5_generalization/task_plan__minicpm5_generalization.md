# 任务计划: local-minicpm5 专项逻辑通用化 deep-interview

## [2026-06-05 17:08:00] [Session ID: omx-1780470665249-tkxhle] 计划: 建立通用化需求规格

### 目标

通过 `$oh-my-codex:deep-interview` 澄清: 当前 `local_minicpm5` 专项代码应抽象成哪一种通用能力 / profile / 策略机制, 以及第一阶段的范围和验收标准。

### 阶段

- [x] 阶段1: 启动 deep-interview 状态并声明只读边界
- [x] 阶段2: 读取当前代码中 `local_minicpm5` 相关事实
- [ ] 阶段3: 访谈澄清意图, 非目标, 决策边界和验收标准
- [ ] 阶段4: 产出 `.omx/interviews` 和 `.omx/specs` 规格文档

### 当前已知事实

- `src/app.rs` 中存在 provider-local system prompt append, 名称和 marker 都绑定 `local-minicpm5` / MiniCPM5。
- `src/providers/openai.rs` 中存在 provider-local OpenAI tools schema `path` 描述改写, 只对 `LOCAL_MINICPM5_PROVIDER_ID` 生效。
- `src/agent.rs` 中存在 provider/model 绑定的 path repair 与 post-tool repeated successful tool-call rewrite。
- 前置 loose 回归显示弱约束下漂移率高, 但 focused 修复证明硬约束下 tool-use 可稳定通过小矩阵。

### 状态

**目前在阶段3** - 需要向用户确认第一阶段想抽象的边界: 是只改命名和配置分流, 还是建立可扩展 provider/model behavior profile。

## [2026-06-05 17:08:34] [Session ID: omx-1780470665249-tkxhle] 修正: context snapshot 已恢复

- 修复对象: `.omx/context/minicpm5-generalization-20260605T090709Z.md`。
- 修复原因: 首次写入时 heredoc 未加单引号, 反引号内容被 shell 执行。
- 当前状态: snapshot 已重新写入, 后续 deep-interview 继续基于修复后的事实摘要进行。

## [2026-06-07 18:42:28] [Session ID: omx-1780470665249-tkxhle] deep-interview Round 1 答案: 选择可配置 profile

- 用户选择: B, 做成可配置 profile。
- 含义: 第一阶段不只是内部重命名, 而是要在模型配置层暴露类似 `toolUseProfile` / `behaviorProfile` 的机制, 让其他本地小模型也能显式复用 local-minicpm5 当前这类 hardening。
- 下一步访谈焦点: profile 的配置形态是命名预设还是细粒度 feature flags。

## [2026-06-07 21:03:18] [Session ID: omx-1780470665249-tkxhle] deep-interview Round 2 答案: profile 名称引用 + 配置文件定义

- 用户选择: 使用 profile 名称, 例如 `weak-openai-compatible`。
- 关键边界: `weak-openai-compatible` 的具体 hardening 配置不应写死在 Rust 代码内部, 而应存在配置文件中。
- 架构含义: Rust 代码应实现通用解释器 / 执行器, 读取 profile 配置后应用 prompt/schema/repair/repeat guard 等行为。
- 当前待澄清: profile definitions 应放在 `models.json` 顶层、provider 下, 还是单独一个 profiles 文件。

## [2026-06-08 14:46:56] [Session ID: omx-1780470665249-tkxhle] deep-interview Round 3 答案: profile 定义放在 models.json 顶层

- 用户选择: A, profile 定义放在同一个 `models.json` 顶层。
- 配置形态: `models.json` 同时包含 `toolUseProfiles` 定义表和 `providers` 模型定义。
- 架构含义: Rust 代码需要在 `ModelsConfig` 顶层读取 `toolUseProfiles`, 再让 provider 或 model 通过 profile 名称引用对应规则。
- 下一步访谈焦点: 第一阶段 profile 引用范围是仅 model-level, 还是同时允许 provider-level 默认值; 以及是否迁移现有 local-minicpm5 全局配置。

## [2026-06-08 15:09:44] [Session ID: omx-1780470665249-tkxhle] deep-interview Round 4 答案: provider-level 默认 + model-level override

- 用户选择: B, 同时允许 provider-level 默认 profile 和 model-level override。
- 预期规则: provider 下的 `toolUseProfile` 是默认值; model 下的 `toolUseProfile` 可以覆盖 provider 默认值。
- 架构含义: `ProviderConfig` 和 `ModelConfig` 都需要支持 `toolUseProfile` 字段, profile resolve 应形成单一真相源, 最终每个 `ModelEntry` 只携带 resolved profile 或 resolved profile config。
- 下一步访谈焦点: closure audit, 明确第一阶段非目标和验收标准。

## [2026-06-08 15:11:15] [Session ID: omx-1780470665249-tkxhle] deep-interview Round 5 答案: 非目标和验收边界确认

- 用户确认 Round 5 边界。
- 第一阶段要做: 在 `models.json` 顶层支持 `toolUseProfiles`; provider/model 支持 `toolUseProfile`; 用 profile 驱动 prompt/schema/path repair/repeat guard/read line-prefix 收束; 迁移现有 `local_minicpm5` 命名和硬编码判断; 保持 MiniCPM5 focused 小矩阵不回退。
- 第一阶段不做: 独立 `tool-use-profiles.json`; GUI/TUI 配置编辑器; 远程下载 profile; 无限细粒度 knobs; 自动给任意模型套 weak profile; 不把 loose 66% 漂移率作为本轮必须降低目标。
- 当前状态: ambiguity 已低于阈值, 开始 crystallize artifacts。

## [2026-06-08 15:18:06] [Session ID: omx-1780470665249-tkxhle] 修正: artifact 首次写入截断

- 首次 crystallize artifact 写入不完整。
- 下一步动作: 修复 `.omx/interviews/minicpm5-generalization-20260608T071724Z.md`, 新增 `.omx/specs/deep-interview-minicpm5-generalization.md`。

## [2026-06-08 15:20:57] [Session ID: omx-1780470665249-tkxhle] 完成: deep-interview artifacts 已生成

- 已生成 transcript: `.omx/interviews/minicpm5-generalization-20260608T071724Z.md`。
- 已生成 spec: `.omx/specs/deep-interview-minicpm5-generalization.md`。
- 已验证两个文件内容完整: transcript 73 行, spec 204 行。
- 当前 deep-interview 已完成, 不进入实现。下一步需要用户显式切换到 `$ralplan`, `$ultragoal`, `$autopilot`, `$team` 或 `$ralph`。

### 阶段状态

- [x] 阶段1: 启动 deep-interview 状态并声明只读边界
- [x] 阶段2: 读取当前代码中 `local_minicpm5` 相关事实
- [x] 阶段3: 访谈澄清意图, 非目标, 决策边界和验收标准
- [x] 阶段4: 产出 `.omx/interviews` 和 `.omx/specs` 规格文档

## [2026-06-08 15:22:43] [Session ID: omx-1780470665249-tkxhle] ralplan 启动: toolUseProfiles 共识规划

- 用户显式切换到 `$oh-my-codex:ralplan .omx/specs/deep-interview-minicpm5-generalization.md`。
- 当前模式: consensus planning, 不实现代码。
- 输入规格: `.omx/specs/deep-interview-minicpm5-generalization.md`。
- 已读取代码事实:
  - `src/app.rs` 的 MiniCPM5 专用 prompt 常量和 append gate。
  - `src/providers/openai.rs` 的 MiniCPM5 专用 path schema rewrite。
  - `src/agent.rs` 的 MiniCPM5 专用 path repair 与 repeat guard。
  - `src/models.rs` 的 `ModelsConfig` / `ProviderConfig` / `ModelConfig` 当前结构。
- 下一步: 产出 `.omx/plans/prd-minicpm5-tool-use-profiles.md` 与 `.omx/plans/test-spec-minicpm5-tool-use-profiles.md`, 再顺序执行 Architect -> Critic 共识审查。


## [2026-06-10 17:01:52] [Session ID: omx-1781010764764-n4q7h4] 新任务: 为 OpenAI-compatible 本地模型透传生成参数

### 目标
- 在 Pi 的模型配置层支持 per-model / provider-level 生成参数, 第一阶段覆盖 stop 序列和 repetition penalty。
- 让 local-minicpm5 可以通过 models.json 显式配置 stop=["<|im_end|>", "</s>"] 与 repetitionPenalty=1.15。
- OpenAI Chat Completions 请求体需要实际带出 stop 和 repetition_penalty, 防止 MiniCPM5 在 Pi 下循环输出到 max_tokens。

### 现象 -> 假设 -> 验证计划 -> 结论
- 现象: 用户反馈 MiniCPM5 在 Pi 下循环输出停不下来。
- 已验证事实: 当前 mlx_lm_minicpm5_server.py 不支持 --stop-sequences 或 --repetition-penalty 启动参数; MLX-LM server 只从 HTTP body 读取 stop 和 repetition_penalty。
- 主假设: Pi 当前 OpenAI provider 没有从 models.json 读取并透传 stop / repetition_penalty, 导致请求体没有停止序列和重复惩罚。
- 备选解释: 循环也可能来自 prompt/tool-use 后处理弱约束或模型本身能力不足; stop 和 repetition penalty 只能降低/截断风险, 不能保证所有 loose 场景完全稳定。
- 推翻主假设的证据: 聚焦测试中 OpenAI 请求 JSON 已经包含 stop 和 repetition_penalty, 或 Pi 存在其他全局请求体注入机制。

### 阶段
- [x] 阶段1: 读取上下文与现有配置/代码事实。
- [ ] 阶段2: 设计有界 generation config 结构并添加 failing/request-shape 测试。
- [ ] 阶段3: 实现 models.json 解析、provider/model 继承与 OpenAI 请求透传。
- [ ] 阶段4: 更新用户全局 models.json 的 local-minicpm5 配置。
- [ ] 阶段5: 运行聚焦测试、格式检查和编译检查。
- [ ] 阶段6: 记录 WORKLOG / ERRORFIX 并给出验证证据。

### 当前状态
**目前在阶段2** - 先围绕 src/models.rs 和 src/providers/openai.rs 添加最小可证伪测试, 再实现代码。


## [2026-06-10 17:47:32] [Session ID: omx-1781010764764-n4q7h4] 阶段2-4进展: generation 配置与 Pi 全局配置已更新

### 已完成
- 在 `src/models.rs` 增加 `GenerationConfig`, 并让 provider/model 都支持 `generation` 字段。
- provider-level `generation` 作为默认值, model-level `generation` 可以覆盖默认值。
- 在 `src/providers/openai.rs` 透传 `stop` 与 `repetition_penalty` 到 OpenAI Chat Completions 请求体。
- 已更新 `/Users/cuiluming/.pi/agent/models.json` 的 local-minicpm5 模型条目。

### 配置变更
- local-minicpm5 MiniCPM5 条目新增 `generation.stop=["<|im_end|>", "</s>"]`。
- local-minicpm5 MiniCPM5 条目新增 `generation.repetitionPenalty=1.15`。
- local-minicpm5 MiniCPM5 条目 `maxTokens` 从 4096 降为 512。

### Todo 更新
- [x] 阶段1: 读取上下文与现有配置/代码事实。
- [x] 阶段2: 设计有界 generation config 结构并添加 failing/request-shape 测试。
- [x] 阶段3: 实现 models.json 解析、provider/model 继承与 OpenAI 请求透传。
- [x] 阶段4: 更新用户全局 models.json 的 local-minicpm5 配置。
- [ ] 阶段5: 运行聚焦测试、格式检查和编译检查。
- [ ] 阶段6: 记录 WORKLOG / ERRORFIX 并给出验证证据。

### 当前状态
**目前在阶段5** - 重新跑三个聚焦测试、cargo fmt --check、cargo check --all-targets, 然后安装新的 pi 二进制。


## [2026-06-10 18:15:56] [Session ID: omx-1781010764764-n4q7h4] 阶段5-6完成: generation 请求透传已验证并安装

### Todo 更新
- [x] 阶段1: 读取上下文与现有配置/代码事实。
- [x] 阶段2: 设计有界 generation config 结构并添加 failing/request-shape 测试。
- [x] 阶段3: 实现 models.json 解析、provider/model 继承与 OpenAI 请求透传。
- [x] 阶段4: 更新用户全局 models.json 的 local-minicpm5 配置。
- [x] 阶段5: 运行聚焦测试、格式检查和编译检查。
- [x] 阶段6: 记录 WORKLOG / ERRORFIX 并给出验证证据。

### 最终状态
**任务完成** - Pi 已安装新二进制,MiniCPM5 请求会发送 stop 和 repetition_penalty,当前真实 smoke 以 stopReason=stop 正常结束。

### 边界
- 本轮没有提交 git commit。
- 工作区中上一轮 TUI 退出恢复的未提交改动保持原样,没有撤回。
- 模型 smoke 输出内容不符合“只输出 OK”,这是已知指令遵循/loose 质量问题,不属于本轮停止机制修复。
