# Notes: rdog-control-bash toolUseProfile

## [2026-06-18 17:30:00] [Session ID: omx-1781769685432-9t7wjx] 笔记: rdog-control skill 真实执行路径

### 直接证据
- skill 路径: `/Users/cuiluming/.pi/agent/skills/rdog-control.md` -> `/Users/cuiluming/local_doc/l_dev/my/rust/rustdog/.codex/skills/rdog-control/SKILL.md` (symlink)
- skill 行数: 233
- skill 全文没有提到任何非 bash 入口；所有命令形式都是 `printf '...' | rdog control TARGET` / `rdog control TARGET --pty -- COMMAND` 之类 shell 调用。

### 推断
- 在 Pi 里跑这条 skill 的 LLM，工具调用层面只需要 `bash`。
- 其它内置工具（read/write/edit/grep/find/ls/hashline_edit）在这个 skill 工作流里都是噪声，会挤占 prompt 和 schema token。
- 因此"只保留 bash"既减少 token，也降低弱模型误调 read/write 的概率。

## [2026-06-18 17:31:00] [Session ID: omx-1781769685432-9t7wjx] 笔记: 现有 toolUseProfile 机制与缺口

### 现状字段
- `appendSystemPrompt`: 追加 system 文本
- `pathSchema.fileTools`/`optionalPathTools`: 标记哪些 tool 的 `path` 是必填/可选
- `pathSchema.*Description`: 改写这些 tool 的 `path` 字段 description
- `argumentRepair`: 路径/glob 退化值修复
- `postToolGuard`: 同名同参重放 / read 行号剥离

### 缺口
- 没有 `tools` allowlist 字段。即便写了"只用 bash"的 prompt，模型在 OpenAI 请求里仍会看到 read/write/grep/...，schema token 一样贵。
- 这正是新增 `tools` 字段的理由：把"模型可见工具集合"也变成 profile 单一真相源的一部分。

### 单一真相源边界
- profile 解析发生在 `src/models.rs::resolve_tool_use_profile`，单一函数。
- `OpenAIProvider::build_request` 是工具 schema 流入 model 的唯一出口（在该 provider 内），在这里过滤不会污染 anthropic/bedrock/vertex 路径。
- 不动 `Context.tools`：保持 tool registry 与 profile 解耦，profile 只决定"发给模型的 schema"，不影响 Pi 内部能力。

## [2026-06-18 17:32:00] [Session ID: omx-1781769685432-9t7wjx] 笔记: 设计选择

### 方案A: 在 `Context.tools` 处切
- 优点: 全 provider 生效。
- 缺点: 非 OpenAI 路径（Anthropic、Bedrock、Vertex、GitHub Copilot、GitLab Duo）的 schema 构造点要各自再加一份过滤逻辑，重复且容易漏。
- 不选。

### 方案B: 在 OpenAI provider `build_request` 处切
- 优点: 单点、本地 OpenAI-compatible 模型（gemma/minicpm5/qwen/nemotron/...）全部受益；其它 provider 暂不需要。
- 缺点: 暂未覆盖非 OpenAI 路径。如果以后 bedrock 上 weak 模型也有同样需求，再加一份 filter。
- 选 B。

### 方案C: 在 `convert_tool_to_openai_with_profile` 里返回 Option
- 优点: 过滤点与 path 改写点共址，profile 中心化。
- 缺点: `build_request` 收集时仍需要 `.filter_map`，与在收集前 filter 写法等价。
- 选 B 但允许 `convert_tool_to_openai_with_profile` 内部做 `Option` 返回（更内聚），或保持返回 `OpenAITool` + 在 build_request 里 filter_map；折中选后者，与现状最小 diff。

## [2026-06-18 17:33:00] [Session ID: omx-1781769685432-9t7wjx] 笔记: 现有参考点

### 测试入口
- `src/providers/openai.rs::tool_use_profile_conversion_rewrites_path_descriptions_from_config` (line ~1380)
- `src/providers/openai.rs::tool_use_profile_conversion_uses_configured_tool_categories` (line ~1426)
- `src/providers/openai.rs::tool_use_profile_conversion_skips_generic_path_without_description` (line ~1461)
- 新 case 应加到同一 mod，与 `tool_use_path_schema_profile` helper 风格保持一致。

### 加载测试
- `src/models.rs::model_registry_loads_tool_use_profiles_and_provider_default` (line ~3798)
- `src/models.rs::model_registry_model_tool_use_profile_overrides_provider_default` (line ~3881)
- `src/models.rs::model_registry_unknown_provider_tool_use_profile_fails_closed` (line ~3942)
- 新 case：profile 带 `tools` 字段、模型加载后 `entry.tool_use_profile.tools` 与配置一致。

### 真实验证路径
- 加载后的 `OpenAIProvider::build_request` 输出的 `OpenAIRequest.tools` 是 Vec<OpenAITool>，是发给本地 OpenAI-compatible server 的 schema。
- 在 Pi 端：可以用 `pi --provider local --model <abs path> --mode json --print --no-session --tools bash` 直接验证 schema。
- 不在沙箱跑 MLX 推理，只跑 schema 构造。也可以在 `cargo test` 里直接断言 `OpenAIRequest.tools` 长度。

---

## [2026-06-18 18:35:00] [Session ID: codex-native-2026-06-18-rdog-bash-smoke] 笔记: 对照实验设计 - profile appendSystemPrompt 显式 stdin-frame 强制

### 实验设计
- 背景: 3 次 smoke 全部失败, 模型不会自发用 stdin-frame 形态。
- 变量: profile `appendSystemPrompt` 内容。
- 3 组对照:
    - A (基线): 当前内容, 列出 `@ping, @capabilities, ...` 但不解释 stdin-frame。
    - B (stdin-frame 强制): 显式写"line-control frame 必须通过 stdin 喂入, rdog 命令后面不是参数"。给 printf | 单一形态。
    - C (stdin-frame + 多形态示例): 同 B, 但加 printf|heredoc|echo 三种合法形态, 加 @ping / @capabilities 各一个 example。
- 指标: 模型在 3 次 smoke 中写出正确 stdin-frame 形态的次数。
- 决策:
    - A 失败 (3/3 失败) → 已观察, 现象确认。
    - B 3/3 成功 → 候选假设成立, profile prompt 设计修正。
    - B 仍失败但 C 成功 → gemma 2B 需 few-shot 示例, 走 C。
    - C 仍失败 → 备选成立, gemma-2B 能力上限, 记 LATER_PLANS。

### prompt B 设计 (待写入 ~/.pi/agent/models.json)
- You have exactly one tool: bash.
- Use bash to invoke `rdog control TARGET` (TARGET is a Zenoh target name like `mac.lab`).
- `rdog` is a stdio remote-control bridge. The line-control frame is fed via **stdin**, NOT as command-line args. So `rdog control mac.lab @ping` is WRONG; rdog will parse `@ping` as a port and error with `Invalid port @ping: invalid digit found in string`.
- Correct shape: `printf '@ping\n' | rdog control mac.lab` (or `rdog control mac.lab <<< "@ping"`, or `echo '@ping' | rdog control mac.lab`). The `@X` is the line-control frame, sent on stdin.
- One line-control command per bash call. Common frames: `@ping`, `@capabilities`, `@bootstrap`, `@observe`, `@cmd`, `@key`, `@paste`, `@ax-action`, `@web-find`, `@web-act`, `@savefile`, ...
- For a real terminal session use `rdog control TARGET --pty -- COMMAND`.
- Do not repeat a successful bash call. Parse the @response / @savefile / @pty-* frame, then answer briefly in plain text.

### 执行计划
1. 备份当前 profile.appendSystemPrompt 到 task_plan 末尾。
2. 改 ~/.pi/agent/models.json 写入 prompt B。
3. 跑 3 次 smoke (用同一个 prompt "用 bash 通过 rdog control mac.lab @capabilities 拿这个 daemon 的能力清单, 完整展示 @response 的 JSON 帧, 然后用一句话总结 status 和 permission_denied 的 capability")。
4. 统计 stdin-frame 形态命中数。
5. 跑完恢复 profile.appendSystemPrompt 到 prompt A, 让对照实验不影响其他用户。
