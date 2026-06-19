# 讨论存档: 把 rdog-control 做成 pi_agent_rust 跨客户端 MCP tool 的可行性

- 日期: 2026-06-18
- Session ID: omx-1781751290523-tk9ugc
- 触发: 用户希望把 rdog-control skill 转化为 pi_agent_rust 原生内置 tool, 以加速 computer-use 操控桌面。
- 阶段: deep-interview → ultragoal(aggregate mode)
- ultragoal 落点: `G001-pi-agent-rust-rdog-control-mcp-c-pha` in `.omx/ultragoal/goals.json`
- Codex goal: threadId `019ed938-17b9-7d93-8c1b-4d1cfc95de8c`, status active
- 路径选定: **C' (MCP 高层, 3-5 个 tool)** — 因为用户 Q0 答"多客户端"。

## 1. 用户原始问题 (原话)

> 我需要将 $rdog-control 也就是 /Users/cuiluming/.codex/skills/rdog-control 转化为 PI agent rust 原生内置 tool ,以便加速 rdog-control computer use 操控桌面的速度,比如无需收到指令后才载入 skill。首先我想知道的是 这是不是一个好方法(指的是转成 内置 tool call) ,其次,如果是最佳方法,我需要你分析可行性,制定落地实现方法。

## 2. 用户后续追问 (决定分析方向)

> 将 制作成 MCP 也考虑进去呢?也就是 用 skill 还是 tool call 还是 mcp

> symlink 预加载skill,  在 执行 bash tool 调用 rdog 的结果处理上, skill的话,是 model 解析, 其他是程序化解析,这点  skill形式是否比其他形式慢? 我所在意的不是 多一些JSON-RPC 编解码 这种程序运行耗时,而是 是否增加 model req res 轮数? model 一轮的耗时是非常高的,这比程序运行耗时要重的多

> 先将当前讨论进度保存到  docs/discuss/， 然后 进行  Phase 0 ， prompt 用"在左侧的chrome浏览器窗口新建标签，打开 www.xiaohongshu.com ，并点击左侧列表中的'首页'刷新内容" model server是已经在跑的 .venv/bin/python3 mlx_lm_server.py --host 127.0.0.1 --port 18081 pi agent 使用 pi --provider local --model /Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/Qwen3.5-2B-OptiQ-4bit pi --provider local --model /Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/gemma-4-e2b-it-qat-OptiQ-4bit 两个模型 做基准测试

> Q0 (决定 Phase 1 方向): 多客户端 → 路径 C'
> $oh-my-codex:ultragoal  你来跑  Phase 0

## 3. 关键事实 (代码摸底)

### 3.1 pi_agent_rust 端

- 8 个 built-in tool 定义在 `src/tools.rs` (12816 行): read / write / edit / bash / grep / find / ls / hashline_edit。
- `pub trait Tool: Send + Sync` 在 `src/tools.rs:159`, 签名是 name/label/description/parameters(JSON Schema)/execute/effects。
- 注册走 `ToolRegistry::new(enabled, cwd, config)` 硬编码白名单 (`src/tools.rs:2664-2683`), `enabled` 来自 CLI `--tools`, 默认 `"read,bash,edit,write,grep,find,ls,hashline_edit"` (`src/cli.rs:418`)。
- skill 加载: `format_skills_for_prompt()` 在 `src/resources.rs:1278-1306`, 把 `<available_skills>` 块塞进 system prompt, 只列 name+description+file_path, **不内联 SKILL.md 内容**。agent 要拿协议细节必须 `read` SKILL.md。
- skill 路径: `cwd/.pi/skills/` + `~/.pi/agent/skills/` (`src/config.rs:1029-1037`)。`~/.pi/agent/skills/` 当前是空目录。
- 显式注入 skill 的入口: `--skill <path>` 可重复 (`src/cli.rs:540-555`)。
- `Cargo.toml` 完全无 rustdog / rdog 依赖。

### 3.2 rdog-control skill 端

- SKILL.md 233 行 + 4 份 references 共 1235 行 = 1468 行 markdown。
- 30+ 种 line-control 命令 (@ping / @bootstrap / @capabilities / @observe / @window-find / @ax-action / @ax-press / @ax-set-value / @ax-scroll / @ax-focus / @type-text / @click / @drag / @wheel / @mouse-move / @mouse-button / @key / @paste / @web-find / @web-act / @gui-bench / @selector-get / @selector-resolve / @selector-refind / @pty / @savefile / ...)。
- 决策树: GUI agent recipe 8 步 (bootstrap → capabilities → observe → locate → activate → semantic action → verify → mouse fallback)。
- 错误码 64/70/77/78, observation ref 短生命周期, selector_id 持久, window_ref 短生命周期, observation_id 配对使用, selector 状态机 rebound/needs_disambiguation/blocked/not_found。

### 3.3 rustdog 仓库端

- 仓库 `Cargo.toml` 声明 `rustdog = 3.0.0`, **不是** pi_agent_rust 的 workspace 成员。
- `src/control_protocol.rs` 已经有完整 Rust 协议层: `ControlCommand` enum 覆盖所有 30+ 命令, 每个有结构化 Request 类型。
- 关键阻塞: 所有协议类型当前 `pub(crate)`, **不能从外部 crate 复用**。
- `rdog` binary 已安装: `/Users/cuiluming/.cargo/bin/rdog` v3.0.0。

### 3.4 MCP 现状 (用户追问后补充)

- pi_agent_rust 有 `registerMcpServer` API, 但**只是占位**。`__pi_register_mcp_server` (`src/extensions_js.rs:18709`) 把 spec push 到 `mcp_servers: Vec<Value>`, **没有任何 spawn 子进程 / stdio 连接 / tools/list / tools/call 实现**。
- pi_agent_rust `Cargo.toml` 0 个 `rmcp` 依赖。
- rustdog 仓库 0 个 `rmcp` 依赖, 0 个 `#[tool]` 标记。
- `tests/ext_conformance/artifacts/base_fixtures/minimal_mcp/index.ts` 是 "if we support it natively" 占位 fixture。
- **结论: MCP 在两边都是 0 状态, 不是"已有但不够"。**

## 4. 按 model 轮数重新对齐三选一

用户纠正: 真正瓶颈是 model req-res 轮数 (秒级), 不是程序运行毫秒级。

| 路径 | model 轮数(典型 GUI 任务) | context 膨胀 | 错误码处理轮 | 总耗时估 |
|---|---|---|---|---|
| A. Skill (现状) | 8-12 轮 | 2× SKILL.md 读入 (~3000 行) | +2-3 轮 (model 解析 stderr) | 60-180s |
| B. Tool call (高层 3-5 个) | **1-2 轮** | 5 tool schema (~500 tokens) | 0 轮 (结构化) | **5-15s** |
| C. MCP (1:1 翻译 30+ tool) | 5-8 轮 | 30+ tool schema (~3-5k tokens) | +1-2 轮 | 50-150s |
| C'. MCP (高层 3-5 个) | **1-2 轮** | 5 tool schema (~500 tokens) | 0 轮 | **5-15s** |

关键洞察:
- 真正能减少 model 轮数的是"高层 API 抽象", 不是"传输层抽象"。
- Tool call (B) 和 MCP-高层 (C') 的 5-10× 加速都是真的。两者核心机制相同: 把决策树和错误码解析从 model 端移到 Rust 端。
- C (1:1 翻译 MCP) 失败原因: 把 30+ line-control 命令 1:1 转 30+ MCP tool, 决策树外溢到 model 端, 轮数和 skill 一样。
- MCP 的真正价值不是"单客户端速度", 而是"跨客户端复用"。MCP 路径反而多 1-5ms stdio JSON-RPC 边界。

## 5. 路径选择决策

按用户实际使用场景分叉:

- **只 pi_agent_rust 用** → 路径 B (Tool call)
- **多客户端共享 (Claude Desktop / Cursor / Zed 等)** → 路径 C' (MCP 高层) ← **本 run 选定**
- **rdog 想成为通用远程控制协议** → C' + B 兼容 (同时实现两种)

## 6. ultragoal run 启动 (2026-06-18 15:09)

- 旧 `.omx/ultragoal/goals.json` 残留 minicpm5 主题 54 个 goal, 备份到:
  - `.omx/ultragoal/goals.minicpm5-pre-rdog-20260618.jsonl.bak`
  - `.omx/ultragoal/ledger.minicpm5-pre-rdog-20260618.jsonl.bak`
- `omx ultragoal create-goals --force --brief "..."` 创建 1 个 G001。
- `omx ultragoal complete-goals` 拿 handoff, 确认 aggregate objective。
- `get_goal` 返回 `goal: null` (前次 run 残留未激活), 所以 `create_goal` 建立新 active Codex goal, threadId `019ed938-17b9-7d93-8c1b-4d1cfc95de8c`。

### 当前环境事实 (摸底)

- `~/.cargo/bin/rdog` v3.0.0 已装。
- `rdog daemon` 当前**没在跑** (`pgrep` 0 命中)。
- `~/.pi/agent/skills/` 空目录。
- MLX server (PID 19731) 加载的是 `NVIDIA-Nemotron-3-Nano-4B-OptiQ-4bit` 和 `MiniCPM5-1B-OptiQ-4bit`, **不是** Qwen3.5-2B-OptiQ-4bit 和 gemma-4-e2b-it-qat-OptiQ-4bit。
- pi_agent_rust `models.json` 中 `provider "local"` (line 139) 已注册 Qwen3.5-2B-OptiQ-4bit (line 165) 和 gemma-4-e2b-it-qat-OptiQ-4bit (line 201), 但 server 端没这些 model。

### 阻塞 (前置于阶段 6+)

1. **macOS 权限**: rdog daemon 需要 Accessibility + Screen Recording 权限, 用户必须在系统设置手动授予。
2. **MLX server 单 model**: 一次只能 load 一个, 测两个 model 必须"杀-启-测"两次。
3. **真实 GUI 操作**: Phase 0 benchmark 会真改 chrome 窗口状态, 是 destructive side effect, 需要用户授权。

## 7. Phase 0 计划 (G001 子任务)

按 ultragoal G001 brief, Phase 0 拆解:

- 阶段5: 落盘 `docs/discuss/rdog-control-as-builtin-tool-20260618.md` (本文件)
- 阶段6: kill MLX server PID 19731, 加载 Qwen3.5-2B 重启
- 阶段7: 启动 rdog daemon (需要 macOS 权限先)
- 阶段8: 创建 skill symlink `~/.pi/agent/skills/rdog-control.md`
- 阶段9: 跑 `pi --provider local --model ...Qwen3.5-2B-OptiQ-4bit` benchmark
- 阶段10: kill+restart MLX server 加载 gemma-4-e2b
- 阶段11: 跑 `pi --provider local --model ...gemma-4-e2b-it-qat-OptiQ-4bit` benchmark
- 阶段12: 落盘 `docs/discuss/phase0-baseline-20260618.md` 报告
- 阶段13: 决策文档化 (Phase 1+ 启动/不启动)
- 阶段14: `ai-slop-cleaner` + `$code-review` (final gate)
- 阶段15: `update_goal({status:complete})` + 最终 checkpoint

## 8. 已知风险 / 待澄清

- macOS 权限授予需要用户在系统设置里手动操作, agent 不能代劳。
- MLX server 是单 model server, 测两个 model 需要"杀-启-测"两次。
- 当前 18081 server 上 Nemotron + MiniCPM5 仍在用, 杀掉会影响其它正在跑的 pi session。
- Phase 0 benchmark 会真实影响 chrome 窗口, 用户必须明确授权。

## 9. 后续讨论入口

- 下次继续时先读 `docs/discuss/rdog-control-as-builtin-tool-20260618.md` (本文件)。
- 接着读 `.omx/ultragoal/goals.json` + `.omx/ultragoal/ledger.jsonl` 看 G001 进度。
- baseline 数据落在 `docs/discuss/phase0-baseline-20260618.md`。
