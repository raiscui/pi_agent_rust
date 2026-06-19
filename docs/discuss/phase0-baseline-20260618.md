# Phase 0 Baseline Report: rdog-control skill 在 pi_agent_rust 下的 model 行为

- 日期: 2026-06-18
- Session ID: omx-1781751290523-tk9ugc
- ultragoal G001 阶段: 5-11 进展
- 报告作者: pi_agent_rust ultragoal run agent
- 实际执行者: 真实 shell + pi binary (v0.1.18), MLX server PID 19731 (hot-swap mode)
- 关联文件: `docs/discuss/rdog-control-as-builtin-tool-20260618.md`

## 1. 报告范围 (诚实声明)

本报告**只覆盖 text-mode + 无 rdog daemon 场景**下的 model 行为 baseline。
**GUI 真实路径 baseline 未跑**——rdog daemon 当前未启动, macOS Accessibility + Screen Recording 权限需要用户手动授予, 真实 GUI 操作会改用户 chrome 窗口状态, 属于 destructive side effect, 需要用户明确授权才能跑。

**本报告回答的核心问题**: 在 rdog daemon 缺失场景下, pi_agent_rust 看到 `<available_skills> rdog-control` 时, 弱本地模型 (Qwen3.5-2B / Gemma-4-E2B) 会走什么路径?

**未回答**: rdog daemon 在跑 + macOS 权限齐备 + chrome 打开的真实场景下, model 跑出 GUI 任务需要多少轮。

## 2. 测试环境

- MLX server: `127.0.0.1:18081` (PID 19731), 当前 加载 Nemotron + MiniCPM5
- hot-swap 验证: server 接受请求体 `model` 字段动态 load, 不需要 kill+restart
- pi binary: `/Users/cuiluming/.cargo/bin/pi` (从 `/Users/cuiluming/local_doc/l_dev/my/rust/pi_agent_rust` `cargo install`)
- skill symlink: `~/.pi/agent/skills/rdog-control.md -> /Users/cuiluming/local_doc/l_dev/my/rust/rustdog/.codex/skills/rdog-control/SKILL.md` (2026-06-18 15:13 创建)
- rdog daemon: **未跑** (`pgrep -lf "rdog daemon"` 0 命中)
- models.json: `~/.pi/agent/models.json` 已注册 Qwen3.5-2B-OptiQ-4bit (line 165) 和 gemma-4-e2b-it-qat-OptiQ-4bit (line 201), 都用 `provider "local"` (line 139, baseUrl 18081)

## 3. 测试方法

每个模型各跑 1 次, 命令:
```
cd /Users/cuiluming/local_doc/l_dev/my/rust/pi_agent_rust
timeout 60 pi --provider local --model <model-path> -p "<user prompt>"
```

- 强制 60 秒 timeout, 防止 model 卡死挂住 agent
- stdout / stderr 分开捕获
- user prompt (用户原话): "在左侧的chrome浏览器窗口新建标签,打开 www.xiaohongshu.com ,并点击左侧列表中的'首页'刷新内容"

## 4. Baseline 数据

### 4.1 Qwen3.5-2B-OptiQ-4bit

- 启动时间: 2026-06-18 15:15 (~37-60 秒范围, 中间重试过)
- exit code: 0 (一次) / 124 (另一次, timeout 杀)
- stdout 30-157 字节, 主要内容:
  - "Failed to create new tab URL"
  - "/opt/homebrew/bin/bash: timeout 10s firefox --new-tab=/www.xiaohongshu.com: No such file or directory"
  - "Firefox command failed, trying Chrome with new-tab..."
- stderr 502 字节 trace, 关键事件:
  - `pi.provider.factory.select` route=api:openai-completions
  - `rewrote repeated profiled tool call into final tool-result text tool_name=bash tool_arguments={"command":"rtk bash \"timeout 10s firefox --new-tab=/www.xiaohongshu.com\" || echo \"Firefox command failed, trying Chrome with new-tab...\""}`
- **关键观察**:
  - Qwen3.5-2B 调了 `bash` tool 试图 firefox 开新 tab
  - 触发了 `toolUseProfile: weak-openai-compatible` 的 `rewriteRepeatedSuccessfulToolCall` 规则
  - **没看到 read SKILL.md 调用**——model 没用 rdog-control skill
  - 没用 rdog daemon, 用 firefox bash 直撞
- **行为分类**: "乱调 tool 路径" (model 轮数 ≥ 2, 含 tool call)
- **失败原因**: firefox 不在 system PATH, 也没有 rdog skill fallback

### 4.2 gemma-4-e2b-it-qat-OptiQ-4bit

- 启动时间: 2026-06-18 15:18
- 耗时: 18.6 秒
- exit code: 0
- stdout 650 字节, 完整内容:

  > 我是一个 AI 助手，我无法直接控制您本地的 Chrome 浏览器或任何外部应用程序的界面操作，例如新建标签页或刷新网页内容。
  >
  > 我只能通过您向我提供的代码或文件进行编辑、搜索或分析。
  >
  > 如果您希望我帮助您完成与 **www.xiaohongshu.com** 相关的**代码或信息**工作，请告诉我具体的需求，例如：
  >
  > 1. **您想找什么信息**（例如，关于该网站的 RSS 接口或 API 文档）？
  > 2. **您想写什么代码**来与该网站交互（例如，使用 Python 的 `requests` 库）？
  >
  > 请告诉我您希望我如何使用我现有的工具来帮助您。

- stderr 0 字节 (没触发任何 trace)
- **关键观察**:
  - **Gemma 直接 LLM 答了**, **没调任何 tool** (没 bash, 没 read, 没 SKILL)
  - Gemma 诚实说"我没法直接控制浏览器"
  - Gemma 反问用户给更具体需求
- **行为分类**: "不调 tool 路径" (model 轮数 = 1)
- **耗时最短 (18 秒)** 远远优于 Qwen3.5 (37-60+ 秒卡死)

## 5. 关键发现

### 5.1 两个 model 行为天差地别

| 维度 | Qwen3.5-2B | gemma-4-e2b |
|---|---|---|
| 调 tool? | 是 (firefox bash) | 否 (直接 LLM 答) |
| 用 rdog skill? | 否 | 否 (没读 SKILL.md) |
| 耗时 | 37-60+ 秒 (部分 timeout) | 18 秒 |
| 任务完成度 | 失败 (firefox 不在) | "诚实拒绝" |
| model 轮数 | ≥ 2 | 1 |

**对用户原始问题的回答**: "skill 形式是否比其他形式慢?"

- **在弱 model 上, skill 形式完全没用上**——两个 model 都没 read SKILL.md。
- **Gemma 走"不调 tool"路径**反而最稳——只 1 轮 18 秒, 不会出现乱调 tool 卡死。
- **Qwen3.5 走"乱调 tool"路径**——试图 firefox bash, 失败, profile 强制 rewrite, 卡死或慢。
- **完全没有出现 "skill 路径" 8-12 轮的预期**——因为 model 太弱根本不会想到调 rdog skill。

### 5.2 pi -p 模式稳定性问题

- Qwen3.5-2B 在 "say hi" 这种最简单 prompt 下也卡 60 秒被 timeout 杀 (exit=124)。
- stderr 0 字节, stdout 0 字节——pi 启动后没正常退出。
- **这是 pi 自身 print mode 退出机制的 bug 或不稳定**, 与 model / skill 路径无关。
- 影响: 用 pi -p 做 benchmark 不可靠, 需要改用 pi --mode rpc (JSON-RPC over stdio) 才能拿到完整数据。

### 5.3 toolUseProfile: weak-openai-compatible 行为

- 对 Qwen3.5 生效: 触发 `rewriteRepeatedSuccessfulToolCall` 把 `rtk bash "..." || echo "..."` 这种带 fallback 的命令 rewrite 成 final tool-result text, **避免重复 tool call**。
- 对 Gemma 未触发 (Gemma 没调 tool)。
- 推测: profile 是为弱 model 设计的兜底, 但只在"model 真的想调 tool"时才会起作用。

## 6. 决策: Phase 1+ 是否启动?

### 6.1 当前 evidence 支持的结论

**在弱本地 model + 无 rdog daemon 场景下, "skill 形式 vs tool call 形式 vs MCP 形式" 的对比没法用**, 因为:
- model 太弱不会主动用 rdog skill
- rdog daemon 缺失, 即使 model 决定调也调不通
- 真实场景需要 daemon + macOS 权限 + 真实 chrome

### 6.2 用户关心的问题(在意 model 轮数)的部分回答

- Gemma 在该 prompt 下 model 轮数 = 1 (LLM 直答), 不会因 rdog-control 而变多
- Qwen3.5 在该 prompt 下 model 轮数 ≥ 2 (tool call), 触发了 profile rewrite 但仍慢
- **两个 model 都不会因 rdog-control skill 而轮数爆炸**——因为它们根本没用 skill

### 6.3 真正的"model 轮数 vs 形式"对比需要的条件

| 条件 | 当前 | 需要 |
|---|---|---|
| rdog daemon 跑 | ❌ | ✅ 启动 daemon + 授权 macOS 权限 |
| chrome 浏览器 | ❌ 不确定 | ✅ 打开 chrome, 左侧能看到 xhs |
| model 知道 rdog skill 存在 | ⚠️ symlink 已建, 但 model 没用上 | ✅ 强 model (Gemma 3 27B+) 或显式 prompt 提示 |
| pi -p 稳定退出 | ❌ 卡 60s | ✅ 改 pi --mode rpc 或交互模式 |

**当前 evidence 不够做 Phase 1+ 的 go/no-go 决策**。需要 GUI 路径 baseline 才能完整回答 user 问题。

### 6.4 推荐 follow-up 路径

**Phase 0.5 (推荐先做)**:
1. 用户手动到 macOS 系统设置 → 隐私与安全性 → 辅助功能 / 屏幕录制, 授权 rdog binary
2. 启动 rdog daemon: `rdog daemon --config /Users/cuiluming/local_doc/l_dev/my/rust/rustdog/rdog_macos.toml`
3. 跑同样的 2 个 model benchmark, 这次会真触发 rdog 路径
4. 比较"skill 路径"在强 model (Claude Opus 4 / Sonnet 4) vs 弱 model 下的真实 model 轮数

**Phase 1+ (Phase 0.5 跑完后再决定)**:
- 如果 baseline 显示 "skill 路径" 真实轮数 = 8-12 轮: 路径 C' (MCP 高层 3-5 个 tool) 是值得投入的
- 如果 baseline 显示 "skill 路径" 真实轮数 ≤ 4 轮: skill 形式够用, Phase 1+ 不必启动

## 7. Follow-up 命令清单 (用户跑 GUI baseline 用)

```bash
# 1. 启动 rdog daemon (前置: macOS 权限已授权)
RDOG_DIR=/Users/cuiluming/local_doc/l_dev/my/rust/rustdog
nohup $RDOG_DIR/target/debug/rdog daemon --config $RDOG_DIR/rdog_macos.toml \
   > /tmp/rdog_daemon.log 2>&1 &
DAEMON_PID=$!
echo "rdog daemon pid: $DAEMON_PID"
sleep 3

# 2. 验证 daemon 能力
printf '@ping\n@capabilities\n' | rdog control mac.lab
# 期望: @response {"kind":"capabilities",...} 含 screenshot / accessibility / window_control / mouse_input 都 ok

# 3. 跑 pi benchmark (建议用 --mode rpc 而非 -p, 拿完整数据)
cd /Users/cuiluming/local_doc/l_dev/my/rust/pi_agent_rust
# 见 docs/discuss/rdog-rpc-bench.py (待写, 简化建议如下)
python3 docs/discuss/rdog-rpc-bench.py \
   --model /Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/Qwen3.5-2B-OptiQ-4bit \
   --prompt "在左侧的chrome浏览器窗口新建标签,打开 www.xiaohongshu.com ,并点击左侧列表中的'首页'刷新内容" \
   --timeout 300 \
   1>/tmp/pi_qwen_gui.out 2>/tmp/pi_qwen_gui.err
# 同理跑 gemma-4-e2b

# 4. 收集 model 轮数
grep -c "Assistant message" /tmp/pi_qwen_gui.out
grep -c "rdog control" /tmp/pi_qwen_gui.out
grep -c "read.*rdog-control.md" /tmp/pi_qwen_gui.out
```

## 8. 给用户的问题 (供 Phase 0.5 决策)

- Q1: 是否愿意手动授权 rdog macOS 权限 (辅助功能 + 屏幕录制)?
- Q2: chrome 是否当前在跑且左侧能看到 xhs?
- Q3: 是否接受 rdog daemon 启动后会真实改 chrome 窗口状态?
- Q4: 接受后, 是否要我写一个 pi --mode rpc 模式的 benchmark 脚本 (docs/discuss/rdog-rpc-bench.py) 自动化 GUI baseline 收集?

如果 Q1-Q4 都答 "是", Phase 0.5 在用户授权下可以由 agent 跑; 如果 Q1-Q3 答 "否", Phase 0.5 必须用户手动跑。

## 9. ultragoal G001 状态

- 阶段 5-6-8 完成: docs/discuss 落盘 + MLX hot-swap 验证 + skill symlink
- 阶段 7 (启动 rdog daemon) blocked on macOS 权限
- 阶段 9-11 (跑 pi benchmark) 部分完成: text-mode baseline 2 个 model 都跑过, GUI benchmark blocked on daemon
- 阶段 12-13 部分完成: 本报告 + 决策部分 (Phase 0.5 待跑)
- 阶段 14-15 (final gate + checkpoint) 留待 Phase 0.5 完成后做

## 10. 已知遗留 / 限制

- pi -p 模式稳定性问题 (5.2) 仍是阻塞, 即使 GUI 路径通了, 也需要 --mode rpc 模式才能稳定 benchmark。
- rdog daemon 启动需要 macOS 权限, 这是 deep AI agent 不能代劳的硬阻塞。
- 本报告基于 1 次 / 模型的样本, 不是 3 次均值, 结论置信度有限, 留作 Phase 0.5 验证。
- baseline 数据没体现"多客户端"价值 (Claude Desktop / Cursor 等), 那部分需要 Phase 1+ 启动后单独评估。
