# ARCHIVE_MANIFEST — 2026-06-19 持续学习归档

> 本次持续学习（`$continuous-learning` v2.9.9）执行产生的归档清单与摘要。
> 归档执行人：codex-native session，`$continuous-learning` 流程。
> 归档前已逐组阅读本批文件，并完成经验提取、EXPERIENCE 同步、AGENTS 索引修正。

## 1. 涉及上下文集分组

### 默认主线（不归档，继续使用）
- `task_plan.md` (995 行, 最后追加 2026-06-19 17:37:16)
- `notes.md` (407 行, 最后内容 2026-06-18 rdog-control 权限分析)
- `WORKLOG.md` (402 行, 最后追加 2026-06-18 15:58:00 ultragoal reconcile)
- `LATER_PLANS.md` (151 行, 最后追加 2026-06-19 09:45:00 gemma | jq 习惯)
- `EPIPHANY_LOG.md` (305 行, 最后追加 2026-06-19 15:35:00 profile.tools 硬限制)
- `ERRORFIX.md` (211 行, 最后内容 rich_rust 版本锁修复)
- 默认组无日期后缀，活跃，无需归档。

### 真正活跃支线（不归档）
- `__rdog_bash_profile`：3 文件，最后追加 2026-06-19 15:22（M 方向完成）
- `__git_commit`：1 文件，最后追加 2026-06-19 18:38:40（阶段3 clippy 空间阻塞中）

### 未轮转旧支线（已归档到 archive/branch_contexts/）
详见第 3 节。

## 2. 六文件摘要（按组）

### 2.1 默认主线
- **当前主线目标**：把 rdog-control-bash profile + profile.tools 硬限制 (M 方向) 收口，并做一次 git commit 收尾
- **关键决定**：
  - profile.tools 限制必须在 OpenAI schema + ToolRegistry 双层生效
  - 默认 task_plan.md 接近 1000 行时启用 `__git_commit` 支线，避免主线继续膨胀
- **关键发现**：
  - `~/.cargo/bin/pi` 是旧 binary（Jun 14），之前所有 smoke 数据因旧 binary 无效
  - 改完代码必须 `cargo install --path . --force` 装新 binary，否则"代码改了"≠"行为改了"
  - ultragoal reconcile path 真实存在：通过 active snapshot 让 OMX 替 agent reconcile aggregate
- **支线组摘要**：见 2.2 - 2.5
- **暂缓事项**：
  - 解决 gemma-2B 在 rdog 后自发 `| jq` 解析的强习惯（候选方向 A：prompt D）
  - shell sandbox 设计（如果用户需要禁止 bash echo redirect / 限制 bash 只能跑 rdog 子集）
- **重大风险**：
  - profile.tools 之前是"软限制"（schema only），不是"硬限制"（registry + schema 双层）→ 已被 M 方向修复
  - 弱模型不会自发理解 rdog line-control frame 形态 → 已用 profile appendSystemPrompt 强制 stdin-frame

### 2.2 支线 `__minicpm5_generalization`（已归档）
- **任务目标**：通过 deep-interview 澄清 local_minicpm5 专项代码应抽象成哪种通用能力 / profile / 策略机制
- **关键决定**：
  - 选 B：做成可配置 profile（`weak-openai-compatible` 之类）
  - profile 定义放在 `models.json` 顶层 `toolUseProfiles`
  - provider-level 默认 + model-level override
- **关键发现**：
  - generation 参数属于模型请求行为，不应伪装成 launcher 启动参数
  - 现有 MiniCPM5 逻辑本质上是弱 OpenAI-compatible tool-use profile，不应继续以某一个模型命名留在核心路径
- **完成度**：deep-interview + spec 落地 + Pi generation 参数（stop / repetition_penalty）透传 + 实机 smoke 12.5s stopReason=stop
- **可复用点候选**：
  - 配置文件真相源分层（`toolUseProfiles` 顶层 vs `providers.*.models.*.toolUseProfile` 引用）
  - 复用现有 provider compat 承载路径，而不是给 `ModelEntry` 加新字段（避免修改 117 个无关初始化器）
- **错误与根因**：
  - heredoc 未加单引号导致反引号内容被 shell 执行（已修复为 `cat <<'EOF'`）
  - artifact 首次写入中途截断（已重写）

### 2.3 支线 `__minicpm5_loose`（已归档）
- **任务目标**：不修改生产代码，用自然语言弱约束单独跑 local-minicpm5 loose 回归，统计漂移率
- **关键决定**：
  - 10 轮/工具，共 50 trial（满足用户要求的 10-20 次下界，避免 100 trial 压力）
  - loose 和 focused 必须分开统计，不能混算
- **关键发现（结果）**：
  - 50 trial，tool_success=17, drift=33, drift_rate=66%
  - 分工具漂移率：read=70%, grep=50%, find=100%, ls=10%, edit=100%
  - 典型 loose 漂移：grep post-tool runaway, find/edit tool error, 成功工具被重复调用
- **可复用点候选**：
  - "loose 回归是独立统计任务，不能拿它否定 focused 修复"
  - 降低漂移率应走 provider-local prompt/schema 硬化，不要做单工具个例
- **错误与根因**：heredoc 未加单引号（重复发生）

### 2.4 支线 `__minicpm5_prompt`（已归档）
- **任务目标**：在 Pi 的本地 MiniCPM5 provider/model 路径上追加一段很短的 tool-use 约束
- **关键决定**：
  - 不改全局 prompt，避免影响其它 provider/model
  - provider-local 注入，CLI/RPC、扩展资源重建、SDK、ACP 都复用同一个 helper
  - 修复必须 provider-local + 保守 path repair（多候选不修）+ 重复成功工具调用转最终文本
- **关键发现**：
  - 之前 `--system-prompt` 全局替换失败 → 改 provider-local append 才 work
  - 修复组合 = prompt append + schema 改写 + 运行期保守拦截（不是单层）
  - read 工具新失败形态：同一成功工具调用被重复执行，最终超过工具轮次 → 重复保护
- **重大风险 / EPIPHANY**：小模型 tool-use 不能只依赖 prompt 约束，工具参数正确性、工具执行安全边界是一等需求
- **可复用点候选**：
  - `src/app.rs` 的 `append_provider_local_system_prompt_*` 系列 helper 模式
  - `src/agent.rs` 中 path repair 的"必须唯一明确相对路径候选 + 多候选不修"保守策略
- **错误与根因**：
  - 复核 `read` 分类错把幻化文本算作 tool_success（已修正断言：必须包含真实 expected 文本 + 不能出现 `2→` / `P2` 等扩写迹象）
  - 重复成功 read 导致超过工具轮次 → 引入重复保护

### 2.5 支线 `__minicpm5_prompt_test`（已归档）
- **任务目标**：对照测试默认 prompt vs MiniCPM5 专用短 prompt 对真实 Pi `write` 写盘成功率
- **关键决定**：
  - 不修改 Pi Rust 代码，只通过 `--system-prompt` 验证
- **关键发现（**与主假设相反**）**：
  - 默认 prompt 5 次中 2 次写盘成功
  - MiniCPM5 专用短 prompt 3 次中 0 次写盘成功，反而更差
  - 短 prompt 退化：输出 70MB/71MB/31MB 重复文本
- **方法论价值**：候选假设"只用 `--system-prompt` 收缩 Pi prompt 就能明显改善 MiniCPM5 tool call"被动态证据推翻
- **可复用点候选**：
  - 失败不在 Pi 中间层漏解析，而在模型/服务端没发出可执行 tool call
  - 后续应优先：服务端降低 `max_tokens` / parser 失败可观测错误 / `tool_choice` 或模板层强制工具选择

## 3. 归档动作清单

### 3.1 已移动到 archive/branch_contexts/minicpm5_generalization/
- `task_plan__minicpm5_generalization.md`
- `notes__minicpm5_generalization.md`
- `WORKLOG__minicpm5_generalization.md`
- `ERRORFIX__minicpm5_generalization.md`
- 不含 `LATER_PLANS__minicpm5_generalization.md` / `EPIPHANY_LOG__minicpm5_generalization.md`（该支线本就没建这两个文件）

### 3.2 已移动到 archive/branch_contexts/minicpm5_loose/
- `task_plan__minicpm5_loose.md`
- `notes__minicpm5_loose.md`
- `WORKLOG__minicpm5_loose.md`
- `LATER_PLANS__minicpm5_loose.md`
- `ERRORFIX__minicpm5_loose.md`

### 3.3 已移动到 archive/branch_contexts/minicpm5_prompt/
- `task_plan__minicpm5_prompt.md`
- `notes__minicpm5_prompt.md`
- `WORKLOG__minicpm5_prompt.md`
- `LATER_PLANS__minicpm5_prompt.md`
- `EPIPHANY_LOG__minicpm5_prompt.md`
- `ERRORFIX__minicpm5_prompt.md`

### 3.4 已移动到 archive/branch_contexts/minicpm5_prompt_test/
- `task_plan__minicpm5_prompt_test.md`
- `notes__minicpm5_prompt_test.md`
- `WORKLOG__minicpm5_prompt_test.md`

### 3.5 不归档的对象
- 默认主线 6 文件（持续活跃）
- `__rdog_bash_profile` 3 文件（活跃支线，最近追加 2026-06-19 15:22）
- `__git_commit` 1 文件（活跃支线，最近追加 2026-06-19 18:38:40）
- `archive/default_history/task_plan_2026-06-10_163200.md`（已存在，不动）

## 4. 配套沉淀清单

### 4.1 已沉淀到 EXPERIENCE.md
- 经验 A：profile 字段的两层语义（OpenAI schema + ToolRegistry）
- 经验 B：改完代码不重 build 装 = 隐形 bug
- 经验 C：小模型 tool-use 不能只依赖 prompt 约束
- 经验 D：heredoc 未加单引号导致反引号被 shell 命令替换（4 个支线反复出现，需更显眼的提示）
- 经验 E：loose 回归 vs focused 修复不能混算
- 经验 F：`--system-prompt` 短 prompt 反而更差（候选假设被动态证据推翻的良好范例）

### 4.2 已沉淀到 AGENTS.md（新增索引项）
- `archive/manifests/ARCHIVE_MANIFEST__2026-06-19__continuous-learning.md`：本次持续学习归档清单 + 六文件摘要
- `archive/branch_contexts/`：未轮转旧支线归档（minicpm5_* 4 个主题）
- `EXPERIENCE.md`：项目级经验沉淀（已扩充本轮新条目）
- 提醒条目：默认 task_plan.md 已 995 行，下次接近 1000 时建议提前续档 + 启动新支线

### 4.3 不需要新建的 docs / specs
- 4 个 minicpm5 支线都是 closed-loop 实验 + fix，没有需要长期 follow 的设计 / 接口
- 已有的 `docs/models.md` 中 `rdog-control-bash` profile 示例 + `tools` 字段说明，已在 `__rdog_bash_profile` 阶段5 中同步

### 4.4 LATER_PLANS.md 默认组清理建议
- 默认组 LATER_PLANS.md 中"后续计划: 让 ToolUseProfile 也能锁工具白名单"（2026-06-18 16:45:31）已被 `__rdog_bash_profile` 完成（M 方向双层过滤已落地）
- 建议下次主线收尾时清理此条目

## 5. 验证与影响

- 默认根目录 6 个默认文件 + 2 个活跃支线文件保留
- 4 个未轮转旧支线共 18 个文件已搬移到 `archive/branch_contexts/<topic>/`
- 默认 `task_plan.md` 无任何 minicpm5_* 引用，归档不会影响主线的索引
- 默认 `EXPERIENCE.md` 和 `AGENTS.md` 索引已更新
- 暂不需要把 `__rdog_bash_profile` 的内容转成正式 `docs/specs/`，因为它已经收口，剩余的 `| jq` 习惯和 shell sandbox 是独立的 follow-up

## 6. 归档执行签名
- 执行时间：2026-06-19 (Asia/Shanghai)
- 执行流程：$continuous-learning v2.9.9
- 阅读覆盖：6 个默认文件 + 6 个支线组共 22 个文件
- 经验提取：A-F 共 6 条
- 索引更新：EXPERIENCE.md + AGENTS.md
