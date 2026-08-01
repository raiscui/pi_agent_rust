# Issue: anthropic protocol provider has silent usage reporting and thinking-block mis-detection against non-Anthropic services (e.g. MiniMax-M3 anthropic endpoint)

## 状态

- 复现: 2026-08-01
- 项目: raiscui/pi_agent_rust (本地 `cargo build` target/debug/pi, 7/27 编)
- 触发模型: `MiniMax-M3` via `https://api.minimaxi.com/anthropic/v1/messages`
- 同一模型走 OpenAI 协议 (`https://api.minimaxi.com/v1/chat/completions`) 正常
- 跨大模型 v2.23 darwin 评测 (Bonsai-demo pi-bonsai-rdog-calculator) strict 通过数: OpenAI 协议 3/3, anthropic 协议 1/3

## 现象 1: usage 字段 `input=0, cache_read=0, cache_write=0`,只有 `output` 有值

artifact 44 (anthropic) happy-path 在 pi-events.jsonl 输出:
```json
{
  "usage": {
    "input": 0,
    "output": 2147,
    "cacheRead": 0,
    "cacheWrite": 0,
    "totalTokens": 0,
    "cost": { "input": 0.0, "output": 0.0, "cacheRead": 0.0, "cacheWrite": 0.0, "total": 0.0 }
  }
}
```

OpenAI 协议同一模型 (artifact 45) 正常:
```json
"usage": { "input": 45346, "output": 1179, "cacheRead": 36480, "cacheWrite": 0, "totalTokens": 46525 }
```

## 现象 2: 模型在 turn 24 输出 "Handoff" 文档导致 stopReason 提前终止,任务 0 action 完成

artifact 44 (anthropic) happy-path 跑了 24 turn 但 `performedActionTimeline: []`,`performedStepCount: 0`,`observedValues: ["0"]`。Pi 端在 turn 24 看到模型输出 Handoff 文档后停。

artifact 45 (OpenAI) 同一 prompt 6 步完成,`performedActionTimeline: ["1","加","2","乘","3","等于"]`。

## 根因分析(代码定位)

### Bug A: `AnthropicUsage.input` 字段不是 `Option<u64>`

`src/providers/anthropic.rs:1195-1201`:
```rust
#[derive(Debug, Deserialize)]
struct AnthropicUsage {
    #[serde(rename = "input_tokens")]
    input: u64,                                   // <-- 不是 Option
    #[serde(default, rename = "cache_read_input_tokens")]
    cache_read: Option<u64>,
    #[serde(default, rename = "cache_creation_input_tokens")]
    cache_write: Option<u64>,
}
```

如果 MiniMax streaming `message_start` 事件**不带** `usage` 字段(只在 `message_delta` 带 `output_tokens`),`handle_message_start` 在 842 行 `if let Some(usage) = message.usage` 不进入,`input` / `cache_read` / `cache_write` 全部保持 `partial.usage` 的默认值 0。

但 anthropic.rs:1034-1047 的 `handle_message_delta` 直接 set `output`:
```rust
if let Some(u) = usage {
    self.partial.usage.output = u.output_tokens;
}
```

所以最终 `output_tokens` 有值,`input_tokens` / `cache_read` / `cache_write` 全 0。

### Bug B: anthropic 协议下 thinking 行为没正确处理 MiniMax 的"合成 thinking"

MiniMax-M3 的 anthropic 协议 streaming 返回:
- 不发出独立 `content_block_start { type: "thinking" }` 块
- 把 thinking 直接放进 `text` 块,格式 `<think>...</think>\n\n[正文]`

Pi 客户端把整个 text 当作模型输出文本。模型看到自己的 output 里包含 `<think>...</think>` 和 `# Handoff - Calculator 1+2*3 Task` 文档,产生"上一个 agent 写到这,我要做 next agent 接手"的多 agent 假设,导致 stopReason 提前终止。

OpenAI 协议下 MiniMax 同样把 thinking 放进 content,但 Pi 客户端已经对 OpenAI 的 `content` 字段做了 thinking 提取(`<` 标签解析)或者至少 model 不会把同一 content 当作 handoff 输入。

## 建议修复(从小到大)

### 修复 1: 让 `AnthropicUsage` 字段容错

```rust
struct AnthropicUsage {
    #[serde(default, rename = "input_tokens")]
    input: u64,
    #[serde(default, rename = "cache_read_input_tokens")]
    cache_read: u64,    // <-- 改 Option 为 default 0
    #[serde(default, rename = "cache_creation_input_tokens")]
    cache_write: u64,   // <-- 改 Option 为 default 0
}
```

虽然现在没 Option,应该可以反序列化。但更稳的:在 `handle_message_start` 里把 `input/cache_read/cache_write` 全部 `unwrap_or(0)`。

### 修复 2: anthropic 协议下 thinking 标签提取

`handle_content_block_delta` 处理 `TextDelta` 时,如果 text 包含 `<think>...</think>` 标签,自动 split 出 thinking content 放进 thinking block,只把正文当作 text 输出。

参考 OpenAI 协议处理 (src/providers/openai.rs 类似路径, MiniMax-M3 OpenAI 跑通)。

### 修复 3: 文档声明协议支持矩阵

在 `README.md` / `docs/providers.md` 加表:
- OpenAI 协议: 完全支持(usage / tool_calls / cache 字段 / thinking)
- Anthropic 协议: 假定 message_start 必带 usage, thinking 块必为独立 content_block(只有 Anthropic 官方 API 严格遵守, 第三方可能不)

## 复现步骤

1. `~/.pi/agent/models.json` 配 provider:
   ```json
   "minimax-cn-anthropic": {
     "baseUrl": "https://api.minimaxi.com/anthropic/v1/messages",
     "api": "anthropic-messages",
     "apiKey": "env:MINIMAX_CN_API_KEY",
     "models": [{ "id": "MiniMax-M3", "toolUseProfile": "rdog-control-bash" }]
   }
   ```
2. 跑 `Bonsai-demo/.scratch/pi-bonsai-rdog-calculator/runner/run_calculator_eval.py` with provider=minimax-cn-anthropic
3. 看 `pi-events.jsonl`,usage 全 0
4. 看 `suite-result.json`,3 case 只 1/3 strict

## 对比验证

- 同样模型走 OpenAI 协议: artifact 45 3/3 strict,usage/cacheRead 正常

## 优先级

中-高。影响所有用非 Anthropic 官方 API 跑 anthropic 协议的用户(MiniMax / 各种转发服务 / Bedrock / Vertex AI 也可能有类似问题)。

## 相关

- Bonsai-demo/.scratch/pi-bonsai-rdog-calculator/artifacts/44-canonical-v2.23-darwin-minimax-m3-fresh-model-iter30-temp0/(anthropic 1/3)
- Bonsai-demo/.scratch/pi-bonsai-rdog-calculator/artifacts/45-canonical-v2.23-darwin-minimax-m3-openai-protocol-iter30-temp0/(OpenAI 3/3)
- WORKLOG__darwin_calculator.md 2026-08-01 条目
