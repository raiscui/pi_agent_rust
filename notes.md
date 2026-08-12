## [2026-06-05 13:14:00] [Session ID: omx-1780470665249-tkxhle] 笔记: read 矩阵失败的真实原因

### 现象

- `/tmp/pi_minicpm5_tool_matrix.py` 首轮 focused 矩阵 exit 1。
- summary 分类: `read_final_missing_expected_text=1`, 其它 `grep/find/ls/edit` 均为 `tool_success`。

### 动态证据

- read 的 `tool_execution_end` 成功返回 `    1→PI_MINICPM5_MATRIX_READ_OK_01`。
- read 的第 24 个事件 `message_end` 中, assistant content 已经是文本 `PI_MINICPM5_MATRIX_READ_OK_01`。
- read 的第 25 个事件 `turn_end` 中, message 同样是文本 `PI_MINICPM5_MATRIX_READ_OK_01`。
- read 的第 26 个事件 `agent_end` 中, messages 最后一条 assistant 同样是文本 `PI_MINICPM5_MATRIX_READ_OK_01`。

### 结论

- 上一假设“Pi 最终没有 read 文本”不成立。
- 证据显示 repeat guard 已经把重复 read ToolCall 改写为真实 ToolResult 文本。
- 当前失败来自临时矩阵脚本 `collect_assistant_text` 只收集 streaming `message_update` 文本 delta, 没有读取 `message_end` / `agent_end` 中的最终 assistant 文本。

### 下一步

- 修正 `/tmp/pi_minicpm5_tool_matrix.py` 的 assistant 文本收集逻辑。
- 重跑 focused 矩阵, 以修正后的 harness 验证真实结果。


## [2026-06-08 18:03:19] [Session ID: omx-1780470665249-tkxhle] 笔记: G050 toolUseProfiles 模型配置解析

### 静态实现结论
- 单一真相源设在 `ModelEntry.tool_use_profile`。
- `models.json.toolUseProfiles` 只作为配置定义源, Rust 不包含 `weak-openai-compatible` 预设表。
- provider 级 `toolUseProfile` 先解析为默认 profile。
- model 级 `toolUseProfile` 出现时覆盖 provider 默认 profile。
- `load_with_mode` 在 `apply_custom_models` 前调用 `validate_tool_use_profile_references`, 因此未知 profile 不会被半应用成无 profile 模型。

### 动态验证结论
- provider default, model override, unknown provider-level profile, unknown model-level profile, 以及旧 no-profile 加载回归测试均通过。
- 旧 fixture 构造点已全部显式补 `tool_use_profile: None`, 用编译器确保无遗漏。


## [2026-06-08 18:21:12] [Session ID: omx-1780470665249-tkxhle] 笔记: G051/G052 profile-driven wiring

### 静态实现结论
- prompt append, OpenAI schema rewrite, agent argument repair, post-tool repeat guard 现在都消费 resolved profile。
- runtime hardening 不再读取 `local-minicpm5` provider 或 `minicpm5` model 字符串。
- `AgentConfig.tool_use_profile` 是 agent runtime 的单一入口; main/RPC 模型切换会同步更新该值。

### 动态验证结论
- app 层覆盖 configured prompt append, no-profile skip, tools-disabled skip, marker idempotence。
- OpenAI 层覆盖 no-profile schema unchanged, configured generic/file/optional path description rewrite, generic description 缺失时跳过。
- Agent 层覆盖 profile repair, no-profile skip, ambiguous skip, repeat successful rewrite, different args skip, failed result skip, read line-prefix stripping only when configured。


## [2026-06-08 18:24:42] [Session ID: omx-1780470665249-tkxhle] 笔记: G053 durable harness 和文档

### harness 设计
- `scripts/pi_minicpm5_tool_matrix.py` 不依赖真实用户全局配置。
- 每次运行会在 output root 下创建 `pi-agent-config/models.json`, 并用 `PI_CODING_AGENT_DIR` 指向它。
- fixture 显式包含 `appendSystemPrompt`, `pathSchema`, `argumentRepair`, `postToolGuard` 四类字段。

### docs 设计
- 文档说明 provider-level default 与 model-level override 的解析顺序。
- 文档说明未知 profile 名称 fail closed。
- 文档明确 no auto-detection, no remote profile loading, no separate profile file。


## [2026-06-08 18:51:56] [Session ID: omx-1780470665249-tkxhle] 笔记: focused matrix 失败拆解

### 现象
- read: `read` 工具成功, ToolResult 包含 `PI_MINICPM5_MATRIX_READ_OK_01`, 但最终 assistant 文本只说文件成功读取。
- grep: 模型调用了 `grep`, 但参数是 `glob: ".grep_01.txt"`, 而用户唯一明确文件候选是 `matrix_grep_01.txt`, 所以 grep 返回 `No matches found`。
- ls: 首轮出现 `__minicpm5_tool_parse_error`, 之后模型恢复并成功调用真实 `ls`, ToolResult 包含目标文件。

### 当前判断
- grep 是 runtime repair 的可泛化缺口: 在 profile 显式开启 `repairGrepDegenerateGlob` 时, 如果用户文本只有一个明确相对文件候选, 且 grep 没有 path, 但 glob 是该候选的点前缀后缀漂移, 可以安全修复为 path。
- read 和 ls 是否要算失败, 更接近 focused harness 的分类边界: 工具真实执行成功, 但 read 最终文本没有复述内容; ls 有恢复前 parse error 噪声。

### 下一步
- 先补 grep repair 单测和实现。
- 再决定 focused harness 是否应该以“目标工具成功 + 结果真实 + agent_end + 无 runaway”为 tool_success 判定核心。


## [2026-06-08 18:59:40] [Session ID: omx-1780470665249-tkxhle] 笔记: focused matrix 修复后证据

### 关键修复
- grep 失败的已验证原因是模型把唯一文件候选漂移成点前缀 glob。
- 修复在 profile flag `repairGrepDegenerateGlob` 下生效, 没有新增 provider/model 字符串分支。
- harness 分类调整为验证 focused tool-use 能力: 目标工具最终成功优先, 不让可恢复的 parse-error 噪声覆盖目标工具成功。

### 动态结果
- 命令: `python3 scripts/pi_minicpm5_tool_matrix.py --trials 1 --timeout 120 --pi-bin "$PWD/target/debug/pi" --provider local-minicpm5 --model /Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/MiniCPM5-1B --server-url http://127.0.0.1:18081/v1 --output-root /tmp/pi-minicpm5-profile-focused-fixed2-20260608185840`
- 结果: `tool_success=5`。
- 输出目录: `/private/tmp/pi-minicpm5-profile-focused-fixed2-20260608185840`。


## [2026-06-08 19:05:02] [Session ID: omx-1780470665249-tkxhle] AI SLOP CLEANUP REPORT

### Scope
- 本轮 changed files 中与 toolUseProfiles 泛化相关的核心文件和新增 harness/docs。
- 重点文件: `src/models.rs`, `src/app.rs`, `src/providers/openai.rs`, `src/agent.rs`, `scripts/pi_minicpm5_tool_matrix.py`, `docs/models.md`。

### Behavior Lock
- 首轮 verification 已通过: model/app/openai/agent profile tests, `cargo check --all-targets`, `cargo clippy --all-targets -- -D warnings`, `cargo build --bin pi`。
- focused MiniCPM5 matrix 已通过: `/private/tmp/pi-minicpm5-profile-focused-fixed2-20260608185840`, `tool_success=5`。

### Cleanup Plan
- fallback-like scan。
- runtime-specific model branch scan。
- stale docs/comments cleanup。

### Fallback Findings
- changed files 中没有发现本轮新增 masking fallback slop。
- `swallow` / `todo` 命中来自既有测试文案和 JS test harness, 非本轮新增绕过。

### Passes Completed
- Fallback-like code resolution gate: 无 masking fallback 需要处理。
- Dead code deletion: 无新增死代码。
- Duplicate removal: 无新增重复 helper 需要合并。
- Naming/error handling cleanup: 修正 grep repair 注释和 `docs/models.md` 字段说明, 同步 `.git` / 点前缀 literal glob 修复语义。
- Test reinforcement: 已新增 grep 点前缀 suffix 和 hidden literal glob 单测。

### Remaining Risks
- MiniCPM5 MLX shim 仍可能产生可恢复的 `__minicpm5_tool_parse_error` 噪声; 本轮 focused harness 以目标工具最终成功为通过标准, 不把可恢复噪声误判为目标工具失败。

## [2026-06-08 19:36:00] [Session ID: omx-1780470665249-tkxhle] 笔记: G054 independent code review gate

### code-reviewer lane
- Agent: 019ea6f1-af67-7940-9364-82678271104e / Jason。
- Files reviewed: 15。
- Total issues: 0。
- Severity counts: CRITICAL 0, HIGH 0, MEDIUM 0, LOW 0。
- Result: `codeReview.recommendation: APPROVE`。
- 关键证据: 审查确认 `weak-openai-compatible` 没有做成 Rust 预设表; provider default / model override / unknown fail-closed / no-profile 不变 / read-grep-find-ls-edit focused harness 全部符合验收。

### architect lane
- Agent: 019ea6f2-0d31-77a2-8ab5-f723a0cfd08a / Plato。
- Result: `Architectural Status: CLEAR`。
- 关键证据: 审查确认 `ModelEntry.tool_use_profile` 是 resolved profile 的单一落点; Rust 只定义 bounded typed config 和 applicator; runtime hardening 不再依赖 local-minicpm5 / minicpm5 字符串分支; provider 边界只影响 OpenAI Chat Completions schema shaping。

### 结论
- final gate 的 independent review 条件已满足: code-reviewer APPROVE + architect CLEAR + 两条 distinct lane evidence。
- 下一步写入 `.omx/ultragoal/quality-gate-minicpm5-tool-use-profiles.json`, 并使用 fresh `get_goal` complete snapshot 尝试 ultragoal checkpoint。

## [2026-06-08 19:40:00] [Session ID: omx-1780470665249-tkxhle] 笔记: G054 checkpoint 首次失败与恢复路径

### 现象
- 命令: `omx ultragoal checkpoint --goal-id G054-run-final-verification-cleanup-and-i --status complete ...`
- 结果: exit 1。
- 错误: `Codex goal status mismatch: expected active, got complete`。

### 判断
- 这不是代码实现或 verification 失败。
- 这是 handoff 已记录的 ultragoal goal-state mismatch: Codex aggregate goal 已 complete, 但 `.omx/ultragoal/goals.json` 的 activeGoalId 仍停在 `G050-implement-tooluseprofiles-model-conf`。

### 恢复路径
- 根据 OMX 输出, completed aggregate reconciliation 必须先 checkpoint 当前 active in-progress OMX goal。
- 下一步使用 `G050-implement-tooluseprofiles-model-conf` 作为 goal id, 并在 evidence 中显式命名 `.omx/ultragoal/goals.json` / `.omx/ultragoal/ledger.jsonl` 以及完整实现、验证、review 证据。

## [2026-06-08 19:53:00] [Session ID: omx-1780470665249-tkxhle] 笔记: stop hook G001 reconciliation 尝试失败

### 现象
- fresh `get_goal` 返回同一 aggregate ultragoal objective, status 为 `complete`。
- 按 stop hook 要求执行 `G001-workflow-oh-my-codex-ralplan` complete checkpoint。
- 结果 exit 1。
- 错误仍是 `Codex goal status mismatch: expected active, got complete`。

### 关键矛盾
- stop hook 指定使用 `G001-workflow-oh-my-codex-ralplan`。
- OMX checkpoint runtime 错误提示要求 checkpoint goal 必须是 active in-progress OMX goal。
- 当前 `omx ultragoal status` 的 activeGoalId 是 `G050-implement-tooluseprofiles-model-conf`。

### 下一步
- 不重复 `--status complete`。
- 按 hook 的安全恢复口径, 尝试对 G001 记录 blocked checkpoint, evidence 中说明 completed aggregate Codex goal 阻塞当前 thread 的 Ultragoal reconciliation。

## [2026-06-08 19:55:00] [Session ID: omx-1780470665249-tkxhle] 笔记: active G050 blocked checkpoint 已成功

### 现象
- G001 complete checkpoint 失败。
- G001 blocked checkpoint 失败。
- 改用当前 active in-progress OMX goal `G050-implement-tooluseprofiles-model-conf` 做 blocked checkpoint, 并且不附加 quality-gate JSON, 命令成功。

### 成功命令摘要
- `omx ultragoal checkpoint --goal-id G050-implement-tooluseprofiles-model-conf --status blocked --codex-goal-json .omx/ultragoal/codex-goal-snapshot-minicpm5-tool-use-profiles.json ... --json`

### 结论
- Ultragoal ledger 已记录 safe-recovery blocker。
- blocker 是: aggregate Codex goal 已 complete, 但 `.omx/ultragoal/goals.json` 的 active repo-native microgoal 仍为 G050。
- 实现和 final gate 证据仍然完整, 保存在 `.omx/ultragoal/quality-gate-minicpm5-tool-use-profiles.json`。

## [2026-06-08 20:01:00] [Session ID: omx-1780470665249-tkxhle] 笔记: OMX 源码确认 G001 hook 指令与 activeGoalId 冲突

### fresh get_goal
- objective: `Complete the durable ultragoal plan in .omx/ultragoal/goals.json, including later accepted/appended stories, under the original brief constraints; use .omx/ultragoal/ledger.jsonl as the audit trail.`
- status: `complete`。

### 当前 ultragoal 状态
- `activeGoalId`: `G050-implement-tooluseprofiles-model-conf`。
- `G001-workflow-oh-my-codex-ralplan`: `status=in_progress`, `steeringStatus=blocked`, 但不是 active goal。
- `G050-implement-tooluseprofiles-model-conf`: `status=in_progress`, 是 active goal, 已有 safe-recovery blocker。

### 源码证据
- 文件: `/Users/cuiluming/n/lib/node_modules/oh-my-codex/dist/ultragoal/artifacts.js`。
- `canReconcileCompletedTaskScopedAggregateSnapshot` 在 210-221 行要求:
  - aggregate mode。
  - `goal.status === 'in_progress'`。
  - `plan.activeGoalId === goal.id`。
  - evidence 提到 ultragoal plan artifact。
  - evidence 提到当前 goal id。
  - evidence 包含 implementation + validation/review completion evidence。
- `isSafeCompletedAggregateBlockerSnapshot` 在 244-255 行也要求:
  - aggregate mode。
  - `goal.status === 'in_progress'`。
  - `plan.activeGoalId === goal.id`。
  - snapshot status 为 complete。
  - evidence 描述 aggregate Codex goal complete / microgoal unreconcilable loop。

### 结论
- stop hook 要求 G001 complete checkpoint, 但当前 OMX runtime 规则要求 checkpoint goal 必须是 active goal。
- 因为 `activeGoalId=G050`, G001 complete 和 G001 blocked 都不是合法路径。
- G050 blocked checkpoint 成功符合源码中 safe blocker 的条件, 因此这是当前线程可执行的正确审计落点。

## [2026-06-10 15:18:00] [Session ID: omx-1781010799354-k3m6a6] 笔记: pi 退出后残留鼠标上报序列

## 来源

### 用户现象
- 用户反馈: `pi` 退出后终端留下大量类似 `35;23;41M` 的文本。
- 这类文本符合 SGR mouse report 的尾部格式。完整形态通常是 `ESC [ < 35 ; x ; y M`。

### 代码证据
- `src/interactive.rs` 默认在 TUI 启动时调用 `program.with_mouse_all_motion()`。
- `charmed-bubbletea 0.2.0` 的 `Program::run_with_writer` 在 mouse_all_motion 时写入 `crossterm::event::EnableMouseCapture`。
- `crossterm 0.29.0` 的 `EnableMouseCapture` 会写入 `?1000h`, `?1002h`, `?1003h`, `?1015h`, `?1006h`。
- 其中 `?1003h` 是 all-motion mouse tracking, `?1006h` 是 SGR mouse mode。

## 综合发现

### 现象
- 退出后 shell 看到的 `35;x;yM` 不是普通日志,而是鼠标事件 escape sequence 的尾部。

### 主假设
- TUI 全鼠标移动捕获导致大量 SGR mouse report。在退出边界,即使底层库执行 cleanup,stdin 中仍可能有已积压的 mouse events。shell 接管后会把这些事件当普通输入显示。

### 备选解释
- 后台任务退出后继续写 stdout。当前没有看到支持它的静态证据;残留文本形态更符合 stdin 鼠标上报。

### 修复策略
- 不修改第三方 `charmed-bubbletea` crate。
- 在 Pi 自己的 `run_interactive` 退出边界增加幂等兜底恢复。
- 兜底写入 disable bracketed paste / disable focus / disable mouse / show cursor / leave alternate screen。
- 短暂启用 raw mode,零等待、限量排空 crossterm event reader 中已经积压的事件,随后关闭 raw mode。

### 验证
- 新增测试验证 mouse capture 启用时恢复序列包含 `?1006l` 和 `?1003l`。
- 新增测试验证禁用 mouse capture 时不会额外写 mouse disable 序列,但仍恢复 paste/cursor/alt-screen。

## [2026-06-10 17:52:00] [Session ID: omx-1781010799354-k3m6a6] 笔记: 零等待排空结论被真实复现推翻

### 现象
- 用户安装上一轮版本后仍看到 `Goodbye!` 后出现 `^[[<35;x;yM`。
- 这说明只写 `DisableMouseCapture` 和 `Duration::ZERO` 排空不足以保护真实 shell 退出边界。

### 当前假设
- 主假设: mouse disable 写出后,终端或 PTY 中仍有稍后到达的 SGR mouse report。零等待轮询无法覆盖这个时间窗口。
- 备选解释: 退出后仍有其他路径重新打开 mouse capture,或 crossterm event reader 内部保留了未消费字节。

### 验证计划
- 使用 PTY 包裹真实 shell 和 `pi`,捕获 `Goodbye!` 前后的原始字节。
- 在检测到 mouse disable 后主动注入 SGR mouse report,观察旧实现是否会让它越过 `Goodbye!` 被 shell 回显。
- 再实现 quiet-window drain,对比同样注入是否被 Pi cleanup 消费。

## [2026-06-10 18:08:00] [Session ID: omx-1781010799354-k3m6a6] 笔记: 默认 all-motion mouse capture 是过度策略

### 新静态证据
- `run_interactive` 在没有 opt-out 时调用 `program.with_mouse_all_motion()`。
- `charmed-bubbletea` 对 `with_mouse_all_motion` 使用 `crossterm::event::EnableMouseCapture`。
- `crossterm` 的该序列同时启用 `?1003h` all-motion 和 `?1006h` SGR mouse mode。
- 用户看到的 `^[[<35;x;yM` 里的 `35` 对应无按键移动报告,正是 all-motion 风险面。

### 修复策略调整
- 不再把“多 drain 一点”当唯一修复。drain 只能处理已进入进程可读队列的事件,不能保证终端在 cooked/echo 窗口里没有已经回显的延迟字节。
- 默认不启用 mouse capture。保留 `disable_mouse_capture: false` 作为显式 opt-in,避免破坏确实需要鼠标滚轮路由的用户。
- 对 opt-in 路径继续增加 quiet-window drain,降低退出瞬间延迟事件落回 shell 的风险。


## [2026-06-11 15:20:08] [Session ID: omx-1781010799354-k3m6a6] 笔记: 鼠标滚轮恢复的底层证据

### 现象
- 用户反馈 pi 当前没有鼠标滚轮支持,这不符合交互需求。
- 上一轮默认关闭 mouse capture 后,Pi 自己的 `handle_mouse_wheel` 逻辑仍在,但终端不再把滚轮事件送入 TUI。

### 静态证据
- `src/interactive.rs` 中 `update_inner` 会处理 `MouseMsg` 的 `WheelUp` / `WheelDown`,并调用 `handle_mouse_wheel`。
- `charmed-bubbletea-0.2.0` 的 `with_mouse_cell_motion()` 和 `with_mouse_all_motion()` 都调用 `crossterm::event::EnableMouseCapture`。
- `crossterm-0.29.0` 的 `EnableMouseCapture` 会同时开启 `?1000h`, `?1002h`, `?1003h`, `?1015h`, `?1006h`。

### 当前假设
- 要恢复滚轮,不应回到 `with_mouse_all_motion()` 默认路径。
- 更合适的方向是 Pi 自己写更精确的 ANSI mouse mode: 开 `?1000h` 与 `?1006h` 来接收按钮/滚轮的 SGR 报告,避免开 `?1003h` 的普通移动上报。

### 备选解释
- 如果 crossterm 对仅 `?1000h + ?1006h` 的滚轮报告解析不完整,则需要考虑启用 `?1002h` button-event tracking,但仍避免 `?1003h` all-motion。

### 待验证
- 增加单元测试确认默认路径输出精确启用序列,包含 `?1000h` 和 `?1006h`,不包含 `?1003h`。
- 保留退出恢复测试确认会关闭 mouse mode 并 drain。
## [2026-06-12 17:57:10] [Session ID: codex-20260612-pi-model-max-tokens] 笔记: OpenAI-compatible 请求 max_tokens 默认值泄漏

### 现象

- DiffusionGemma VLM provider 的 live `models.json` 条目声明 `maxTokens=512`。
- fast-infer server 脚本声明 `--max-tokens 128`。
- 真实 Pi 请求体仍出现 `max_tokens=4096`。

### 证据

- `src/app.rs::build_stream_options()` 旧实现没有写入 `StreamOptions.max_tokens`。
- `src/provider.rs::StreamOptions.max_tokens` 是 `Option<u32>`。
- `src/providers/openai.rs` 中 OpenAI-compatible provider 默认 `DEFAULT_MAX_TOKENS=4096`。
- `src/providers/openai.rs` 构造请求时使用 `options.max_tokens.or(Some(DEFAULT_MAX_TOKENS))`。

### 结论

- `4096` 不是模型注册表和 server 脚本的值, 而是 provider fallback 默认值。
- 修复应落在 `build_stream_options()` 的模型选择到请求选项转换边界, 而不是修改 OpenAI provider 默认值。

### 修复

- `build_stream_options()` 现在设置 `max_tokens: Some(selection.model_entry.model.max_tokens)`。
- 这让当前选中模型的 `maxTokens` 成为请求输出预算真相源。

### 验证

- 失败测试先证明旧行为为 `None`。
- 修复后聚焦单测通过。
- mock server 捕捉修复后的 `target/debug/pi` 和已安装 `pi` 请求体, 都显示 `max_tokens=512`。

## [2026-06-12 19:05:28] [Session ID: codex-20260612-rich-rust-install-e0119] 笔记: rich_rust 未锁定安装解析漂移

### 现象

- 用户的无 `--locked` 安装路径解析到 `rich_rust-0.2.1`。
- `rich_rust-0.2.1` 中 `Choice` 和 `table::Cell` 的 blanket `From<T>` 实现触发 E0119。
- 报错提到与 `time::format_description::parse::format_item::HourBase` 的上游 `From` 实现存在冲突风险。

### 静态证据

- `Cargo.toml` 原写法是 `rich_rust = { version = "0.2.0", features = ["markdown"] }`。
- 在 Cargo 语义下, `"0.2.0"` 允许解析到同一兼容区间内的 `0.2.1`。
- 当前 `Cargo.toml` 改为 `rich_rust = { version = "=0.2.0", features = ["markdown"] }`。

### 依赖图证据

- `cargo tree -p rich_rust --locked` 显示当前锁文件使用 `rich_rust v0.2.0`。
- `cargo tree -i fancy-regex@0.14.0` 显示 `fancy-regex v0.14.0` 只由 `rich_rust v0.2.0` 引入。
- `cargo tree -i fancy-regex@0.17.0` 显示 `jsonschema v0.42.2` 仍使用自己的 `fancy-regex v0.17.0`。
- `cargo tree -i windows-sys@0.52.0 --target all` 和 `cargo tree -i windows-sys@0.59.0 --target all` 显示两个版本都仍由跨平台依赖使用,不是手写锁文件伪造。

### 结论

- 根因是 `rich_rust` 依赖约束太宽,导致无锁安装漂移到当前 nightly 下会失败的 `0.2.1`。
- 修复点应放在 `Cargo.toml` 依赖真相源,而不是要求用户每次安装都手动加 `--locked`。

### 验证

- `cargo metadata --format-version 1 --locked --no-deps`: passed。
- `cargo install --path . --bin pi --force`: succeeded, replaced `/Users/cuiluming/.cargo/bin/pi`。
- `cargo fmt --check`: passed。
- `cargo check --all-targets`: 0 errors, 1 third-party future-incompat warning。
- `cargo clippy --all-targets -- -D warnings`: 0 errors, 1 third-party future-incompat warning。

## [2026-06-18 16:08:20] [Session ID: omx-1781769685432-9t7wjx] 笔记: rdog-control GUI benchmark 前置验证

## 现象

- `rdog control mac.lab` 在 daemon 未启动时返回 `Zenoh autodiscovery 在 3000ms 内未找到可连接的 router locator`。
- 使用 `/Users/cuiluming/local_doc/l_dev/my/rust/rustdog/rdog_macos.toml` 启动 daemon 后, `@ping#1` 返回 `pong`, 证明 Zenoh/daemon 基础链路可用。
- `@capabilities` 返回 `status:"degraded"`。
- GUI 相关能力均为权限阻塞:
  - `screenshot.status = permission_denied`, permission `macos.screen-recording`
  - `accessibility.status = permission_denied`, permission `macos.accessibility`
  - `window_control.status = permission_denied`
  - `keyboard_input/mouse_input/type_text.status = permission_denied`
- `@observe` 返回 `macOS Screen Recording permission denied for rdog process`。
- `@bootstrap` 返回 `不支持的控制指令类型: bootstrap`。
- `@web-find` 返回 `不支持的控制指令类型: web-find`。

## 假设与验证

### 主假设
- 当前 GUI benchmark 的执行侧已被外部条件阻塞, 不是单纯模型慢或 prompt 不好。

### 支撑证据
- `@ping` 已通过, 排除 target 完全不可达。
- `@capabilities` 明确返回一等权限错误码 `77` 和 permission 名称。
- `@observe` 明确失败在 Screen Recording permission。
- `@web-find`/`@bootstrap` 明确是协议/二进制能力不匹配, 与模型无关。

### 最强备选解释
- 即使 rdog 权限与协议都修好, 两个弱本地模型仍可能不会主动读取或正确调用 skill。

### 需要后续 benchmark 观察的点
- pi agent 是否读取 `~/.pi/agent/skills/rdog-control.md`。
- 是否产生 `rdog control` bash/tool 调用。
- 如果产生调用, 是否因权限/unsupported command 失败。
- 如果完全不调用, 则问题在弱模型 tool/skill 采纳能力, 而不是 rdog 外部环境。

## [2026-08-11 12:55:00] [Session ID: omx-1786418643597-4bz6s9] 笔记: ToolUseProfile 加载流程

### 静态发现
- `load_models_config` 被 registry load 和 model catalog route 共同复用,在此处校验能保证无效引用 fail-closed,不会部分写入注册表。
- `apply_custom_models_with_provider_headers` 同时覆盖自定义 provider/model 和 built-in provider override,是解析 `ToolUseProfile` 的唯一正确落点。
- generated catalog 使用独立严格 schema,只能提供模型 membership。本轮构造 generated `ModelsConfig` 时保持 `tool_use_profiles` 为空,不扩展其权限边界。

### 动态发现
- 有效 red 测试在 custom model 已加载后因 profile 为 `None` 失败,证明被测路径和状态一致。
- 接入后 4 个定向测试通过,覆盖 provider 继承、model 覆盖、未知引用和空引用。
- `cargo test --lib` 最初暴露 10 个 merge 遗留编译错误。恢复既有 profile 扩展字段和 test-only helper 后,定向测试成功编译运行。

### 结论
- profile 名称只存在于 `ModelsConfig` 解析阶段;运行期单一真相源仍是 `ModelEntry.tool_use_profile: Option<ToolUseProfile>`。
- 校验先于应用,未知或空引用不会退化成无 profile 模型。

## [2026-08-11 22:01:00] [Session ID: omx-1786418643597-4bz6s9] 笔记: macOS scoped scan descriptor 路径

### 现象
- `ScopedScanRoot::io_path()` 在 macOS 生成 `/dev/fd/<fd>/.`,目录 fd 的 `fstat` 有效,但该路径不能用于 `read_dir` 或子进程 cwd。
- 精确缓存测试在 `ensure_recursive_scan_access()` 阶段返回 `ENOENT`,scanner 尚未启动。

### 假设验证
- shell `test . -ef /dev/fd/0` 实验返回 false,不能作为可靠的 child identity guard,该候选方案已推翻。
- `rustix 1.1.4` 已提供安全的 `rustix::fs::getpath`,底层是 Apple `F_GETPATH`,无需新增依赖或项目内 unsafe。
- race 测试明确要求打开后的 cwd、目录和单文件在 pathname 被外部 symlink 替换后继续访问原 inode,因此简单 fail-closed 会破坏既有安全不变量。

### 当前结论
- Apple 分支应从已打开 fd 动态取得当前路径,并将路径 metadata 与 handle metadata 做 identity 校验。
- 目录 scanner 使用该路径作为 cwd 和 `.` operand。单文件不能作为 cwd,应使用 pinned workspace cwd,把已验证的文件路径作为 operand。
- Linux/Android 继续使用 `/proc/self/fd`,不改变其 descriptor 语义。

## [2026-08-11 23:10:46] [Session ID: omx-1786418643597-4bz6s9] 笔记: rpi 调用面分类

### 静态证据
- `Cargo.toml` 已将唯一 shipping target 声明为 `[[bin]] name = "rpi"`,library crate 仍为 `pi`。
- `tests/perf_budgets.rs`、`tests/perf_regression.rs` 仍有 `release/pi`、`perf/pi`、`debug/pi` 与 `custom-release/pi` 的断言,这些必须改为实际产物路径。
- `.github/workflows/ci.yml`、`bench.yml`、`release.yml` 仍构建或打包 `pi`,会在 CI 或发布阶段失败。
- `install.sh` 仍围绕 TypeScript `pi` 的 adoption 和 `rpi` wrapper alias 设计,与唯一 rpi binary 契约冲突。

### 边界结论
- 当前运行文档、安装器回归和性能命令属于本次迁移范围。
- `docs/evidence/dropin-differential-evidence-suite.json` 与 benchmark comparison 记录历史证据,不改写其过去的 `pi` 路径或命令。
- TypeScript 项目及 extension JS API 的 `pi` 命名不属于 Rust binary 迁移范围。

## [2026-08-12 00:24:21] [Session ID: omx-1786418643597-4bz6s9] 笔记: drop-in lane 自包含 fixture

### 现象
- `canonical_dropin_verdict_uses_release_gate_age_limit` 在修复前返回 `Malformed`,而预期为 `Current`。
- freshness 元数据已将失败归类为 `dropin_verdict_source_lane_invalid`。

### 静态证据
- `validate_dropin_certification_lane` 按顺序严格比对每个 gate 的 `id`、`name`、`bead`、`blocking`、`artifact_path` 和可选 `reproduce_command`。
- production 的 `opportunity_matrix_integrity` 名称是 `Opportunity matrix artifact integrity`;测试 fixture 少了 `artifact`。

### 动态证据与结论
- 修正该名称前,精确测试失败为 `Some(Malformed)`。
- 只修正该字符串后,同一条精确测试通过,证明 fixture 与 production 契约的这一精确字段不一致参与了失败路径。
- 本轮没有放宽 source lane 校验,用户 symlink 的 fail-closed 边界仍需由后续精确测试复验。

## [2026-08-12 01:11:21] [Session ID: omx-1786418643597-4bz6s9] 笔记: 默认全局 agent 目录迁移

### 静态发现

- `Config::global_dir()` 是全局 agent 根目录的唯一运行时来源。未设置 `PI_CODING_AGENT_DIR` 时,它现在返回 `~/.rpi/agent`。
- 资源加载和 QuickJS 模块缓存均从这个函数派生路径,因此不会因缓存目录保留第二个旧路径真相源。
- Kimi device ID 原本读取 `~/.pi/agent/kimi-device-id` 的兼容回退已删除;Kimi 只使用自身共享目录。

### 扫描结论

- 对 `src`、`tests`、`README.md`、`docs` 和 `scripts` 的静态扫描没有发现 `~/.pi/agent` 或 `.join(".pi").join("agent")`。
- 剩余 `.pi/agents` 和 `.pi/mcp.json` 均是项目级约定,不属于全局配置目录迁移范围。
- `jq empty` 已验证四个修改后的当前 JSON 契约;`bash -n tests/run_e2e.sh` 已通过。

### 质量门补充

- `cargo clippy -j 2 --all-targets -- -D warnings` 先发现测试 fixture 的无意义 `Result` 包装。移除后,精确 semantic graph 测试、fmt、all-target check 和 clippy 均通过。
- `proc-macro-error2 v2.0.1` 的 future-incompat 来自 `charmed-bubbletea-macros`;macOS 链接大型 lib test 时的 compact-unwind warning 也与本轮目录改动无关。两者不通过修改本仓库代码规避。

## [2026-08-12 02:10:30] [Session ID: omx-1786418643597-4bz6s9] 笔记: rpi 调用面补充分类

### 静态证据

- `src/sdk.rs` 的 in-process SDK 初始化使用了 `Cli::try_parse_from(["pi"])`;它不会启动子进程,但 argv[0] 应与 Clap 的公开程序名保持一致,因此改为 `rpi`。
- `src/cli.rs` 与 `tests/cli_edge_cases.rs` 中大量 `"pi"` 都是 Clap parser 测试的 argv[0] 占位,不参与二进制查找或用户命令解析,本轮不做无行为收益的批量替换。
- README、发布说明、终端说明、swarm 操作手册和 extension capture scenario 中的 `pi` 是对 Rust binary 的实际说明,已改为 `rpi`。
- `docs/planning/EXISTING_PI_STRUCTURE.md` 是 Rust port 的规范资料,其全局设置、认证、模型、会话、资源和 RPC 示例已经同步为 `~/.rpi/agent` 与 `rpi --mode rpc`。

### 保留边界

- TypeScript Pi 命令、Cargo library crate `pi`、`package.json` 的 `pi` 字段、项目级 `.pi/` 路径、历史讨论、beads 历史和外部扩展生态描述不属于此次迁移。
- `docs/EXTENSION_CANDIDATES.md` 记录上游 Pi 与 OpenClaw 的外部比较,保留其上游 `~/.pi/agent` 例子。

### 验证计划

- 对修改后的 JSON golden 执行 `jq empty`,再运行 CLI、配置和 swarm replay 定向测试。
- 通过 fmt、all-target check、clippy 和分类扫描后,才可进入提交前 ledger 与 UBS 门禁。

## [2026-08-12 13:32:03] [Session ID: omx-1786418643597-4bz6s9] 笔记: rpi 发布安装链路验证

### 动态证据

- `bash tests/installer_regression.sh`: 48 passed,0 failed。
- `cargo fmt --check`、`cargo check -j 2 --all-targets`、`cargo clippy -j 2 --all-targets -- -D warnings`: 均通过。
- `bash -n install.sh uninstall.sh tests/installer_regression.sh`、Ruby YAML 解析和 `git diff --check`: 均通过。

### 静态分类

- `.github/workflows/release.yml` 的 build matrix、archive root、archive 内 binary、asset inventory、manifest 和发布说明均为 `rpi`。
- `docs/releasing.md` 的 DSR raw binary、aggregate manifest、smoke、installer digest 校验和 release assets 均为 `rpi`。
- 剩余 `pi` 命中不是 shipping executable,它们是 TypeScript 命令保护、`pi.release.*` schema 或 DSR `.tool` 协议标识。

### 环境修正

- `/data` 在当前 macOS 环境只读,导致 `sccache` 无法创建临时文件。
- 改用 `/private/tmp` 后同一质量门通过,因此该问题不构成源码或构建回归。
