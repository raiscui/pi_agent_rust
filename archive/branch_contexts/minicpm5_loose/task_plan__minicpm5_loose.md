# 任务计划: local-minicpm5 loose 多轮回归

## [2026-06-05 16:22:21] [Session ID: omx-1780470665249-tkxhle] 计划: 独立统计弱约束 tool-use 漂移率

### 目标

在不修改生产代码的前提下, 用自然语言弱约束提示单独跑 local-minicpm5 的  回归, 统计 no tool call, wrong tool, parse error, tool error, post-tool runaway, repeated same tool, final answer mismatch 等漂移率。

### 阶段

- [ ] 阶段1: 准备 loose harness 与环境检查
- [ ] 阶段2: 执行 10 轮/工具 loose 回归
- [ ] 阶段3: 汇总漂移统计和典型样本
- [ ] 阶段4: 记录结果并交付

### 关键问题

1. loose 和 focused 的区别是什么?
   - loose prompt 不使用“必须调用工具 / 不要只用文字回答 / 工具返回后只回答原文”等硬约束, 只用普通自然语言任务描述。
2. 是否修改生产代码?
   - 不修改。本任务只创建  临时 harness 和测试输出。
3. 统计口径是什么?
   - 每个工具 10 次, 共 50 个 trial。分类统计成功率和漂移类型。

### 做出的决定

- 决定: 先跑 10 轮/工具, 满足用户要求的 10-20 次下界, 避免 100 个 trial 对本地 server 造成过长压力。
- 理由: focused 5/5 已通过, 本轮目标是估计弱约束漂移率, 10 轮/工具足够暴露主要漂移类型。

### 状态

**目前在阶段1** - 准备 loose harness 与环境检查。

## [2026-06-05 16:23:01] [Session ID: omx-1780470665249-tkxhle] 修正: 首条 loose 计划中的反引号内容缺失

- 现象: 首条计划里 `read / grep / find / ls / edit` 和 `/tmp` 等内容被 shell 命令替换吃掉。
- 原因: 写入计划时使用了未加单引号 heredoc。
- 修正后的目标: 在不修改生产代码的前提下, 用自然语言弱约束提示单独跑 local-minicpm5 的 `read / grep / find / ls / edit` 回归, 统计漂移率。
- 修正后的执行方式: 创建 `/tmp/pi_minicpm5_loose_matrix.py` 临时 harness, 每个工具 10 次, 共 50 个 trial。
- 下一步行动: 写入临时 loose harness 并运行。

## [2026-06-05 16:24:00] [Session ID: omx-1780470665249-tkxhle] 状态: loose harness 已创建

- 临时脚本: `/tmp/pi_minicpm5_loose_matrix.py`。
- prompt 风格: 弱约束自然语言, 不包含 focused 的“必须调用工具 / 真实 tool call / 返回后只回答原文”等硬约束。
- 分类项: `tool_success`, `no_tool_call`, `wrong_or_no_tool_call`, `parse_error_tool`, `tool_error`, `tool_result_mismatch`, `side_effect_mismatch`, `tool_success_no_agent_end`, `post_tool_runaway_text`, `repeated_same_tool`, `final_answer_mismatch`, `read_fabricated_extra_lines`。
- 下一步: 先跑 1 轮 smoke test。

## [2026-06-05 16:31:44] [Session ID: omx-1780470665249-tkxhle] 状态: loose smoke test 完成并修正分类顺序

- smoke 命令: `python3 /tmp/pi_minicpm5_loose_matrix.py --trials 1 --timeout 120 ...`
- smoke 结果: 5 个 trial 中 `tool_success=2`, `tool_success_no_agent_end=1`, `tool_error=2`, 漂移率 60%。
- 观察到的典型 loose 漂移:
  - `grep`: 工具成功后 post-tool 文本持续重复扩写, 没等到 `agent_end`。
  - `find`: 调用了 `find`, 但工具返回 error 或结果未达到预期。
  - `edit`: 调用了 `edit`, 但参数/路径漂移导致工具错误。
- harness 修正: 将 `len(assistant_text) > 2000` 的判断移动到 `agent_end` 判断之前, 让长文本跑飞优先归类为 `post_tool_runaway_text`。
- 下一步: 正式跑 `--trials 10 --timeout 90`, 共 50 个 trial。

## [2026-06-05 16:56:00] [Session ID: omx-1780470665249-tkxhle] 完成: loose 10 轮/工具回归已完成

- 正式命令: `python3 /tmp/pi_minicpm5_loose_matrix.py --trials 10 --timeout 90 ...`
- 输出目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-loose-matrix-da30nebi`
- 结果: 50 trial, `tool_success=17`, drift=33, drift rate=66%。
- 已写入 `notes__minicpm5_loose.md`, `WORKLOG__minicpm5_loose.md`, `ERRORFIX__minicpm5_loose.md`, `LATER_PLANS__minicpm5_loose.md`。
- 已检查是否需要 `EPIPHANY_LOG__minicpm5_loose.md`: 本轮没有新增超出 MiniCPM5 已知弱约束不稳定性的架构级灾难风险, 暂不创建。

### 阶段状态

- [x] 阶段1: 准备 loose harness 与环境检查
- [x] 阶段2: 执行 10 轮/工具 loose 回归
- [x] 阶段3: 汇总漂移统计和典型样本
- [x] 阶段4: 记录结果并交付

## [2026-06-05 17:01:27] [Session ID: omx-1780470665249-tkxhle] 复核: loose summary 统计已确认

- 复核命令: `python3 - <<'PY' ... summary.json ... PY`
- 复核文件: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-loose-matrix-da30nebi/summary.json`
- 复核结果: `total=50`, `success=17`, `drift=33`, `drift_rate=0.66`。
- 分工具漂移率: `read=70%`, `grep=50%`, `find=100%`, `ls=10%`, `edit=100%`。
- 本次复核没有修改生产代码, 也没有把 loose 结果和 focused 修复混合统计。
