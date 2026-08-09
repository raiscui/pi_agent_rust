## [2026-06-30 16:18:00] [Session ID: omx-1782803182165-j1czn4] 错误修复: G005 quality gate sourceArtifacts 漏列 benchmark 脚本

### 现象
- G005 final checkpoint 失败, ultragoal 校验提示 architecture invariant source 必须引用 sourceArtifacts 中的条目。

### 原因
- quality gate 第三条 invariant 证明 benchmark tooling boundary, source 引用了 docs/discuss/rdog-rpc-bench.py。
- sourceArtifacts 只列了 ultragoal artifacts 和 phase0.5 report, 没有列 benchmark 脚本。

### 修复
- 把 docs/discuss/rdog-rpc-bench.py 加入 .omx/ultragoal/quality-gate-g005-final-reconciliation-20260630.json 的 architectureInvariantGate.sourceArtifacts。

### 验证
- 重新运行 G005 checkpoint。

## [2026-06-30 16:24:00] [Session ID: omx-1782803182165-j1czn4] 补充验证: G005 checkpoint 修复后成功

### 修复补充
- 第一次修复只补 sourceArtifacts 仍不够, 因为 ultragoal 源码会把 invariant.source 按 # 截断后与 sourceArtifacts 做完全相等比较。
- 第三条 invariant.source 原本写成 docs/discuss/rdog-rpc-bench.py and docs/discuss/phase0.5-gui-baseline-20260630.md#本轮边界, 被判定为装饰性来源。
- 将该 source 改为单一 docs/discuss/rdog-rpc-bench.py, 把报告边界证据移到 implementationEvidence。

### 验证
- omx ultragoal checkpoint --goal-id G005-final-ultragoal-reconciliation-after --status complete --quality-gate-json ... 返回 ok=true。
- ledger 追加 goal_completed G005, qualityGate 内含 aiSlopCleaner/verification/codeReview/architectureInvariantGate。

