## [2026-06-05 16:56:00] [Session ID: omx-1780470665249-tkxhle] 后续建议: 如果要降低 loose 漂移率

### 可选方向
- 针对 `find`: provider-local prompt/schema 明确禁止 `path=.**`, 当前目录应使用 `path=.` 或省略 path。
- 针对 `edit`: provider-local prompt/schema 强化 `path` 必须是当前目录相对文件名, 禁止 `../file.txt`。
- 针对 post-tool: 继续压缩 local-minicpm5 的工具返回后回答协议, 尤其是 read/grep 的行号/hashline 元数据解释。
- 针对 no tool call: 对文件修改类任务增加更硬的 provider-local append prompt, 禁止口头声称已修改。

### 暂不建议
- 不建议把 `write` 或任一单工具做成特殊个例。
- 不建议仅靠更宽松的 harness 判定成功, 因为 drift 里存在真实 tool error 和无 tool call。
