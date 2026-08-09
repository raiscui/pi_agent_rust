## [2026-07-12 16:13:22] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 错误修复: DeepSeek Key 被完整环境快照写入仓库

### 现象

- DeepSeek 精确真值同时出现在全局 `~/.zshrc`、受跟踪的 `WORKLOG.md` 和忽略的 `.omx` 日志。
- Git 历史扫描确认 2 个可达 `WORKLOG.md` 版本仍保存同一真值。

### 原因

- Key 被配置在全局 shell 启动文件, 因而自动注入所有交互 shell、测试和 agent 子进程。
- 一次诊断误把完整进程环境追加到 `WORKLOG.md`, 将 DeepSeek 和其他凭据一起带入长期记录。
- 后续只隔离测试环境, 没有从工作记录和 Git 历史移除已经写入的值。

### 修复

- 把 DeepSeek 真值迁入仓库 `.envrc`, 设置 `0600`, 用 `.gitignore` 隔离。
- 增加空值 `.envrc.example`, 从 `~/.zshrc` 移除全局 export。
- 整体移除 `WORKLOG.md` 的环境快照, 脱敏 `.omx` 本地日志。
- 在 `AGENTS.md` 增加 secret hygiene 规则, 禁止记录完整环境。

### 验证

- 仓库外干净 shell: DeepSeek 变量未设置。
- 仓库内 `direnv exec`: 变量加载成功, 指纹和长度与迁移前一致。
- 当前受跟踪 / 待跟踪文件: 15 个高风险环境值精确反查为 0。
- 仓库目录精确反查: 仅忽略的 `.envrc` 有 1 个允许命中。
- Git 历史: 仍有 2 个可达提交命中, 所以历史修复尚未完成。

### 未完成边界

- 未吊销或轮换 DeepSeek Key。
- 未运行 history rewrite、reflog expire、garbage collection 或任何 force push。

## [2026-07-12 18:36:29] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 历史修复结果

### 修复

- 通过隔离 mirror 从两个分支的所有相关 `WORKLOG.md` 版本中整体移除环境快照。
- 原子更新 `main` 与 `feature/read-scope-allowlist`, 校准两个 worktree index。
- expire unreachable reflog, 执行 `git gc --prune=now`, 删除含旧对象的 mirror。

### 验证

- 旧 branch tips、污染 commits 和污染 blobs 共 6 个对象均不存在。
- reflog 旧哈希命中为 0。
- `git fsck --full --no-reflogs` 和 unreachable scan 均无输出。
- 可达历史、tracked / candidate 文件与 feature worktree 的旧 Key 精确命中为 0。
- 主 worktree 仅 `.envrc` 命中, 且该文件被忽略、权限为 `0600`。

### 仍需外部处理

- 历史清理不能让已暴露的旧 Key 恢复安全。仍需在 DeepSeek 控制台吊销并轮换它。
