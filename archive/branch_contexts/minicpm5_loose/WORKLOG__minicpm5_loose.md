## [2026-06-05 16:56:00] [Session ID: omx-1780470665249-tkxhle] 任务名称: local-minicpm5 loose 多轮回归

### 任务内容
- 单独创建 `/tmp/pi_minicpm5_loose_matrix.py` 临时 harness。
- 使用弱约束自然语言 prompt 跑 `read / grep / find / ls / edit`。
- 每个工具 10 次, 共 50 个 trial。
- 统计自然语言弱约束下的 tool-use 漂移率。

### 完成过程
- 先跑 1 轮 smoke test, 发现 loose 模式下 `grep` 容易 post-tool runaway, `find/edit` 容易 tool error。
- 修正临时 harness 分类顺序, 让长文本跑飞优先归类为 `post_tool_runaway_text`。
- 正式执行 `--trials 10 --timeout 90`, 输出保存到 `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-loose-matrix-da30nebi`。
- 从 `summary.json` 提取总体统计, 分工具统计和代表失败样本。

### 验证证据
- 临时脚本语法检查: `python3 -m py_compile /tmp/pi_minicpm5_loose_matrix.py` exit 0。
- smoke test: `--trials 1 --timeout 120`, 5 trial 完成。
- 正式 test: `--trials 10 --timeout 90`, 50 trial 完成, 命令 exit 0。
- `summary.json` 存在且统计到 50 个 trial。

### 总结感悟
- focused 成功说明“给足硬约束时”MiniCPM5 可以走真实 tool call。
- loose 统计说明“弱约束自然语言”下漂移率高达 66%。
- 后续如果想让默认交互更稳, 应优先考虑 provider-local prompt/schema 继续硬化, 而不是把某个单一工具如 `write` 做成个例。

## [2026-06-05 17:01:27] [Session ID: omx-1780470665249-tkxhle] 任务名称: loose 回归统计复核

### 任务内容
- 复核 loose 回归输出目录和 `summary.json` 是否存在。
- 重新读取统计字段, 确认总 trial, 成功数, 漂移数, 分类计数和分工具漂移率。

### 完成过程
- 读取支线上下文 `task_plan__minicpm5_loose.md`, `notes__minicpm5_loose.md`, `WORKLOG__minicpm5_loose.md`, `ERRORFIX__minicpm5_loose.md`, `LATER_PLANS__minicpm5_loose.md`。
- 执行 Python JSON 读取命令, 从 `summary.json` 提取核心统计。
- 按 `verification-before-completion` 的要求, 在汇报前完成 fresh verification。

### 总结感悟
- loose 回归是独立统计任务, 不能拿它否定 focused 修复。
- 这份结果只能说明自然语言弱约束下的漂移率, 不能和硬约束 focused prompt 混算。
