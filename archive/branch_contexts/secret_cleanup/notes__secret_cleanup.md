## [2026-07-12 16:02:06] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 笔记: DeepSeek Secret 泄露面证据

### 当前树

- 合法变量名 `DEEPSEEK_API_KEY` 出现在 provider 元数据、认证代码、测试和文档中。这些引用是配置契约, 不是密钥泄露, 不应删除。
- 精确真值只命中 `WORKLOG.md:486` 和忽略的 `.omx/logs/turns-2026-06-29.jsonl:3`。
- `WORKLOG.md:414-507` 是完整环境快照。它同时含 DeepSeek 之外的凭据类变量, 因此必须整体移除。

### 本地来源

- 精确真值命中 `~/.zshrc:107`。当前 `direnv status` 显示仓库没有 `.envrc` 或 `.env` 被加载。
- 现有模式把 Key 注入所有交互 shell, 会污染测试、agent 日志和任何子进程。仓库级 `.envrc` 更符合最小暴露范围。

### Git 历史

- `29cd99af10d39a36dd5507e2612b59c67539e119` 首次提交含真值的 `WORKLOG.md`。
- `99a3b42dddca14b9c22a5ea637324a1d29a37a91` 的 `WORKLOG.md` 版本仍含同一真值。
- 当前文件修改只能清理 HEAD, 不能清理上述可达对象。后续必须把"当前树通过"和"历史通过"分开报告。

### 清理原则

- 真值只进入 Git 忽略且权限为 `0600` 的 `.envrc`。
- 仓库只跟踪 `.envrc.example`, 其中使用空默认值和说明, 不包含可用凭据。
- 禁止记录完整 `env` 输出。诊断时使用变量名 allowlist, 或只记录 `set/unset`、长度和不可逆指纹。

## [2026-07-12 17:32:30] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 笔记: 历史重写预检

### 安全约束

- 当前仓库有两个活跃 worktree。直接运行历史过滤会让 branch ref、index 和工作文件失配。
- 当前主 worktree 有 tracked 与 untracked 修改, feature worktree 有 untracked 上下文文件。不能 stash、reset 或 checkout 覆盖。
- 采用隔离 mirror 的原因是把 filter 的 reset / reflog 行为限制在临时仓库, 再用 `git update-ref --stdin` 原子交换本地引用。

### 清理副作用

- reflog 清理会让 8 个含旧 Key 的历史版本不再可恢复。
- `git gc --prune=now` 会同时删除执行前已经存在的 283 个不可达对象。它们不是当前分支内容, 但其中包括 17 个不可达 commit。
- 临时 mirror 自身也含重写前对象, 完成后必须删除, 否则本机仍保留一份旧 Secret 历史。
