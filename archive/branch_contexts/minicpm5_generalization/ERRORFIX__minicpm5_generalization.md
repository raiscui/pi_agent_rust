
## [2026-06-05 17:08:34] [Session ID: omx-1780470665249-tkxhle] 错误修正: deep-interview context snapshot heredoc 未加单引号

- 现象: 首次写入 `.omx/context/minicpm5-generalization-20260605T090709Z.md` 时, Markdown 反引号内的 `local_minicpm5`, `src/app.rs`, `models.json` 等被 shell 当作命令执行, snapshot 内容出现空洞。
- 原因: 我使用了未加单引号的 heredoc。
- 修复: 已用 `cat <<'EOF'` 重新写入同一个由我创建的 context snapshot 文件, 保留反引号内容。
- 验证: 下一步会读取 snapshot 头部和关键行, 确认反引号内容完整。

## [2026-06-08 15:18:06] [Session ID: omx-1780470665249-tkxhle] 错误修正: deep-interview artifact 首次写入截断

- 现象: `.omx/interviews/minicpm5-generalization-20260608T071724Z.md` 只有 12 行, 内容停在 `reusable` 后面; `.omx/specs/deep-interview-minicpm5-generalization.md` 未生成。
- 原因: artifact 写入命令内容中途截断, 导致 heredoc 没有完整写入预期文档。
- 修复计划: 直接修复由本轮创建的不完整 interview 文件, 并新增缺失的 spec 文件。
- 验证计划: 写入后读取两个文件头尾和行数。


## [2026-06-10 18:15:56] [Session ID: omx-1781010764764-n4q7h4] 错误修复: MiniCPM5 Pi 请求缺少 stop 与 repetition_penalty

### 问题
- Pi 的 OpenAI Chat Completions request schema 没有 `stop` 和 `repetition_penalty`。
- 用户全局 MiniCPM5 配置只有 `maxTokens=4096`,模型重复时可能持续输出到较大 token 上限。

### 现象 -> 假设 -> 验证 -> 结论
- 现象: MiniCPM5 在 Pi 下出现循环输出、难以停止。
- 主假设: Pi 没有把停止序列和重复惩罚传给 MLX-LM server。
- 备选解释: weak/loose prompt、tool-use 后处理或模型能力也可能造成重复与错误内容。
- 静态验证: 修改前 `OpenAIRequest` 和 `models.json` 均没有对应字段; MLX-LM server 明确从 HTTP body 读取它们。
- 动态验证: request JSON 单测确认字段透传;真实 Pi smoke 在 12.50 秒内以 `stopReason="stop"` 结束。
- 结论: Pi 的 generation 参数缺口已确认并修复。指令遵循质量仍需按独立问题处理。

### 修复
- 新增 provider/model 级 `generation` 配置和继承规则。
- OpenAI request 序列化 `stop` 与 `repetition_penalty`。
- MiniCPM5 实际配置加入两个停止符和 `repetitionPenalty=1.15`。
- MiniCPM5 `maxTokens` 从 4096 降为 512,增加硬安全边界。

### 实施过程中的错误
- 首次长 Python 编辑脚本因三引号未闭合报 SyntaxError,发生在写文件前,未产生部分修改;随后改用 `apply_patch`。
- 首次编译暴露一个显式 `ProviderConfig` 初始化器缺 `generation`;补 `generation: None` 后通过。
- 首次请求测试使用精确浮点比较失败;确认字段已序列化后改为容差比较。

### 验证
- 新增测试 3/3 passed。
- fmt/check/clippy 均 exit 0。
- 新二进制安装成功。
- 真实 Pi smoke exit 0,最终 stopReason 为 stop。
