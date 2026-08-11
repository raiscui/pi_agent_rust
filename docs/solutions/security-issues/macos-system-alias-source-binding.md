---
title: "macOS system aliases in semantic graph source binding"
date: 2026-08-12
last_updated: 2026-08-12
module: src/semantic_workspace_graph.rs
component: performance-source-binding
problem_type: security_issue
severity: high
status: active
tags:
  - macos
  - source-binding
  - symlink-validation
verified_by:
  - cargo test -j 2 --test semantic_workspace_graph_builder -- canonical_dropin_verdict_rejects_symlinked_repository_path_components --exact
  - cargo test -j 2 --test semantic_workspace_graph_builder -- performance_budget_freshness_accepts_clean_head_bound_artifact --exact
root_cause: "macOS 的 /var 和 /tmp 是系统 symlink,通用的逐段拒绝 symlink 规则把可信仓库路径错误判为不可绑定。"
resolution_type: "只对白名单中的 root 持有固定系统 alias 放行,其余 symlink 继续拒绝。"
---

# macOS 系统目录别名的 source binding

## Problem

语义工作区图在 macOS 上验证 performance source binding 时,仓库临时目录可能经过 `/var` 到 `/private/var` 的系统别名。通用 symlink 拒绝规则会使合法证据降级为不可认证。

## Symptoms

- `performance_budget_freshness_accepts_clean_head_bound_artifact` 不能得到 `Current`。
- 不能以放宽全部 symlink 检查的方式修复,否则用户控制的仓库路径会绕过 source binding。

## What Didn't Work

把 symlink 视为普通目录会同时信任用户创建的符号链接,破坏 repository root、`.git` 和证据文件的 fail-closed 边界。

## Verified Root Cause

`canonical_real_directory` 对路径逐段使用 `symlink_metadata`。macOS 的 `/var` 和 `/tmp` 本身是稳定的系统符号链接,因此在 canonicalization 前被通用拒绝。动态测试显示 source binding 的正常路径恢复后为 `Current`,同时用户构造的 symlink 仍被拒绝。

## Solution

`is_macos_system_directory_alias` 只接受 `/var -> /private/var` 和 `/tmp -> /private/tmp`。每个候选 alias 必须是 root 持有的 symlink,且 `canonicalize` 结果必须精确等于预期目标。其他任何 symlink 都返回 `None`。

## Why This Works

该规则恢复 macOS 固定系统入口的可达性,但没有引入可配置路径或用户可控目标。source binding 的默认行为仍是拒绝 symlink。

## Verification

- `cargo test -j 2 --test semantic_workspace_graph_builder -- canonical_dropin_verdict_rejects_symlinked_repository_path_components --exact`
- `cargo test -j 2 --test semantic_workspace_graph_builder -- performance_budget_freshness_accepts_clean_head_bound_artifact --exact`

两条测试在 2026-08-12 均通过。

## Prevention

新增系统路径例外时,必须同时证明固定目标、受信任 owner 和用户创建 symlink 的拒绝回归。不得把通用 symlink 规则改为 allow。

## Related

- `src/semantic_workspace_graph.rs`
- `tests/semantic_workspace_graph_builder.rs`
