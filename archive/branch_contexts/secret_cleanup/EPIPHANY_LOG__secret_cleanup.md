## [2026-07-12 16:06:32] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 主题: 完整环境快照会把多类凭据一次性写入长期记录

### 发现来源

- 清理 `WORKLOG.md:486` 的 DeepSeek Key 时, 发现该行属于一整段 shell 环境快照。

### 核心问题

- 事故不是单个变量误写。完整 `env` 输出把多个 API Key、访问令牌和本机路径一起写入了受 Git 跟踪的工作记录。
- 只替换 `DEEPSEEK_API_KEY` 会留下同一事故中的其他凭据, 也不会阻止以后再次泄露。

### 为什么重要

- 环境快照常被当作普通诊断信息, 实际上等价于导出当前进程的整个信任边界。
- 一旦进入 append-only 工作记录, 后续删除当前行也不能自动清除 Git 历史对象。

### 当前结论

- 当前 `WORKLOG.md` 的环境快照已整体移除。
- 后续诊断只允许输出变量名 allowlist、`set/unset`、长度或不可逆指纹, 禁止记录完整环境。
- 历史对象仍需单独治理, 当前树清理不能替代历史清理和凭据轮换。

### 后续讨论入口

- 若用户授权历史重写, 先吊销所有曾进入该快照的凭据, 再用精确 replace-text 规则重写受影响引用并强制推送。

## [2026-07-12 17:32:30] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 主题: 多 worktree 历史重写不能直接运行 filter 工具

### 发现来源

- 历史重写预检发现 `feature/read-scope-allowlist` 正在独立 worktree 中使用, 主 worktree 也有并行未提交改动。

### 核心问题

- filter 工具在非 bare 仓库里可能 reset 工作树。只考虑 branch ref 而忽略各 worktree 的 index, 会造成 staged/unstaged 状态错位, 甚至覆盖并行工作。
- `git gc --prune=now` 也不只删除目标 Secret 对象。当前已经存在 283 个不可达对象, 包含 17 个 commits。

### 当前结论

- 必须在隔离 mirror 中过滤, 验证后用原子 ref transaction 更新两个分支。
- 两个 worktree 的 index 要分别校准, 工作文件只能做针对环境快照的结构化脱敏, 禁止 checkout/reset。
- 第二次确认必须明确包含现有不可达对象和临时 mirror 删除范围。
