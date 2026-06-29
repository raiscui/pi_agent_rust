# Models Configuration

Pi loads available models from a built-in registry and an optional user-defined `models.json`.

## Location

| Path | Description |
|------|-------------|
| `~/.pi/agent/models.json` | User-defined model overrides and custom providers |

## Schema

The root object contains a `providers` map and may contain a top-level
`toolUseProfiles` map.

```json
{
  "toolUseProfiles": {
    "weak-openai-compatible": { "...": "..." }
  },
  "providers": {
    "openai": { ... },
    "anthropic": { ... },
    "ollama": { ... }
  }
}
```

### Provider Config

| Field | Type | Description |
|-------|------|-------------|
| `baseUrl` | string | Base API URL (e.g. `https://api.openai.com/v1`) |
| `api` | string | Protocol adapter (e.g. `openai-completions`, `openai-responses`, `anthropic-messages`, `google-generative-ai`, `google-vertex`) |
| `apiKey` | string | API key, env var name, or shell command (see Secret Resolution) |
| `models` | object[] | List of models. If omitted, provider settings override built-in config for that provider. |
| `headers` | object | Custom HTTP headers |
| `authHeader` | boolean | If true, sends key in `Authorization: Bearer <key>` |
| `compat` | object | Compatibility flags |
| `toolUseProfile` | string | Optional default tool-use profile name for this provider |

If `models` is provided, built-in models for that provider are replaced with the list in `models.json`.

### Model Config

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Model ID sent to API |
| `name` | string | Display name |
| `contextWindow` | number | Context window size in tokens |
| `maxTokens` | number | Max output tokens |
| `reasoning` | boolean | True if model supports extended thinking |
| `input` | string[] | `["text", "image"]` |
| `cost` | object | Cost per million tokens |
| `toolUseProfile` | string | Optional tool-use profile override for this model |

### Tool-Use Profiles (`toolUseProfiles`)

`toolUseProfiles` is a top-level map of named, configuration-defined tool-use
hardening profiles. Providers and models reference a profile by name with
`toolUseProfile`.

Resolution order:

1. `model.toolUseProfile`, when present.
2. `provider.toolUseProfile`, when present.
3. No profile.

Unknown profile names fail closed as a configuration error. Pi does not
auto-detect weak models, does not fetch profiles from remote locations, and
does not read a separate `tool-use-profiles.json` file.

Supported first-pass fields:

| Field | Description |
|-------|-------------|
| `appendSystemPrompt` | Extra system prompt text appended only when tools are enabled |
| `pathSchema.fileTools` | Tools whose `path` is a required file path |
| `pathSchema.optionalPathTools` | Tools whose `path` is optional |
| `pathSchema.filePathDescription` | Description used for `path` in `fileTools` |
| `pathSchema.optionalPathDescription` | Description used for `path` in `optionalPathTools` |
| `pathSchema.genericPathDescription` | Fallback description for other tools with `path` |
| `argumentRepair.repairDegeneratePathFromUserText` | Repair degenerate/absolute path values from one explicit relative path in user text |
| `argumentRepair.repairGrepDegenerateGlob` | Repair `grep` when `glob` degenerates to the current directory or a non-wildcard dot-prefixed literal, and one explicit file is present |
| `postToolGuard.rewriteRepeatedSuccessfulToolCall` | Convert repeated same-name/same-argument successful tool calls into the prior tool result |
| `postToolGuard.stripReadLinePrefixes` | Strip `read` line metadata like `1→TEXT` when reusing a prior read result |
| `tools` | Optional allowlist of tool names exposed to the model in the OpenAI schema. `null`/missing keeps the historical no-filter behavior. `[]` disables every tool (profile 显式禁 tool). A non-empty list exposes only the named tools; names not present in the current tool registry are silently ignored. |

### Compatibility Flags (`compat`)

| Field | Description |
|-------|-------------|
| `supportsStore` | Enable OpenAI `store` parameter (where supported) |
| `supportsDeveloperRole` | Use `developer` role instead of `system` (OpenAI o1/o3) |
| `supportsReasoningEffort` | Send `reasoning_effort` param (OpenAI) |
| `supportsUsageInStreaming` | Expect usage fields in streaming responses |
| `maxTokensField` | Override param name (e.g., `max_completion_tokens`) |
| `openRouterRouting` | OpenRouter routing metadata (JSON object) |
| `vercelGatewayRouting` | Vercel gateway routing metadata (JSON object) |

## Examples

### 1. Override OpenAI Base URL (e.g. for Groq)

```json
{
  "providers": {
    "openai": {
      "baseUrl": "https://api.groq.com/openai/v1",
      "apiKey": "gsk_...",
      "models": [
        {
          "id": "llama3-70b-8192",
          "name": "Groq Llama 3 70B",
          "contextWindow": 8192
        }
      ]
    }
  }
}
```

### 2. Azure OpenAI

Azure requires resource-specific URLs and `api-key` header instead of Bearer token.

```json
{
  "providers": {
    "azure-openai": {
      "api": "openai-completions",
      "baseUrl": "https://my-resource.openai.azure.com/openai/deployments/my-deployment",
      "apiKey": "...",
      "authHeader": false,
      "headers": {
        "api-key": "..."
      },
      "models": [
        {
          "id": "gpt-4",
          "contextWindow": 128000
        }
      ]
    }
  }
}
```

### 3. Local LLM (Ollama)

```json
{
  "providers": {
    "ollama": {
      "api": "openai-completions",
      "baseUrl": "http://localhost:11434/v1",
      "apiKey": "ollama",
      "models": [
        {
          "id": "llama3",
          "contextWindow": 8192
        }
      ]
    }
  }
}
```

### 4. Local MiniCPM5 via OpenAI-compatible server

MiniCPM5-style weak OpenAI-compatible tool-use hardening is configured as data,
not as a Rust-side preset. You can rename the profile as long as the provider or
model references the same name.

```json
{
  "toolUseProfiles": {
    "weak-openai-compatible": {
      "appendSystemPrompt": "- If a task needs a tool, output the tool call first.\\n- Do not repeat a successful tool call.\\n- Tool results are the only source of file facts.",
      "pathSchema": {
        "fileTools": ["read", "edit", "write", "hashline_edit"],
        "optionalPathTools": ["grep", "find", "ls"],
        "filePathDescription": "Relative file path copied from the user's request. Never use absolute paths.",
        "optionalPathDescription": "Optional relative file or directory path. Omit it when the user gives no explicit path.",
        "genericPathDescription": "Relative file or directory path. Never use absolute paths."
      },
      "argumentRepair": {
        "repairDegeneratePathFromUserText": true,
        "repairGrepDegenerateGlob": true
      },
      "postToolGuard": {
        "rewriteRepeatedSuccessfulToolCall": true,
        "stripReadLinePrefixes": true
      }
    }
  },
  "providers": {
    "local-minicpm5": {
      "api": "openai-completions",
      "baseUrl": "http://127.0.0.1:18081/v1",
      "apiKey": "local",
      "authHeader": false,
      "toolUseProfile": "weak-openai-compatible",
      "compat": {
        "supportsTools": true,
        "supportsStreaming": true,
        "supportsUsageInStreaming": false,
        "supportsParallelToolCalls": false
      },
      "models": [
        {
          "id": "/Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/MiniCPM5-1B",
          "name": "MiniCPM5-1B",
          "contextWindow": 131072,
          "maxTokens": 4096,
          "reasoning": false,
          "input": ["text"]
        }
      ]
    }
  }
}
```

### 5. rdog-control-bash profile (bash-only local model)

Use this profile when a local OpenAI-compatible model is wired to the
`rdog-control` skill and you want to expose only the `bash` tool — the
single entry point that `rdog-control` needs to drive LAN hosts,
hardware bridges, and microcontrollers. The `tools` allowlist removes
every other tool from the OpenAI schema, so the model cannot drift into
`read` / `write` / `grep` calls and the prompt stays focused on
`rdog control TARGET` line-control commands.

```json
{
  "toolUseProfiles": {
    "rdog-control-bash": {
      "appendSystemPrompt": "- You have exactly one tool: bash.\n- Use bash to invoke `rdog control TARGET` for remote control of LAN hosts, hardware bridges, and microcontrollers.\n- One line-control command per bash call: @ping, @capabilities, @bootstrap, @observe, @cmd, @key, @paste, @ax-action, @web-find, @web-act, @savefile, ...\n- For a real terminal session use `rdog control TARGET --pty -- COMMAND`.\n- Do not repeat a successful bash call. Parse the @response/@savefile/@pty-* frame, then answer briefly in plain text.",
      "tools": ["bash"]
    }
  },
  "providers": {
    "local": {
      "baseUrl": "http://127.0.0.1:18081/v1",
      "api": "openai-completions",
      "apiKey": "local-no-key-needed",
      "authHeader": false,
      "compat": {
        "supportsTools": true,
        "supportsUsageInStreaming": false
      },
      "models": [
        {
          "id": "/Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/gemma-4-e2b-it-qat-OptiQ-4bit",
          "name": "Local Gemma 4 E2B IT OptiQ 4bit",
          "contextWindow": 128000,
          "maxTokens": 4096,
          "input": ["text"],
          "reasoning": false,
          "toolUseProfile": "rdog-control-bash"
        }
      ]
    }
  }
}
```

Notes:

- The `tools` allowlist is enforced in two places from the same
  profile source: Pi first filters the ToolRegistry before tool
  execution, then `OpenAIProvider::build_request` filters the OpenAI
  request `tools` array. This keeps the model-visible schema and the
  client-executable tool set aligned.
- `tools: []` is a valid (and explicit) way to disable every tool via
  the profile. It is intentionally distinct from
  `compat.supportsTools: false`, which signals the upstream model
  itself does not support tool calling.

## Secret Resolution

API keys can be plain strings, environment variables, or shell commands.

- **Environment Variable**: If the string matches an env var name (e.g. `OPENAI_API_KEY`), it is resolved.
- **Shell Command**: Prefix with `!` to execute a command.

```json
{
  "providers": {
    "openai": {
      "apiKey": "!pass show api/openai"
    }
  }
}
```

Shell commands run via `sh -c` on Unix and `cmd /C` on Windows.

### Local providers (no API key)

`ollama`, `llamacpp` (llama.cpp's `llama-server`), `mistralrs` (mistral.rs), and
`lmstudio` are recognized built-in **local** providers. `ollama`, `llamacpp`, and
`mistralrs` require **no API key** — they expose an OpenAI-compatible server on
localhost and are called without an `Authorization` header. They work
out-of-the-box without a `models.json` entry:

```bash
# Defaults: llama-server -> http://127.0.0.1:8080/v1, mistral.rs -> http://127.0.0.1:1234/v1
pi --provider llamacpp  --model ggml-org/gemma-4-E4B-it-GGUF -p "hi"
pi --provider mistralrs --model default -p "hi"
```

Provider aliases are accepted: `llama.cpp` / `llama-cpp` / `llama-server` ->
`llamacpp`, and `mistral.rs` / `mistral-rs` -> `mistralrs`.

To point at a non-default host/port, add a `models.json` entry (no `apiKey`
needed):

```json
{
  "providers": {
    "llamacpp": {
      "baseUrl": "http://127.0.0.1:9090/v1",
      "models": [ { "id": "my-model" } ]
    }
  }
}
```

## User Model Override (extending the bundled snapshot)

Pi ships with a snapshot of every provider's discovery endpoint at
`docs/provider-upstream-model-ids-snapshot.json`. The snapshot is regenerated
ahead of releases, but a new model from a provider (e.g. Anthropic shipping a
new Opus version) is invisible to `/model` until the next release.

Drop a JSON file at `<config_dir>/pi/models-override.json` to extend the
snapshot at runtime. The file uses the same shape as the bundled snapshot:

```json
{
  "anthropic": ["claude-opus-4-7"],
  "openrouter": ["anthropic/claude-opus-4-7"]
}
```

`<config_dir>` is whatever `dirs::config_dir()` reports — `~/.config` on Linux,
`~/Library/Application Support` on macOS, `%APPDATA%` on Windows. Set
`PI_MODELS_OVERRIDE=/path/to/file.json` in the environment to point pi at a
file outside the standard config directory.

Behavior:

- **Additive only.** Override entries union with the bundled snapshot. There
  is no way to *remove* a bundled model via the override file; the provider's
  next refresh will reintroduce anything you delete.
- **Survives upgrades.** The override file is in your user config directory,
  not in pi's binary, so model entries you add stay across releases until the
  bundled snapshot catches up — then they dedupe automatically.
- **Fail-safe.** A missing or malformed override file logs a debug/warning
  line and is treated as empty so a typo never breaks pi startup.
- **Provider IDs must match canonical names.** Use `anthropic`, `openai`,
  `openrouter`, etc. (the keys you see in
  `docs/provider-upstream-model-ids-snapshot.json`).

The override only affects the `/model` autocomplete catalog. To actually call
a model that pi does not yet have a built-in route for, also configure the
provider in `models.json` (sections above) — pi already routes any
`anthropic/<id>` value through the Anthropic API regardless of whether the ID
is in the snapshot.

## See Also

- `appendSystemPrompt` 在 system prompt 装配链中的位置: [`docs/system-prompt-injection.md`](system-prompt-injection.md) §3、§7、§10。
