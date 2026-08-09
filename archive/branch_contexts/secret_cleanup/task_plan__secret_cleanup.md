# 任务计划: DeepSeek API Key 本地与仓库隔离

## [2026-07-12 15:57:06] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 任务计划: 建立脱敏清理闭环

### 目标

- 不回显任何密钥值, 清除当前工作树和本地配置中的 DeepSeek 明文凭据。
- 让仓库只保留环境变量名称与安全模板, 真值只进入 Git 忽略的本地载体。
- 检查所有可达 Git 引用是否仍含历史泄露, 用证据区分"当前文件已清理"和"历史已清理"。

### 方案对比

- 方案 A, 最佳方案: 先完成当前树和本地配置隔离, 再吊销旧 Key, 生成新 Key, 重写所有受影响 Git 历史并协调强制推送。此方案能真正消除旧凭据风险, 但吊销和历史重写都需要用户另行明确授权。
- 方案 B, 先恢复安全边界: 立即清理当前树, 建立 `.envrc` / `.envrc.example` / `.gitignore` 隔离, 并精确列出历史命中。它不会改变已有 Git 对象, 也不能让已经泄露的旧 Key 重新安全。
- 当前决定: 先执行方案 B 中所有可逆步骤。若历史仍命中, 本轮给出精确证据和待授权命令, 不擅自重写历史或操作 DeepSeek 账号。

### 阶段

- [x] 阶段1: 回读项目上下文、历史事故记录和表达规范。
- [ ] 阶段2: 以脱敏方式盘点当前树、Git 跟踪面、可达历史和本地 Key 来源。
- [ ] 阶段3: 清理当前明文痕迹, 建立本地与仓库的单一真相源边界。
- [ ] 阶段4: 运行仓库扫描、Git 历史扫描和配置权限验证。
- [ ] 阶段5: 记录证据、风险和需要用户明确授权的后续动作。

### 当前假设与备选解释

- 主假设: 当前 DeepSeek Key 来自本地全局环境配置, 并曾被整行环境快照写入 `WORKLOG.md` 后进入 Git 历史。
- 备选解释: 当前环境值可能来自父级 direnv、终端注入或密码管理器, 仓库当前树只剩历史对象而没有明文。
- 推翻主假设的证据: 本地精确值反查找不到持久化来源, 或 Git 历史对象扫描不再命中该值。

### 验证纪律

- 扫描只输出路径、行号、匹配类型、长度和不可逆指纹前缀, 不输出密钥正文。
- 当前树和历史分别验证, 避免用"工作树已干净"冒充"历史已干净"。
- 不运行 `git filter-repo`、rebase、force push、远端 Key 吊销等不可逆或外部状态操作。

### 状态

**目前在阶段2** - 正在定位真实泄露面和本地配置来源。

## [2026-07-12 16:02:06] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 阶段状态: 泄露面盘点完成

### 已验证现象

- 当前 DeepSeek 真值指纹为 `sha256:cf72ec34a480`, 长度为 35。扫描只记录指纹, 未主动输出真值。
- 当前持久化副本共 3 处: `WORKLOG.md:486`、忽略的 `.omx/logs/turns-2026-06-29.jsonl:3`、全局 `~/.zshrc:107`。
- `WORKLOG.md` 中不是单独一行误写, 而是从 414 到 507 行的整段环境快照。快照还含其他凭据类型, 正确处理方式是移除整段快照, 不是只遮住 DeepSeek 一行。
- 可达 Git 历史中有 2 个 `WORKLOG.md` 版本含相同真值: `29cd99af10d39a36dd5507e2612b59c67539e119` 和 `99a3b42dddca14b9c22a5ea637324a1d29a37a91`。
- 受影响的本地引用是 `main` 和 `feature/read-scope-allowlist`; 当前远端跟踪引用未显示包含该提交。
- `.gitignore` 尚未忽略 `.envrc`; 当前仓库也没有 `.envrc` 或 `.envrc.example`。

### 假设结论

- 主假设成立: 全局 `~/.zshrc` 是当前持久化来源, 完整环境快照把真值带入 `WORKLOG.md`, 随后进入 Git 历史。
- 备选解释"仅剩历史对象"不成立, 因为当前工作树和全局 shell 配置都仍有精确值命中。

### 阶段

- [x] 阶段2: 以脱敏方式盘点当前树、Git 跟踪面、可达历史和本地 Key 来源。
- [ ] 阶段3: 清理当前明文痕迹, 建立本地与仓库的单一真相源边界。

### 即将执行

- 先更新 `.gitignore` 并增加不含真值的 `.envrc.example`。
- 以 `0600` 权限把当前 Key 迁入被忽略的仓库 `.envrc`, 验证指纹一致后再移除 `~/.zshrc` 的全局 export。
- 移除 `WORKLOG.md` 的完整环境快照, 并脱敏本地 `.omx` 日志中的精确值。

### 状态

**目前在阶段3** - 开始执行可逆的当前树和本地配置隔离。

## [2026-07-12 16:06:32] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 阶段状态: 本地与当前树隔离完成

### 完成动作

- `.gitignore` 已加入 `.envrc` 和 `.direnv/`。
- 已创建不含真值的 `.envrc.example`。
- 当前 Key 已迁入 `.envrc`, 权限为 `0600`, 并通过 `direnv allow` 激活。
- `~/.zshrc` 的全局 `DEEPSEEK_API_KEY` export 已替换为迁移说明。
- `WORKLOG.md` 中 118 行误写片段已收束为 2 条脱敏结论, 完整环境快照不再存在于当前树。
- `.omx/logs/turns-2026-06-29.jsonl` 中的精确值已替换为脱敏标记。

### 动态证据

- 仓库外的干净 login shell: `global_shell_deepseek=absent`。
- 仓库内 `direnv exec`: `direnv_loaded=True`, 指纹和长度与迁移前一致。
- 当前仓库精确值扫描: 1 个允许命中, 仅为忽略的 `.envrc:2`; 非允许命中为 0。
- 全局配置精确值扫描: 0 命中。

### 阶段

- [x] 阶段3: 清理当前明文痕迹, 建立本地与仓库的单一真相源边界。
- [ ] 阶段4: 运行仓库扫描、Git 历史扫描和配置权限验证。

### 即将执行

- 检查工作树 diff 的结构与 whitespace, 不输出被删除的凭据值。
- 运行可用的 secret scanner, 复核 DeepSeek 精确值和常见高风险 token 形态。
- 再次确认历史对象仍命中时, 把它明确列为需要授权的独立阶段。

### 状态

**目前在阶段4** - 正在做当前树与历史的终态验证。

## [2026-07-12 16:13:22] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 验证结果: 当前树通过, 历史仍阻塞

### 当前树验证

- 从当前进程筛出 15 个高风险环境变量, 对所有受 Git 跟踪或待跟踪文件做精确值反查, 命中为 0。
- DeepSeek 精确值在仓库物理目录内只剩 `.envrc:2`, 该文件被 `.gitignore` 命中且权限为 `0600`。
- `.envrc.example` 不含真值, `direnv exec` 能从干净环境加载仓库 `.envrc`。
- `git diff --check` 无输出, 没有 whitespace 错误。
- token 形态扫描有 22 个命中, 均位于 provider 示例或显式测试夹具; 它们不等于本机任何高风险环境变量, 不属于本次真实凭据泄露。

### 历史验证

- `WORKLOG.md` 的可达历史仍有 2 个提交含 DeepSeek 精确真值。
- 因此当前只能确认"本地配置与当前工作树已隔离", 不能确认"Git 历史已清理"。

### 阶段

- [x] 阶段4: 运行仓库扫描、Git 历史扫描和配置权限验证。
- [x] 阶段5: 记录证据、风险和需要用户明确授权的后续动作。
- [ ] 阶段6: 用户授权后轮换已泄露凭据, 重写受影响引用并清理旧对象。

### 阻塞条件

- 旧 Key 已进入可达历史, 安全上必须视为已泄露。轮换 DeepSeek Key 会改变外部账号状态。
- 清理 2 个历史提交需要重写 `main` 和 `feature/read-scope-allowlist`, 随后还要处理 reflog / unreachable object。该操作不可逆, 且当前工作树还有并行会话改动, 必须得到明确授权并安排安全窗口。

### 状态

**等待明确授权** - 所有可逆清理和验证已完成, 未执行 Key 吊销、历史重写、对象清理或推送。

## [2026-07-12 17:27:29] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 授权阶段: 准备历史重写命令

### 用户授权原文

- `重写 main 和 feature/read-scope-allowlist 历史, 清理 reflog 与旧 Git 对象`

### 当前边界

- 该原文明确授权了目标动作, 但仓库不可逆操作规范还要求: 执行前列出原始命令、精确影响范围, 并等待用户确认理解。
- 当前只执行只读预检: 工具版本、引用拓扑、worktree、status、submodule 和历史命中面。
- 不移动分支、不修改 index、不 checkout、不执行 filter、reflog expire 或 GC。

### 即将执行

- 确认 `git filter-repo` 是否可用及其工作树行为。
- 确认受影响引用、远端引用、tag、worktree 和当前并行改动。
- 选择不会覆盖 tracked、untracked、ignored 文件的执行路径, 然后把完整命令逐行交给用户做第二次确认。

### 状态

**阶段6 预检中** - 等待形成可安全执行的最终命令集。

## [2026-07-12 17:32:30] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 阶段6 预检结论: 必须隔离重写并二次确认

### 引用与 worktree

- `main` 当前为 `21c9c27d3f7c51d507a3a1fb1bc51c228a00af6d`, 比 `my/main` 领先 34 个提交。
- `feature/read-scope-allowlist` 当前为 `8597192e74d97abe0a2dc1ed50bcf2ee8ad31d44`, 是 `main` 的祖先, 相差 29 个提交。
- feature 分支正在 `/Users/cuiluming/local_doc/l_dev/my/rust/pi_agent_rust-read-allowlist` worktree 中使用。该 worktree 没有 tracked 修改, 有 3 个 untracked 上下文文件。
- 两个 worktree 的 `WORKLOG.md` 都必须校准。feature worktree 当前仍有 1 个精确值命中。
- 没有 submodule, 没有 stash。远端引用和 tag 不包含受影响提交。

### 对象与 reflog

- 受污染的唯一 `WORKLOG.md` blob 是 `778dd7fc5a04a0fb890ed29acaa026305758c1e3` 和 `c8d4de9f39487d8b3854f0ba821487fcf78e736f`。
- 59 个 reflog commit 候选中, 8 个提交版本含精确真值。
- 执行历史重写前, 仓库已经有 283 个不可达对象: 17 commits、106 trees、160 blobs。
- `git reflog expire ... --all` 加 `git gc --prune=now` 不会只删除 DeepSeek 相关对象; 这 283 个已有不可达对象也会失去恢复机会并被清理。

### 工具与执行路径

- 本机未安装 `git filter-repo`; Homebrew 可安装稳定版 2.47.0。
- 不允许直接在当前多 worktree 仓库过滤, 因为 filter 工具可能 reset 当前工作树。
- 选定路径: 在 `/private/tmp/pi_agent_rust_secret_rewrite_20260712_172729.git` 创建 `--no-local --mirror` 隔离副本, 只重写两个本地分支, 验证后 fetch 到临时 refs, 原子更新两个 branch refs, 分别更新两个 worktree 的 `WORKLOG.md` index, 再清理 reflog 和对象。

### 二次确认边界

- 尚未安装工具、创建 mirror、移动引用、修改 feature worktree、expire reflog、运行 GC 或删除临时 mirror。
- 下一条回复必须明确确认: 两个分支从污染提交开始的 commit hash 会变化; 8 个污染 reflog 版本会失效; 283 个原有不可达对象也会删除; 指定临时 mirror 会被 `rm -rf` 删除。

### 状态

**等待第二次明确确认** - 确认后才执行下方列出的原始命令序列。

## [2026-07-12 18:25:03] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 不可逆操作最终授权

### 用户确认原文

> 我确认执行上述历史重写、reflog 清理、git gc --prune=now 和 rtk proxy rm -rf /private/tmp/pi_agent_rust_secret_rewrite_20260712_172729.git。我理解两个分支的提交哈希会变化, 8 个污染 reflog 版本和现有 283 个不可达对象将无法恢复。

### 获准执行的操作

- 安装 `git-filter-repo` 2.47.0。
- 创建并重写指定隔离 mirror。
- 原子更新 `main` 和 `feature/read-scope-allowlist`。
- 校准两个 worktree 的 `WORKLOG.md` 与 index, 不覆盖其他文件。
- 执行 `git reflog expire --expire=never --expire-unreachable=now --all`。
- 执行 `git gc --prune=now`。
- 执行 `rtk proxy rm -rf /private/tmp/pi_agent_rust_secret_rewrite_20260712_172729.git`。

### 状态

**阶段6 执行中** - 已获得两次明确授权, 开始隔离重写与验证。

## [2026-07-12 18:27:30] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 阶段6A 完成: mirror 重写验证通过

### 验证证据

- 新 `main`: `5f877467edad53d501e9c8057db53eb9a46b5eab`。
- 新 `feature/read-scope-allowlist`: `5aa74667ad46681a97d00c592d2c99409811d4be`。
- 所有可达 `WORKLOG.md` 历史版本精确值命中为 0。
- `main` commit count 保持 3570; feature commit count 保持 3541。
- feature 仍是 main 的祖先; `my/main` 仍是新 main 的祖先。
- 两个 tip tree 都只允许 `WORKLOG.md` 变化, 实际验证均为 1 个路径。

### 待办

- [x] 在隔离 mirror 中重写并验证两个分支。
- [ ] fetch 新对象到临时 refs, 再次检查源 refs 没有漂移。
- [ ] 原子更新两个 branch refs, 校准两个 worktree。
- [ ] 清理 reflog 与旧对象, 删除 mirror。
- [ ] 运行终态 Secret / Git 完整性验证。

### 状态

**阶段6B 执行中** - 准备把已验证对象导入临时 refs, 尚未移动正式分支。

## [2026-07-12 18:31:36] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 阶段6B 完成: 两个分支已原子更新

### 执行结果

- `git update-ref --stdin` transaction 返回 `start: ok`, `prepare: ok`, `commit: ok`。
- `main` 已更新为 `5f877467edad53d501e9c8057db53eb9a46b5eab`。
- `feature/read-scope-allowlist` 已更新为 `5aa74667ad46681a97d00c592d2c99409811d4be`。
- 两个 worktree 的 `WORKLOG.md` index 已分别校准到新 tip blob。
- main 原有其他 tracked / untracked 改动保持存在; feature 仍只有原来的 3 个 untracked 上下文文件。
- 正式 refs 的 `WORKLOG.md` 历史精确值命中为 0, feature 仍是 main 的祖先, `my/main` 仍是 main 的祖先。

### 待办

- [x] fetch 新对象并原子更新两个 branch refs。
- [x] 校准两个 worktree, 保留其他未提交文件。
- [ ] 删除 `refs/secret-rewrite/*` 临时 refs。
- [ ] expire unreachable reflog, 执行 `git gc --prune=now`。
- [ ] 验证旧 commits / blobs 不再存在, 再删除 mirror。

### 状态

**阶段6C 执行中** - 开始清理旧对象可达性与对象数据库。

## [2026-07-12 18:34:04] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 阶段6C 完成: reflog、旧对象与 mirror 已清理

### 不可逆操作审计记录

- 用户授权原文: `我确认执行上述历史重写、reflog 清理、git gc --prune=now 和 rtk proxy rm -rf /private/tmp/pi_agent_rust_secret_rewrite_20260712_172729.git。我理解两个分支的提交哈希会变化, 8 个污染 reflog 版本和现有 283 个不可达对象将无法恢复。`
- 实际执行: `rtk proxy git reflog expire --expire=never --expire-unreachable=now --all`。
- 实际执行: `rtk proxy git gc --prune=now`。
- 实际执行: `rtk proxy rm -rf /private/tmp/pi_agent_rust_secret_rewrite_20260712_172729.git`。
- 执行时间窗口: 2026-07-12 18:31:36 至 2026-07-12 18:34:04 +0800。

### 删除前验证

- 6 个旧 tip / commit / blob 对象全部无法读取。
- reflog 中旧哈希命中为 0。
- `git fsck --full --no-reflogs` 和 unreachable scan 均无输出。
- 正式 refs 的 DeepSeek 精确值命中为 0。
- 主 worktree 只有忽略的 `.envrc` 允许命中; feature worktree 为 0 命中。

### 待办

- [x] expire unreachable reflog。
- [x] 执行 `git gc --prune=now`。
- [x] 删除临时 mirror。
- [ ] 删除后重新运行完整终态验证并记录结果。

### 状态

**阶段6D 验证中** - 重新读取计划后执行完成前验证门禁。

## [2026-07-12 18:36:29] [Session ID: 019f5551-7950-7a21-b33b-617b24f4f8d0] 阶段6 完成: 本地历史与旧对象清理通过

### 最终引用

- `main`: `5f877467edad53d501e9c8057db53eb9a46b5eab`。
- `feature/read-scope-allowlist`: `5aa74667ad46681a97d00c592d2c99409811d4be`。
- feature 仍是 main 的祖先; `my/main` 仍是 main 的祖先; 本地 main 仍领先 `my/main` 34 个提交。
- 未修改或推送任何远端引用。

### 删除后完成门禁

- [x] 临时 mirror 路径不存在。
- [x] 6 个旧 tip / commit / blob 对象均不存在。
- [x] reflog 旧哈希命中为 0。
- [x] `git fsck --full --no-reflogs` 无错误。
- [x] unreachable scan 无输出。
- [x] 可达 `WORKLOG.md` 历史精确值命中为 0。
- [x] 15 个当前高风险环境值在 tracked / candidate 文件中精确命中为 0。
- [x] 主 worktree 只有忽略且 `0600` 的 `.envrc` 允许命中; feature worktree 为 0 命中。
- [x] 仓库外新 login shell 不再获得 DeepSeek Key; 仓库内 direnv 加载成功。
- [x] `git diff --check` 无错误。
- [x] 两个 worktree 的原有其他修改与 untracked 文件均保留。

### 授权范围完成状态

- [x] 重写 `main` 历史。
- [x] 重写 `feature/read-scope-allowlist` 历史。
- [x] 清理 unreachable reflog。
- [x] 清理旧 Git 对象。
- [x] 删除含旧历史的临时 mirror。
- [ ] 吊销并轮换 DeepSeek Key。该动作需要 DeepSeek 账号操作授权, 不在本次用户确认范围内。

### 状态

**历史清理已完成** - 本次获授权的不可逆操作全部执行并通过验证; 仅凭据轮换仍作为外部账号事项保留。
