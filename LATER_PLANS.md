## [2026-06-05 13:25:00] [Session ID: omx-1780470665249-tkxhle] 后续计划: local-minicpm5 loose 多轮回归

### 背景
- 本轮 focused 小矩阵已经覆盖 `read / grep / find / ls / edit`, 每项 1 次, 结果为 `tool_success=5`。
- 用户之前提到可以后续再跑 10-20 次 loose 回归, 用来观察自然语言弱约束下 MiniCPM5 的随机漂移。

### 建议
- 后续可单独跑 10-20 次 loose 回归, 不与本轮 focused 修复混在一起。
- 统计维度建议包含: no tool call, wrong tool, parser error, tool error, post-tool runaway, repeated same tool, final answer mismatch。
- 如果 loose 下仍有高频失败, 再决定是否要扩展 provider-local guard, 不要提前把 `write` 或任意单工具做成特例。

## [2026-06-05 16:22:21] [Session ID: omx-1780470665249-tkxhle] 状态: loose 多轮回归已开始执行

- 对应原计划: local-minicpm5 loose 多轮回归。
- 当前处理方式: 启用支线上下文 , 单独跑弱约束提示回归并统计漂移率。
- 说明: 为遵守上下文 append-only 记录方式, 这里不删除原条目, 以追加状态说明表示该计划正在本轮落地。

## [2026-06-05 16:23:01] [Session ID: omx-1780470665249-tkxhle] 修正: loose 支线记录名补正

- 上一条记录里的支线名因未加单引号 heredoc 被 shell 命令替换吃掉。
- 正确支线名是 `__minicpm5_loose`。
- 正确任务是单独跑 local-minicpm5 弱约束 loose 回归, 统计漂移率。

## [2026-06-05 16:56:00] [Session ID: omx-1780470665249-tkxhle] 状态: loose 多轮回归已完成

- 原后续计划“local-minicpm5 loose 多轮回归”已在支线 `__minicpm5_loose` 中完成。
- 输出目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-loose-matrix-da30nebi`
- 总体结果: 50 trial, 成功 17, 漂移 33, 漂移率 66%。
- 后续如要继续降低 loose 漂移率, 请查看 `LATER_PLANS__minicpm5_loose.md`。

## [2026-06-08 19:45:00] [Session ID: omx-1780470665249-tkxhle] 后续计划: 恢复 Ultragoal repo-native checkpoint 状态

### 背景
- `get_goal` 当前显示 aggregate Codex goal 已经 `complete`。
- `.omx/ultragoal/goals.json` 仍显示 activeGoalId 为 `G050-implement-tooluseprofiles-model-conf`。
- `omx ultragoal complete-goals` 要求 G050 非 final story checkpoint 时传入 active get_goal snapshot。
- 由于 hidden Codex goal 已 complete, G050/G054 checkpoint 均失败。

### 建议
- 在新的 Codex session 或手动 `/goal clear` 后, 重新运行 `omx ultragoal complete-goals` 并按它的 handoff 做状态恢复。
- 不建议手动编辑 `.omx/ultragoal/goals.json` 伪造 G050-G054 complete, 除非后续明确设计一个官方 reconciliation 命令。
- 已生成可复用证据文件:
  - `.omx/ultragoal/quality-gate-minicpm5-tool-use-profiles.json`
  - `.omx/ultragoal/codex-goal-snapshot-minicpm5-tool-use-profiles.json`


## [2026-06-08 22:42:20] [Session ID: omx-1780470665249-tkxhle] 后续计划: 推送本地 scoped commit

### 背景
- 本地 commit 已创建: `1ae44892 Generalize tool-use profiles for OpenAI-compatible models`。
- 当前环境中的 GitHub 账号对 `Dicklesworthstone/pi_agent_rust` 均无 push 权限。
- 当前 `main...origin/main` 显示 `[ahead 1, behind 3]`。

### 后续动作
- 使用有 `push=true` 权限的 GitHub 身份。
- 在干净 worktree 或临时 worktree 中基于最新 `origin/main` 承载 commit `1ae44892`。
- 推送 `main`, 并按项目规则同步 `main:master`。

## [2026-06-09 16:29:00] [Session ID: omx-1780470665249-tkxhle] 状态: 推送本地 scoped commit 已完成

- 原后续计划“推送本地 scoped commit”已完成。
- 最终不是推送到 `origin/main`, 而是按用户要求推送到 `my/main`。
- 远端 `my/main` 当前 commit: `e0cc86895112f5600cb25c96ea5d17a74b39920d`。
- `my` fork 没有 `master` ref, 本轮没有额外创建 legacy `master` 分支。

## [2026-06-18 16:45:31] [Session ID: codex-native-2026-06-18-gemma4-bash-only] 后续计划: 让 ToolUseProfile 也能锁工具白名单

### 背景
- 用户用 `pi --provider local --model /Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/gemma-4-e2b-it-qat-OptiQ-4bit` 时, 只想保留 `bash` 工具。
- 现状:
  - `Cli::tools` 默认是 `read,bash,edit,write,grep,find,ls,hashline_edit` (`src/cli.rs:418`).
  - 临时解决: `pi ... --tools bash` 让 `Cli::enabled_tools()` 返回 `["bash"]`, 经 `ToolRegistry::new` (`src/tools.rs:2652-2683`) 只 push `BashTool`, `default_system_prompt` (`src/app.rs:267-320`) 也只渲染 bash 段。
  - 但每次命令行都得加 `--tools bash` 才生效, `~/.pi/agent/models.json` 里的 gemma-4-e2b-it-qat-OptiQ-4bit entry 也无法锁定"只剩 bash"。
- 真相源现状: `ToolUseProfile` (在 `src/models.rs:184-218`) 只控制 `appendSystemPrompt` / `pathSchema` / `argumentRepair` / `postToolGuard`, **不控制 tool 列表**。`append_tool_use_profile_system_prompt` (`src/app.rs:212-235`) 只往 system prompt 末尾追加内容, 早退条件是 `enabled_tools.is_empty()` 而不是 profile 决定的。

### 用户偏好
- "如果用户要求把 model-specific hardening 改成更通用的机制, 默认先找可配置真相源; 优先走 `toolUseProfiles` / `models.json`, 不要继续堆 provider/model 字符串分支。"
- "改良胜过新增", 但 profile 当前确实没这条 axis, 这次不是"重复堆", 是"补齐 axis"。

### 建议
- 在 `ToolUseProfileConfig` (`src/models.rs:184-191`) 加一个可选字段 `enabled_tools: Option<Vec<String>>`。
- 在 `ToolRegistry` 构造的调用链 (e.g. `src/main.rs:1442`, `src/sdk.rs:1777`, `src/agent.rs:9237`) 增加"如果当前 model 解析出的 profile 声明了 `enabled_tools`, 就用 profile 的列表去覆盖 CLI 给的"或者"按组合策略合并"。
  - 注意: `ToolUseProfile` 还在 `Agent::new_with_options` 等地方被 `tool_use_profile` 字段消费 (`src/agent.rs:9087-9107`), 改 schema 必须同步更新解析路径。
- 在 `models.json` (`~/.pi/agent/models.json`) 给 `local.gemma-4-e2b-it-qat-OptiQ-4bit` 挂一个 `toolUseProfile: "bash-only"` 之类的名字, 这样不传 `--tools` 也能落到只剩 bash。
- 验证: 写一个独立单测覆盖 `ToolUseProfile::enabled_tools_override` + 一个端到端断言 (e.g. `pi --provider local --model .../gemma-4-e2b-it-qat-OptiQ-4bit --print` 输出的 system prompt 里 available tools 段只有 bash)。

### 风险
- CLI `--tools` 与 profile `enabledTools` 同时给, 谁优先, 默认怎么合并, 需要明确语义 (优先 profile? 还是必须两者一致? 还是并集/差集?)。
- 旧 profile (e.g. `weak-openai-compatible`, `minicpm5-optiq-strict-write`) 不带 `enabledTools`, 行为应保持不变 (Option 默认 None 走原路径)。
- `agent.rs:9087-9107` 那条 path 在 `append_tool_use_profile_system_prompt` 之后, 需要确认新字段不会让 prompt marker 重复 (现在有 idempotence 检查, 新加 path 要保证不破坏)。

### 当前结论
- 本次任务不落地 schema 改动, 走 `pi ... --tools bash` 临时路径。
- 后续如果用户希望"换 model 就自动锁工具", 再开一个独立任务做这条 schema 扩展 + `models.json` 登记 + 单测。

---

## [2026-06-19 09:45:00] [Session ID: codex-native-2026-06-19-rdog-prompt-c] 后续计划: 解决 gemma-2B 在 rdog 后自发 | jq 解析的强习惯

### 背景
- rdog-control-bash profile 的 stdin-frame 强制 (prompt B) 已落地, 5/5 命中 `printf '...' | rdog control TARGET` 形态。
- 但模型在"parse JSON 帧" 任务上有自发 `| jq` 的强习惯, prompt C 末行 "Do NOT pipe to jq/grep/sed/awk/head/tail" 约束未生效 (1/3 干扰率与 prompt B 持平)。
- 候选根因:
    1. gemma-2B 学过 "parse JSON = | jq", hard-coded 习惯, prompt 弱约束无法覆盖
    2. 弱模型对 prompt 末行约束注意力不够
    3. 样本量 n=3 + n=5 太小, 统计上无法证伪
- 已记录到 `EPIPHANY_LOG.md` "prompt C 'Do NOT pipe' 约束未生效" 段。

### 后续动作
- 候选方向 A: prompt D (把约束前置第 2 行 + MUST NOT + 正向引导 python3), 跑 3 次, 验证 0/3 干扰。
- 候选方向 B: 把 stdio-frame + "不要 pipe 给 text tools" 知识升级到 `~/.pi/agent/skills/rdog-control.md` 顶部, 让所有 rdog 相关 skill 调用都默认拿到 (而不是只 profile prompt)。
- 候选方向 C: pi 端 hook — 在 `bash` tool 的 result 里自动 strip ANSI 转义, 模型看到的 stdout 是干净的。
- 候选方向 D: 换更大模型 (Qwen3.5-4B-OptiQ-4bit 已配 weak-openai-compatible, 在 local provider), 用 4B 模型重跑回归, 看 | jq 干扰率是否降为 0。

### 决策原则
- A 是 prompt engineering 边际递减, 不优先。
- B 改 skill 文档, 范围小, 推荐。
- C 改 pi 代码, 与用户偏好"配置 = 真相源" 不一致, 除非 B 也失败。
- D 等用户自己决定模型选择, 不在 pi 端硬切。

### 当前状态
- prompt C 在 `~/.pi/agent/models.json` 活跃, 备份链: `.smoke_bak` (A) → `.smoke_bak_b` (B) → 当前 (C)。
- 决策权在用户: 选 A / B / C / D 任一方向继续, 或接受现状 (1/3 干扰作为已知瑕疵)。

---

## [2026-06-19 10:05:00] [Session ID: codex-native-2026-06-19-rdog-skill-upgrade] 后续计划: 监控 "skill 顶部段何时对 gemma-2B 生效" 与 "pi skill 强制 read 机制设计"

### 背景
- 升级 `~/.pi/agent/skills/rdog-control.md` 顶部加 stdio bridge 段 (+30 行 / +1327 chars), 替换 symlink 为真实文件。
- 真机 smoke 验证: gemma-2B 3 次都不 read rdog-control.md, skill 顶部段 0 收益。
- pi 当前 skill 加载是"按需 read" 不是"always inject", 这是根本原因。
- 详细记录见 `EPIPHANY_LOG.md` "skill 顶部 stdio bridge 段 0 生效" 段。

### 后续动作
- 候选方向 E: profile `appendSystemPrompt` 加一句 "Read ~/.pi/agent/skills/rdog-control.md FIRST to get full stdio-bridge context, then invoke rdog through bash.", 强制 read。短期把 skill 顶部段从 0 收益变成 1 收益, 但增加一个 read 步骤, gemma-2B 可能不执行 read 然后 bash。
- 候选方向 F: 简化 prompt C, 删掉 stdin-frame / no-pipe 段, 让 skill 顶部段负责。**不推荐**: gemma-2B 不 read, F 方向会让 stdin-frame 命中回退到 0/3。
- 候选方向 G: 监控更强模型 (Qwen3.5-4B-OptiQ-4bit, 已配 weak-openai-compatible) 跑 rdog-control 时是否主动 read skill 文件, 如果是, 删掉 prompt C 的冗余段。
- 候选方向 H: 提 PR 给 pi_agent_rust 改进 skill 机制 (例如 "skill 内容 always inject 到 system prompt"), 长期治理。

### 决策原则
- E 增加步骤, 不优先。
- F 回退当前收益, 绝对不推荐。
- G 监控, 0 成本。
- H 长期, 不在当前任务范围。

### 当前状态
- skill 升级完成, 备份在 `~/.pi/agent/skills/rdog-control.md.skill_backup` (可恢复)。
- profile prompt C 保留, 仍生效 (5/5 stdin-frame 命中)。
- | jq 干扰率 1/3 (短期无法降到 0, 模型强习惯)。
- 接受现状, 不擅自做 E/F。

## [2026-06-19 19:00:00] [Session ID: codex-native-2026-06-19-continuous-learning] 后续计划: shell sandbox 设计 (rdog profile 之外)

### 背景
- `__rdog_bash_profile` 阶段 6 + M 方向已完成: profile.tools 真正决定 ToolRegistry + OpenAI schema 双层。
- 但即使 profile.tools=["bash", "read"], model 仍能用 bash `echo "x" > file`, `curl`, `rm` 等, 写盘 / 联网 / 删文件都直接通过 shell, 绕开 profile 限制。
- profile 限制"tool 维度", shell 限制"command 维度", 是 sandbox 范畴。
- 用户如果需要"完全禁止写文件" / "bash 只能跑 rdog 子集" / "禁止 curl 联网", 需要独立 shell sandbox 设计 (e.g. rbash / 命令白名单 / seccomp / nix-style)。

### 建议
- 不在当前主线 scope 落地, 留作独立任务。
- 如果用户后续真要做, 推荐先设计"rdog 专用 shell wrapper" 而不是 rbash (兼容性最好)。
- 与 profile.tools 关系: shell sandbox 在 bash tool execute 入口拦截, profile.tools 在 tool 注册层拦截, 两层独立。

## [2026-06-19 19:00:00] [Session ID: codex-native-2026-06-19-continuous-learning] 后续计划: 防止 "code 改了但 binary 没更新" 的隐形 bug

### 背景
- `__rdog_bash_profile` 阶段 5 完成时, source 改了 (profile.tools 字段 + OpenAI 过滤), 但 `~/.cargo/bin/pi` 是旧 binary (Jun 14), 实际跑的还是旧代码, 导致所有 smoke 数据无效。
- 反复出现的踩坑: agent 改完 source 跑测试, 实际跑的是旧 binary。

### 建议
- 短期: 改完 `src/**/*.rs` 后必须 `cargo install --path . --force`, 并用 `ls -la ~/.cargo/bin/pi` 验证 mtime > source mtime。
- 长期: 可以加一个 wrapper 脚本, 在 `pi` 命令前自动检测 source mtime vs binary mtime, 不一致就提示重 build。
- 也可以在 README / AGENTS.md 加一个 "改完代码后必做清单" 段落, 把这条提到必做项高度。

## [2026-06-19 19:00:00] [Session ID: codex-native-2026-06-19-continuous-learning] 后续计划: 清理 LATER_PLANS.md 中已完成的过期条目

### 背景
- LATER_PLANS.md 2026-06-18 16:45:31 "后续计划: 让 ToolUseProfile 也能锁工具白名单" 已被 `__rdog_bash_profile` 阶段 5+6 完成 (profile.tools 字段 + M 方向硬过滤已落地)。
- LATER_PLANS.md 2026-06-05 13:25:00 "后续计划: local-minicpm5 loose 多轮回归" 已被 `__minicpm5_loose` 完成 (50 trial, drift 66%)。

### 建议
- 下次主线收尾时, 把这两条从 LATER_PLANS.md 删除或加 "[已完成 by <支线>]" 标记。
- 持续学习 skill 不主动删除主线文件, 只追加索引; 清理权限留给主线 agent。

## [2026-08-01 23:50:00] [Session ID: root-merge-590d618] 遗留: 8 个无法在本次修复的测试失败

1. orchestrate_* (5 个, bench_schema): 需要真实 perf 运行生成 extension Criterion
   证据 (bd-2zcs5.51 的 ext_cold_load_simple_p95 / policy_eval_p99 / protocol_parse_p99)。
   跑真实 perf (release build + criterion) 后可满足 preflight/staging 门禁。
2. test_combinatorial_slash_commands / test_slash_command_differential_harness /
   test_certification_artifacts_fail_closed (3 个): pi-mono legacy 代码不完整,
   packages/coding-agent/src/core/tools/ 目录在 git 中从未存在, 差分 runner
   无法启动。需补齐 pi-mono 缺失模块或调整差分测试的依赖。
3. 全量测试运行会改写 repo 内产物文件 (tests/artifacts、tests/ext_conformance/reports、
   tests/full_suite_gate 等约 40 个): 建议将产物目录纳入 .gitignore 或
   建立"跑完 restore"的约定, 避免提交噪音。
4. pi-mono 依赖安装: 本机需 npm ci --ignore-scripts + 手动 esbuild install
   (pnpm workspace 布局不链接依赖, npm 的 esbuild postinstall 失败)。
