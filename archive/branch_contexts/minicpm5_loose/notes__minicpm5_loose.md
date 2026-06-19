## [2026-06-05 16:31:44] [Session ID: omx-1780470665249-tkxhle] 笔记: loose smoke test 结果

### 运行方式

- 脚本: `/tmp/pi_minicpm5_loose_matrix.py`
- 参数: `--trials 1 --timeout 120`
- 模型: `/Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/MiniCPM5-1B`
- Server: `http://127.0.0.1:18081/v1`

### 结果

- 总 trial: 5
- 成功: 2
- 漂移: 3
- 漂移率: 60%

### 典型现象

- `read`: 成功, 但回答有轻微口头包装, 没有只输出原文。
- `grep`: 工具成功, 但 post-tool 阶段重复扩写并超过等待窗口。
- `find`: 工具路径/结果漂移, 未形成成功闭环。
- `ls`: 成功。
- `edit`: 工具错误, 模型后续解释里暴露路径理解漂移。

### harness 修正

- `grep` 这种长文本跑飞之前被归为 `tool_success_no_agent_end`。
- 修正后会优先归为 `post_tool_runaway_text`, 更贴近真实漂移类型。

## [2026-06-05 16:56:00] [Session ID: omx-1780470665249-tkxhle] 笔记: loose 10 轮/工具正式回归统计

### 运行方式

- 脚本: `/tmp/pi_minicpm5_loose_matrix.py`
- 参数: `--trials 10 --timeout 90`
- 总 trial: 50
- 输出目录: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-loose-matrix-da30nebi`
- Summary: `/var/folders/58/3f9_69ts3bx4slnb8tgl572m0000gn/T/pi-minicpm5-loose-matrix-da30nebi/summary.json`

### 总体统计

- 成功: 17 / 50
- 漂移: 33 / 50
- 总漂移率: 66%

### 分类统计

- `tool_success`: 17
- `tool_error`: 18
- `tool_success_no_agent_end`: 7
- `final_answer_mismatch`: 4
- `post_tool_runaway_text`: 2
- `no_tool_call`: 2

### 按工具统计

| 工具 | 成功 | 漂移 | 漂移率 | 主要漂移类型 |
| --- | ---: | ---: | ---: | --- |
| `read` | 3/10 | 7/10 | 70% | post-tool runaway, final answer mismatch, no agent_end |
| `grep` | 5/10 | 5/10 | 50% | tool_success_no_agent_end, final answer mismatch |
| `find` | 0/10 | 10/10 | 100% | tool_error |
| `ls` | 9/10 | 1/10 | 10% | tool_success_no_agent_end |
| `edit` | 0/10 | 10/10 | 100% | tool_error, no_tool_call |

### 代表样本

- `read#2`: 工具调用成功后文本跑飞, 出现 `P1→P2` 和大量重复 `content`, 没等到 `agent_end`。
- `read#4`: 最终回答把 `PI_MINICPM5_LOOSE_READ_OK_04` 幻写成 `PII_MINICPM5_LOOSE_READ_OK_04`。
- `find#1-3`: `find.path` 生成 `.**`, 导致工具报 `Path not found`。
- `edit#1-2`: `edit.path` 生成 `../loose_edit_XX.txt`, 被 cwd scope 拦截为 outside working directory。
- `edit#4`: 无真实 tool call, 口头声称已经替换。
- `edit#6`: 无真实 tool call 且长文本重复解释, 没等到 `agent_end`。

### 结论

- 在弱约束自然语言下, MiniCPM5-1B 的通用 tool-use 不稳定。
- `ls` 最稳, `grep` 中等, `read` post-tool 稳定性仍弱, `find/edit` 在弱约束下基本不可用。
- 这份统计不推翻 focused 5/5 结果; 它说明弱约束 prompt 下的漂移率很高。
