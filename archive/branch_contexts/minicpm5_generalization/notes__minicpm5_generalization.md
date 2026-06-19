
## [2026-06-07 21:03:18] [Session ID: omx-1780470665249-tkxhle] 笔记: models.json 当前结构与 profile 承载点

### 代码事实
- `src/models.rs` 当前 `ModelsConfig` 只有 `providers: HashMap<String, ProviderConfig>`。
- `ProviderConfig` 有 `baseUrl/api/apiKey/headers/authHeader/compat/models`。
- `ModelConfig` 有 `id/name/api/reasoning/input/cost/contextWindow/maxTokens/headers/compat`。
- 当前没有显式 `deny_unknown_fields`, 所以新增顶层字段在 serde 默认行为下不会直接破坏旧配置, 但如果要读取必须加字段。

### 设计压力点
- 用户明确要求 profile 具体配置在配置文件, 不是写死在代码。
- 如果放 `models.json` 顶层, 可以形成 `toolUseProfiles` 定义表 + model/provider 引用。
- 如果放 provider 下, profile 更接近 provider-local 配置, 但跨 provider 复用性差。
- 如果单独文件, 边界清晰但新增文件路径和加载顺序, 对第一阶段成本更高。

## [2026-06-08 14:46:56] [Session ID: omx-1780470665249-tkxhle] 笔记: Round 3 后的候选配置形态

### 用户已确认
- `toolUseProfiles` 放在 `models.json` 顶层。
- 模型或 provider 通过名称引用 profile。
- profile 具体规则不能写死在 Rust 内部。

### 候选 JSON 形态
```json
{
  "toolUseProfiles": {
    "weak-openai-compatible": {
      "appendSystemPrompt": "...",
      "pathSchema": { "...": "..." },
      "argumentRepair": { "...": true },
      "postToolGuard": { "...": true }
    }
  },
  "providers": {
    "local-minicpm5": {
      "models": [
        {
          "id": "./models/MiniCPM5-1B",
          "toolUseProfile": "weak-openai-compatible"
        }
      ]
    }
  }
}
```

### 仍未定
- `toolUseProfile` 只允许 model-level, 还是 provider-level 也可设置默认 profile。
- 第一阶段是否要把用户当前 `~/.pi/agent/models.json` 的 local-minicpm5 配置迁移为示例/真实配置。
- 验收是否包含真实 MiniCPM5 focused 小矩阵。

## [2026-06-08 15:09:44] [Session ID: omx-1780470665249-tkxhle] 笔记: profile 应用层级

### 用户已确认
- `toolUseProfiles` 定义在 `models.json` 顶层。
- provider-level 可以配置默认 `toolUseProfile`。
- model-level 可以配置 `toolUseProfile` 并覆盖 provider 默认值。

### 解析规则候选
1. 读取 `ModelsConfig.toolUseProfiles`。
2. 读取 `ProviderConfig.toolUseProfile` 作为 provider 默认。
3. 读取 `ModelConfig.toolUseProfile` 作为 model override。
4. 最终每个模型解析出 0 或 1 个 profile, 进入 prompt/schema/repair/guard 执行路径。

### 设计约束
- 不应在 agent/provider/app 三处各自重复判断 provider/model 字符串。
- profile resolve 应作为单一真相源, 避免多条执行路径不一致。

## [2026-06-08 15:11:15] [Session ID: omx-1780470665249-tkxhle] 笔记: closure gate 已通过

### Non-goals
- 不做独立 profile 文件。
- 不做 UI 配置编辑器。
- 不做 profile 下载/同步机制。
- 不暴露无限细粒度 knobs。
- 不自动推断 weak profile, 必须显式配置。
- 不把 loose 漂移率降低作为本轮验收目标。

### Acceptance Criteria
- 现有 `local_minicpm5` 硬编码判断迁移为 profile 驱动。
- `models.json` 可表达顶层 `toolUseProfiles`。
- provider-level `toolUseProfile` 可作为默认值。
- model-level `toolUseProfile` 可覆盖 provider 默认值。
- 每个模型最终只有一个 resolved profile 作为单一真相源。
- MiniCPM5 focused 小矩阵保持通过。

## [2026-06-08 15:22:43] [Session ID: omx-1780470665249-tkxhle] 笔记: Ralplan 代码证据索引

### 已确认代码证据
- `src/app.rs:29-51`: MiniCPM5 专用 provider id、prompt marker 和 hard tool-use prompt。
- `src/app.rs:234-275`: `append_provider_local_system_prompt` 通过 `should_append_local_minicpm5_tool_prompt` 绑定 provider/model 字符串。
- `src/providers/openai.rs:35-44`: MiniCPM5 专用 path 描述常量。
- `src/providers/openai.rs:1186-1248`: `convert_tool_to_openai_for_provider` 只对 `LOCAL_MINICPM5_PROVIDER_ID` 改写 schema。
- `src/agent.rs:701-943`: `repair_local_minicpm5_*` 与 `rewrite_local_minicpm5_*` 是 runtime hardening 主体。
- `src/agent.rs:2934-3034`: finalize 和 execute tool calls 路径调用上述 hardening。
- `src/models.rs:92-123`: 现有模型配置结构只有 `providers`, provider/model 下没有 `toolUseProfile`。
- `src/models.rs:621-642`: `models.json` 使用 `serde_json::from_str::<ModelsConfig>` 进入加载。
- `src/models.rs:1680-1835`: `apply_custom_models` 是 provider/model 配置合并入口。
- `src/models.rs:3277-3335`: 已有 `models.json` 加载测试可扩展。


## [2026-06-10 18:15:56] [Session ID: omx-1781010764764-n4q7h4] 笔记: MiniCPM5 Pi generation 参数透传与真实 smoke

### 现象
- 用户反馈 MiniCPM5 在 Pi 下可能持续循环输出,难以自然结束。
- 修改前的 `OpenAIRequest` 没有 `stop` / `repetition_penalty` 字段。
- 修改前的 Pi 全局 `models.json` MiniCPM5 条目只有 `maxTokens=4096`,没有 generation 配置。

### 已验证结论
- 当前 `mlx_lm.server` 从 HTTP body 读取 `stop` 和 `repetition_penalty`,不支持把它们作为 launcher CLI 参数。
- Pi 原请求路径确实没有透传这两个字段。这是已确认的配置/请求缺口,但不能单独解释所有 weak/loose 指令漂移。
- 修复后 `models.json` 的 MiniCPM5 条目配置为:
  - `maxTokens=512`
  - `generation.stop=["<|im_end|>", "</s>"]`
  - `generation.repetitionPenalty=1.15`

### 动态证据
- 配置继承测试: passed。
- 真实 JSON 配置加载测试: passed。
- OpenAI request JSON 测试: passed,确认序列化 `stop` 和 `repetition_penalty`。
- 真实 Pi smoke:
  - 命令路径: 安装后的 `/Users/cuiluming/.cargo/bin/pi`。
  - provider/model: `local-minicpm5` + `MiniCPM5-1B`。
  - `--mode json --print --no-session --no-tools`。
  - 结果: exit 0, 12.50 秒,最终 `stopReason="stop"`。
  - 模型没有遵从“只输出 OK”,而是输出 RTK 命令列表。说明停止路径已正常结束,但指令遵循质量仍是独立问题。

### 并发配置变化
- 收尾时发现另一个任务向同一个 `models.json` 追加了 Nemotron 模型。
- 该改动不是本轮生成,已完整保留;本轮只确认 MiniCPM5 generation 配置仍存在。
