## [2026-06-05 16:56:00] [Session ID: omx-1780470665249-tkxhle] 问题: loose 支线计划 heredoc 未加单引号导致反引号内容被执行

### 问题现象
- 写入 `task_plan.md`, `LATER_PLANS.md`, `task_plan__minicpm5_loose.md` 时, shell 输出 `command not found: __minicpm5_loose` 等错误。
- 落盘记录中的 `__minicpm5_loose`, `/tmp`, 文件名等反引号内容缺失。

### 原因
- 我使用了未加单引号的 heredoc。
- Markdown 正文包含反引号时, shell 会执行 command substitution。

### 修复
- 追加修正记录, 明确正确支线名和正确文件名。
- 后续所有包含反引号的 Markdown 写入均使用 `cat <<'EOF'`。

### 验证
- 后续 `task_plan__minicpm5_loose.md`, `notes__minicpm5_loose.md`, `WORKLOG__minicpm5_loose.md` 的追加记录均正确保留反引号内容。
- loose harness 创建, smoke test 和正式 50 trial 均已完成。
