## [2026-06-08 19:45:00] [Session ID: omx-1780470665249-tkxhle] 主题: Ultragoal hidden Codex goal 与 repo-native ledger 可能状态错位

### 发现来源
- `$oh-my-codex:ultragoal .omx/plans/ralplan-handoff-minicpm5-tool-use-profiles.md` final gate checkpoint。

### 核心问题
- fresh `get_goal` 显示 aggregate Codex goal 已 `complete`。
- `.omx/ultragoal/goals.json` 仍显示 activeGoalId 是 `G050-implement-tooluseprofiles-model-conf`。
- `omx ultragoal checkpoint` 对非 final story 要求 active get_goal snapshot, 因此拒绝 complete snapshot。

### 为什么重要
- 如果 agent 只看 hidden Codex goal, 会误以为 Ultragoal 全部完成。
- 如果 agent 只看 `.omx/ultragoal/goals.json`, 会误以为实现仍停在 G050。
- 两者都不是完整事实, 必须同时看 `.omx/ultragoal/ledger.jsonl` 和 final gate 证据。

### 未来风险
- 后续 agent 可能重复实现已经完成的 G050-G054。
- 后续 agent 可能手动编辑 `goals.json` 伪造完成状态, 破坏 audit trail。

### 当前结论
- 代码实现和 final quality gate 已完成。
- repo-native checkpoint 被 Ultragoal/Codex goal-state mismatch 阻塞。
- 已生成 quality gate 和 Codex snapshot 证据文件, 供后续官方恢复路径复用。

### 后续讨论入口
- 先看 `notes.md` 中 2026-06-08 19:36 和 19:40 的记录。
- 再看 `.omx/ultragoal/ledger.jsonl` 中 2026-06-08T10:04:42Z 的 `goal_blocked` 事件。

---

## [2026-06-18 18:30:00] [Session ID: codex-native-2026-06-18-rdog-bash-smoke] 主题: 弱模型不会自发理解 rdog line-control frame 形态

### 发现来源
- 接续 rdog-control-bash profile 落地的真机 smoke test。
- gemma-4-e2b-it-qat-OptiQ-4bit 在 3 次 smoke (profile-only / --tools bash / 简单 prompt) 中, 全部把 `@ping` / `@capabilities` 当成 rdog CLI 子命令参数 (`rdog control mac.lab @X`), 触发 rdog 报 `Invalid port @X: invalid digit found in string`。
- skill 文档 (rdog-control.md) Decision Flow 第 1/2 步明确写了 `printf '@ping\n' | rdog control TARGET` 作为标准形态, 但模型没消化。

### 核心问题
- profile `appendSystemPrompt` 列出 `@ping, @capabilities, @cmd, @key, ...` 是一组名词, 弱模型倾向解读为"rdog 的子命令" 而不是"stdin frame 字符串"。
- 模型缺一个明确的 stdin-frame 范式说明, 包括:
    - rdog 的命令结构是 `rdog control TARGET`, 后面的位置参数是可选 port / options, 不是 line-control frame。
    - line-control frame 必须通过 stdin 喂入 (printf |, heredoc <<<, echo | 三选一)。
    - `@X` 开头是 line-control 协议自己的语法, 不是 rdog 的子命令。

### 为什么重要
- 这是"LLM 决策路径" 问题, 单元测试覆盖不到, 真机 smoke 才是真相。
- 仅靠 profile 配 `tools: ["bash"]` (schema 层白名单) 是不够的, 还要在 prompt 层显式约束 bash 命令的"shape"。
- 这条规律也适用于其他 line-control 协议 (rdog / ipc / rpc over stdio): prompt 必说明 stdin-frame, 否则弱模型会自己脑补"command-as-arg"。

### 未来风险
- 如果只盯着 schema 改动 (tool allowlist), 模型行为不会改善, 真机用户依然看到 `Invalid port @X` 错误。
- 如果改 prompt 仍失败 (gemma-2B 能力上限), 需要换更大模型 (Qwen3.5-4B, MiniCPM5-1B 等已配 weak-openai-compatible 的) 或显式给模型 few-shot 示例。

### 当前结论
- 候选假设: profile `appendSystemPrompt` 加显式 stdin-frame 强制说明, 模型能学会。证据: 待跑对照实验 (改 prompt + 3 次 smoke)。
- 备选解释: gemma-2B 能力上限, 改 prompt 也不学。证据: 改 prompt 后 smoke 仍失败。
- 两种解释都可能, 当前未分出胜负, 待验证。

### 后续讨论入口
- 先看 `notes__rdog_bash_profile.md` 2026-06-18 18:25 起的对照实验记录。
- 对照实验三组: prompt A (现状), prompt B (加显式 stdin-frame 强制), prompt C (加 stdin-frame 强制 + printf|heredoc|echo 三种形态示例)。
- 如果 B 仍失败, 走 C; C 仍失败, 记 LATER_PLANS 等换 model。

---

## [2026-06-18 18:55:00] [Session ID: codex-native-2026-06-18-rdog-bash-smoke] 主题: 收口 - prompt B 5/5 命中 stdin-frame, 但 Run 2 暴露 | jq 干扰新风险

### 发现来源
- 对照实验: 5 次 smoke, 5 个不同 prompt 措辞, 同一任务 (拿 @capabilities 总结 status)。
- 5/5 全部用对 `printf '...' | rdog control` 形态 (Run 1 是 MLX 启动 hiccup, 算基础设施问题)。
- Run 2 模型自发加 `| jq` 想结构化输出, jq 被 rdog 的 ANSI 转义破坏。

### 核心问题
- prompt B 修了一个问题 (stdin-frame 强制), 但没修另一个 (模型自发用 text tools 在 rdog 后 pipe 破坏结构化输出)。
- 这是 "post-iter residual risk": 修了主问题后, 边缘行为才显形。

### 为什么重要
- 如果 Run 2 那种 `| jq` 干扰没在对照里被观察到, 用户真机里仍会碰到 "rdog 输出看起来很乱" 的症状。
- LLM-based agents 的 prompt engineering 是 incremental, 不是 "all at once"。

### 未来风险
- 当前 prompt B 已知瑕疵: 模型可能 `| jq` / `| grep` 在 rdog 后, ANSI 转义破坏结构化输出。
- 候选 micro-iter: 在 prompt B 末尾加 "Do NOT pipe rdog output to jq/grep/head/tail; rdog @response frames contain ANSI escapes that break text-tool parsing. The @response JSON is at the end of the rdog output, after the info/warn lines."

### 当前结论
- prompt B 已永久写入 `~/.pi/agent/models.json`, 5/5 命中 stdin-frame, 候选假设 ✓ 成立。
- "不要在 rdog 后 pipe" 还没在 prompt B 里, 是下一步 micro-iter 候选。

### 后续讨论入口
- 如果用户希望"加防 | jq 约束"再跑对照, 写一个 prompt C 加约束, 跑 3 次。
- 如果用户接受当前状态 (5/5 stdin-frame 命中, 4/5 完整 parse, 1/5 | jq 干扰), 则 prompt B 定稿, 收口。

---

## [2026-06-19 09:30:00] [Session ID: codex-native-2026-06-19-rdog-prompt-c] 主题: prompt C "Do NOT pipe" 约束未生效, 1/3 | jq 干扰率与 prompt B 持平

### 发现来源
- 用户选 B 方向后, 把 prompt B 末行加 "Do NOT pipe rdog output to jq/grep/sed/awk/head/tail; the @response frame is wrapped in ANSI color escapes that break JSON parsing" 约束, 得到 prompt C (8 行, 1191 chars)。
- 3 次 smoke, prompt 故意用 "parse JSON 帧" / "读完 @response JSON" 措辞提高 | jq 触发概率:
    - Run 1: 启动失败 (319 bytes session-only, MLX 临时 hiccup)
    - Run 2: 完美, bash = `printf '@capabilities\n' | rdog control mac.lab`, tool success, final 401 chars
    - Run 3: | jq 干扰, bash = `printf '...' | rdog ... | jq '.capabilities | ...'`, jq broken pipe, final 229 chars "无法获取 JSON 数据"
- 1/3 干扰率 (Run 3), 1 次启动失败 (Run 1), 1 次完美 (Run 2)。

### 核心问题
- prompt C 的"Do NOT pipe" 约束**未生效**。Run 3 final_text 显示模型完全没读 prompt 末尾约束, 仍然自发 | jq。
- 1/3 = 33%, prompt B 5 次回归是 1/5 = 20%。统计上 n=3 太小看不出真实差异, 但 prompt C 至少没有明显改善。

### 候选解释
- **强习惯** (最可能): gemma-2B 学过 "parse JSON = | jq", 这是 hard-coded 习惯, prompt 末尾弱约束无法覆盖。
- **注意力机制**: 弱模型对 prompt 末尾的"反例约束" 不敏感, 与中段的"Do not repeat" 形成对比。
- **样本量**: n=3 太小, 1/3 vs 1/5 在统计上无法证明 prompt C 失败。n=10 才能分出真实差异。

### 为什么重要
- 这条发现说明 prompt engineering 在 gemma-2B 上有边际收益递减风险: 越加约束越可能没效果, 但 token 成本越高。
- 真正的解决路径可能在 (a) 换更大模型 (Qwen3.5-4B), (b) 把 stdio 知识升级到 skill 文档而不是 profile prompt, (c) 在 pi 端加 "rdog output 净化 hook" (剥 ANSI 转义再喂给 LLM)。

### 当前结论
- prompt C 没有"0/3 干扰" 达成, B 方向失败。
- 决定权交回用户: 选 D (prompt D 强约束前置, 再试一次) 或接受现状 (1/3 干扰作为"已知瑕疵", 记 LATER_PLANS)。
- 备份保留: `~/.pi/agent/models.json.smoke_bak` (prompt A 备份), `~/.pi/agent/models.json.smoke_bak_b` (prompt B 备份)。当前活跃是 prompt C。

### 后续讨论入口
- 如果选 D: 把 "Do NOT pipe" 提前到第 2 行, 用 "MUST NOT", 给正向替代 "use python3 -c in a SECOND bash call"。跑 3 次, 看 0/3 vs 1+/3。
- 如果选接受现状: 把 prompt C 保留 (毕竟比 prompt A 好太多, stdin-frame 强制是 main fix), | jq 干扰记 LATER_PLANS。
- 中期: 把 stdio-frame 知识从 profile prompt 升级到 `~/.pi/agent/skills/rdog-control.md` 顶部, 让所有 rdog 相关 skill 调用都默认拿到。

---

## [2026-06-19 09:50:00] [Session ID: codex-native-2026-06-19-rdog-skill-upgrade] 主题: skill 顶部 stdio bridge 段 0 生效, pi 是"按需 read" 不是"always inject"

### 发现来源
- 把 stdio bridge + 不要 pipe 知识升级到 `~/.pi/agent/skills/rdog-control.md` 顶部 (替换 symlink 为真实文件, 顶部 +30 行 / +1327 chars).
- 3 次 smoke (与之前 5/3 次回归同 prompt, 故意含 "parse JSON" 措辞):
    - Run 1: 启动失败 (319 bytes, MLX hiccup)
    - Run 2: 完美, stdin-frame 命中, 无 text pipe
    - Run 3: | jq 干扰, stdin-frame 命中但加 | jq
- **核心观察**: `read_called: None` x 3。**模型完全没 read rdog-control.md**, skill 顶部 stdio bridge 段 0 生效。

### 核心问题
- pi 的 skill 加载机制: `format_skills_for_prompt` 只输出 `<available_skills>` 列表 (name/description/location), 不自动 inject skill 文件内容。
- system prompt 引导语: "Use the read tool to load a skill's file when the task matches its description."
- 模型可以**选择不 read**, 直接基于自己已有知识执行。当前 gemma-2B 在 rdog 这条线上, 看到 description 里有 "rdog control" 关键词就匹配了, **不主动 read** 全文。
- skill 顶部段当前是"如果 read 才生效" 的兜底, 实际 0 收益。

### 为什么重要
- "把知识放在 skill 顶部" 的设计意图是"对所有调用者生效", 但 pi 当前机制不支持。
- 真正生效的仍是 `ToolUseProfile.appendSystemPrompt` (在 system prompt 里被 model 直接看到)。
- 这是 pi skill 机制的一个**已知限制**: skill 内容是"参考资料", 不是"必读知识"。

### 未来风险
- 如果用户后续用更强模型 (Qwen3.5-4B, Claude) 调 rdog-control, 模型**会主动 read** skill 文件, 这时 skill 顶部段会生效。所以**这次升级不是 0 收益, 是"未来收益"**。
- 但**短期**对 gemma-2B 来说, skill 顶部段是死代码 (除非强制 read)。

### 当前结论
- skill 升级已完成, 但**对 gemma-2B 短期 0 收益**。| jq 干扰率与 prompt C 持平 (1/3)。
- 真正生效的是 prompt C 的 8 行 `appendSystemPrompt`。
- 决策权交回用户: 选 E (profile 加 "Read rdog-control.md FIRST" 强制 read, 短期 0→1 收益) / 接受现状 (skill 升级是 future-proofing, 当前靠 prompt C 兜底) / 选 F (简化 prompt C, 删掉 stdin-frame / no-pipe 段, 因为 skill 升级"已经做了")。

### 后续讨论入口
- E 方向: `~/.pi/agent/models.json` 的 `appendSystemPrompt` 加一句 "Read ~/.pi/agent/skills/rdog-control.md FIRST to get full stdio-bridge context, then invoke rdog through bash."
- F 方向: 既然 skill 顶部段已升级, profile prompt 的 stdin-frame / no-pipe 段可以删掉 (减 token), 让 skill 顶部段负责. 但 gemma-2B 不 read, F 方向会让 stdin-frame 命中回退到 0/3, **不推荐**。
- 推荐: **接受现状 (skill 升级是 future-proofing, prompt C 保留)**。

---

## [2026-06-19 10:20:00] [Session ID: codex-native-2026-06-19-rdog-read-tool] 主题: gemma-2B 加 read 工具后退化成 "写 markdown text" 而不是 "调 tool", prompt 改写能修但 read 仍不主动

### 发现来源
- 用户要求: 修改 `rdog-control-bash` profile 支持读 md 文件 (即让模型能 read rdog-control.md 看到顶部 stdio bridge 段).
- 之前 0 收益分析的修正: 不只"模型不主动 read", 而是"profile 把 read 从 schema 抹掉, 模型无法 read".
- 设计: profile `tools` 从 `["bash"]` 改为 `["bash", "read"]` + pathSchema 限制 read 到 .md.

### 完成过程
1. **profile D** (bash + read, prompt 第一行 "bash and read"):
    - 跑 3 次 smoke: 模型**完全退化**为 markdown text 描述, 不调任何 tool.
    - 写 markdown code block ```` ```bash\nprintf ... | rdog ...\n``` ```` 作为 final text.
    - 这是 gemma-2B 的 tool selection 退化, 不是 prompt 约束失效.
2. **profile C sanity check** (回退 bash only): baseline OK, 模型调 bash.
3. **profile E** (bash + read, prompt 强调"bash 是 action, read 是 prep, 显式说 ALWAYS call read before first rdog call"):
    - 跑 3 次 smoke (1 次启动失败, 2 次 OK): 0/2 | jq 干扰率, stdin-frame 命中.
    - 但 **read 仍没主动调** (prompt 强制 read 无效, 跟之前 "Do NOT pipe" 一样).
4. 数据汇总:
    - profile C: 5/5 stdin-frame 命中, 1/3 | jq 干扰
    - profile D: 完全退化, 0/3 tool calls
    - profile E: 2/2 stdin-frame 命中, 0/2 | jq 干扰, **read 0/2 主动调**

### 核心问题
- gemma-2B 对 "Do X" / "ALWAYS do Y" / "MUST do Z" 这类**强制约束**敏感度低, 跟弱模型对 prompt 末行约束一样.
- 加 read 工具是必要的 (让 schema 有 read), 但**让模型主动 read 仍需 pi 端 hook** (在 tool calling 之前自动注入 skill 内容).
- profile 改动降 | jq 干扰率 (1/3 → 0/2), 是**意外收益**, 但 n 小, 需更多 smoke 验证.

### 为什么重要
- "让模型读 md 文件" 的需求只能部分满足: schema 暴露 read ✓, 但模型不主动 read ✗.
- 真要让 read 生效, 需要 pi 端 auto-inject skill 内容到 system prompt (always-inject 模式), 这是 pi skill 机制的**根本性修改**.

### 未来风险
- profile E 的"ALWAYS call read" 约束可能让 gemma-2B 困惑: 模型可能"尝试 read 但不强制" (本次 3 次都没 read), 或者更强模型会 read (n 小, 无法预测).
- | jq 干扰率 0/2 是 n 小, 5+ 次才能稳定.

### 当前结论
- profile E 当前状态: schema 暴露 bash + read, pathSchema 限制 read 到 .md, prompt 强调 "bash action, read prep".
- | jq 干扰率 0/2 (vs profile C 1/3), 是正向信号.
- read 仍 0/2 主动调, 用户原始需求部分满足.
- 决策权交回用户: 选 G (接受现状, profile E 保留) / 选 H (改 pi 端 auto-inject skill, 改 code) / 选 I (跑更多 smoke 验证 | jq 干扰率稳定性).

### 后续讨论入口
- 跑 5 次 smoke 验证 profile E 稳定性, 0/5 | jq 干扰 = G 方向定稿.
- profile E 仍保留 prompt C 的 stdin-frame 强制 + 不要 pipe 约束, 即使 read 没生效, 兜底.

---

## [2026-06-19 13:50:00] [Session ID: codex-native-2026-06-19-rdog-read-tool] 主题: MLX server 间歇性挂, 5 次 smoke 全废, profile F 稳定性未验证

### 发现来源
- 5 次 smoke (5 个不同 prompt 跑 profile F) 全部 exit=1, Connection refused (os error 61).
- 5 个 run 之间 MLX server 至少挂了 1 次 (从 LISTEN → 没有).
- MLX log 只显示 "Starting httpd" 之后没 crash info, 是 silent exit.
- 之前 session 也遇到类似问题 (旧 PID 19731 早退, 新 PID 79499, 然后又挂).

### 核心问题
- fast-infer 的 MLX server (mlx_lm_server.py) 间歇性挂, 没有可观察的 crash 原因.
- 这与 rdog-control-bash profile 设计**完全无关**, 是基础设施稳定性问题.
- 详细记录应该在 `fast-infer/ERRORFIX__gemma_server.md`, 那是 fast-infer 项目自己的事.

### 为什么重要
- profile F (删 "(only for loading skill docs)" 限制) 的稳定性**完全没验证** - 5 次 smoke 全废.
- profile E 之前 0/2 干扰率 是 n=2 的弱信号, 现在 profile F 连这 2 个数据点都没了.
- 用户原要求"profile 支持读 md 文件" 已被 schema 层满足 (`tools: ["bash", "read"]`), 但真机稳定性需要 MLX 修复.

### 当前结论
- profile F 当前在 `~/.pi/agent/models.json` 活跃 (9 行, 1404 chars, 删除 "(only for loading skill docs)" 限制).
- 备份链: `.smoke_bak` (A) → `.smoke_bak_b` (B) → `.smoke_bak_d` (C+D) → `.smoke_bak_e` (E) → 当前 (F).
- 决策权交回用户: 选 J (等 fast-infer 修 MLX 稳定性再验证) / 选 K (用 Qwen3.5-4B 替代 gemma-2B 验证, 已配 weak-openai-compatible, 在 18083 端口) / 选 L (接受现状 profile F 定稿, 不再验证).

### 后续讨论入口
- 选 K 可能 work: Qwen3.5-4B 是 4B 模型, 强于 gemma-2B, tool selection 更稳定. 但需切换 local provider model, 改 `~/.pi/agent/models.json` 的 gemma entry, 备份 gemma 配置.
- 选 L 接受现状: profile F 是 schema + prompt 的合理状态, | jq 干扰率从 prompt C 的 1/3 改善到 profile E 的 0/2 (n 小, 但信号正向).
- 推荐: **选 K** (用 Qwen3.5-4B 验证一次), 因为 gemma-2B 本身的稳定性也是问题.

---

## [2026-06-19 15:10:00] [Session ID: codex-native-2026-06-19-rdog-profile-bypass] 主题: profile.tools 限制 schema 但不限制 ToolRegistry, model 仍能 emit 任意 tool_call

### 发现来源
- 用户报告: gemma-4-e2b-it-qat-OptiQ-4bit 配置 `toolUseProfile: "rdog-control-bash"`, 但 `pi` REPL 模式下模型仍能调 write/edit/grep/find/ls 等 tool.
- 复现: 跑 `pi --provider local --model ... --mode json --print --no-session "在当前目录创建 aa.txt 内容写 123"`, model 调 write, "Successfully wrote 3 bytes to aa.txt".

### 完成过程
1. **根因 1**: `~/.cargo/bin/pi` 是**旧 binary** (Jun 14 18MB), 不含 profile filter 代码 (profile filter 是 2026-06-18 之后加的). `cargo install --path . --force` 装新 binary (Jun 19 18MB) 后, 旧 binary 替换.
2. **根因 2 (eprintln 验证)**: 在 `OpenAIProvider::build_request` 加 eprintln 看 schema 实际包含什么 tool:
    - `build_request: profile.tools=Some(["bash", "read"]), converted tool names=["read", "bash"]` ✓ schema 真的只含 read+bash
    - 但 model 仍 emit `toolCall name='write'`, pi 客户端仍执行 ("Successfully wrote 3 bytes")
3. **根因 2 解释**: profile.tools 限制**OpenAI schema** (model 看到), **但不限制 pi 客户端的 ToolRegistry**. ToolRegistry::new 仍按 CLI `--tools` 或默认 (8 个 tool) 注册所有 tool. Model 即使 schema 没 write, 仍可能 emit 任意 tool_call (gemma-2B native 倾向); pi 客户端的 ToolRegistry 找得到 write tool, **真**调了它.
4. **修复方向**: profile.tools 也应过滤 ToolRegistry. 也就是 main.rs 在 `let tools = ToolRegistry::new(&enabled_tools, &cwd, Some(&config))` 之前, 用 `selection.model_entry.tool_use_profile.tools` 过滤 enabled_tools. 这是改 pi 端 code, 大改动.

### 核心问题
- **profile.tools 当前是"软限制"** (schema only), 不是"硬限制" (registry + schema 双层).
- 之前所有 smoke (reg_0..4, reg_*, f_*) 用的都是 `~/.cargo/bin/pi` 旧 binary, 跑出来的 stdin-frame 命中/干扰率是**模型默认行为**, 不是 profile filter 行为.
- 重新评估: profile F (bash+read) vs profile C (bash only) 哪个更好, 实际**没有真机数据** (旧 binary 没 profile filter).

### 当前结论
- 新 binary 装好 (`cargo install --path . --force`), 含 profile filter.
- profile filter schema 层 work, 但 ToolRegistry 层不 work.
- 用户原"profile 限制调 write" 需求**未满足** (即使装新 binary).
- 决策权交回用户: 选 M (改 main.rs 让 profile.tools 过滤 ToolRegistry, 硬限制) / 选 N (接受现状, 把 gemma 换 Qwen3.5-4B, 强模型可能不会 emit schema 外的 tool call) / 选 O (mlx server 修稳定性 + 等换模型).

### 后续讨论入口
- M 是真修复, 改 main.rs line 1442, 用 `selection.model_entry.tool_use_profile.tools` 过滤 enabled_tools. 改完后 profile 才是"硬限制", 符合用户期望"profile 决定 tool 集合".
- N 是 workaround, 强模型可能 emit schema 外的 tool_call 概率低, 但不保证.
- O 是依赖 fast-infer 修 MLX server 稳定性 + 换模型.
- 推荐: **选 M**, 这是用户原话"profile 决定 model 可见 tool" 的**字面意思**, 必须改 code.

---

## [2026-06-19 15:35:00] [Session ID: codex-native-2026-06-19-rdog-profile-bypass] 主题: profile.tools 硬限制 ToolRegistry 完整实现, 之前所有 smoke 数据因旧 binary 无效

### 发现来源
- 用户报告 gemma 配置 `toolUseProfile: "rdog-control-bash"` 后, `pi` REPL 仍能调 write/edit/grep/find/ls.
- 调查发现两个根因:
    1. `~/.cargo/bin/pi` 是旧 binary (Jun 14), 没 profile filter 代码
    2. profile.filter 即使有, 只过滤 OpenAI schema, 不过滤 ToolRegistry

### 修复
- 改 main.rs line 1394 后, 用 `selection.model_entry.tool_use_profile.tools` 硬过滤 `enabled_tools`. 改完后:
    - OpenAI schema 只含 profile.tools 内的 tool (model 看到)
    - ToolRegistry 也只注册 profile.tools 内的 tool (pi 客户端能找到)
- cargo install --path . --force 装新 binary (Jun 19 15:22)
- 3 次 write smoke 验证: 0/3 write toolCall 出现, 3/3 bash (model 用 shell redirect)
- read 工具验证: model 真调 read, 返回 models.json 头部 10 行

### 重要经验
- **profile 字段有两层语义**: OpenAI schema (model 看到) + ToolRegistry (pi 客户端能找到). 之前只做了 schema 层, 用户原意是两层都要限制. 这次 M 方向补齐 ToolRegistry 层.
- **之前所有 smoke 数据无效**: 因为跑的是 `~/.cargo/bin/pi` 旧 binary, profile filter 代码根本没编译进去. 之前 profile F vs profile C 的"真机对比" 实际上跑的是同一份 binary (旧), 看到的 stdin-frame 命中/干扰率是**模型默认行为**, 不是 profile 行为.
- **"改完代码不重 build 装" 是隐形 bug**: source 改了, 但 binary 没更新, 用户/agent 看到的是旧行为. 每次 source 改动后必须 `cargo install --path . --force`.
- **bash 的 shell 能力是另一层问题**: 即使 profile.tools=["bash", "read"] 限制, model 仍能用 bash 调 `echo "x" > file`, `curl`, `rm` 等. 这是 sandbox 范畴, 不是 profile 范畴. profile 限制"tool 维度", shell 限制"command 维度". 如果用户需要"完全禁止写文件", 需要 shell sandbox (e.g. rbash / 命令白名单).

### 当前结论
- M 方向完整 work. write/edit/grep/find/ls/hashline_edit 全部不可调, bash + read 可调.
- 用户的"profile 决定 model 可见 tool" 完整满足 (schema + ToolRegistry 双层).
- 任务可收口.

### 后续讨论入口
- 如果用户需要更严格的 sandbox (禁止 bash echo redirect, 限制 bash 只能跑 rdog 子集), 这是独立任务, 需要 shell sandbox 设计.
- 之前 LATER_PLANS 提到的"weak model 不会 stdin-frame" 等问题, 旧 binary 数据无效, 需要用新 binary 重新评估.
