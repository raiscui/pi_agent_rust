## [2026-07-12 16:13:22] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 后续计划: 凭据轮换与 Git 历史清理

### 必做事项

- 在 DeepSeek 控制台吊销当前 Key, 创建新 Key, 再更新忽略的 `.envrc`。
- 评估完整环境快照中出现过的其他凭据, 对仍有效的 token 一并轮换。
- 在没有并行工作树写入的安全窗口, 重写 `main` 和 `feature/read-scope-allowlist` 中受影响的 `WORKLOG.md` 对象。
- 验证所有引用、reflog 和可达 / 不可达对象不再命中旧指纹后, 再推送远端。

### 授权边界

- Key 吊销属于外部账号状态变更。
- history rewrite、reflog expire 和 object pruning 属于不可逆 Git / 文件系统操作。
- 上述动作均需用户明确确认具体命令与影响范围后再执行。

## [2026-07-12 18:36:29] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 状态更新: 历史治理已完成

### 已完成

- [x] 重写 `main` 和 `feature/read-scope-allowlist`。
- [x] 清理 reflog、旧对象和临时 mirror。
- [x] 验证本地历史与 worktree 不再命中旧 DeepSeek 真值。

### 仍保留

- [ ] 在 DeepSeek 控制台吊销旧 Key, 创建新 Key, 更新忽略的 `.envrc`。
- [ ] 评估完整环境快照中出现过的其他凭据, 对仍有效的 token 执行轮换。
