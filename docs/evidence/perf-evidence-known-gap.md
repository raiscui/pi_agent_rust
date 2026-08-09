# Perf Evidence Known Gap

> Authoritative statement that `tests/perf/reports/budget_summary.json` reports
> a stale evidence state. Read this BEFORE claiming any "perf test failure" or
> trying to close this gap from a single local machine.

- Schema: `pi.perf.evidence_known_gap.v1`
- Generated: 2026-08-09 (Session ID: 1)
- Source review: `tests/perf/reports/budget_summary.json` (`generated_at = 2026-08-02T00:00:22+00:00`, `ci_fail = 0`, `ci_no_data = 12`, `data_contract_failures_count = 15`)

## 1. What `budget_summary.json` says right now

- `ci_fail = 0` (no CI-enforced budget is in a hard-fail state)
- `ci_no_data = 12` (twelve CI-enforced budgets have no fresh measurement)
- `data_contract_failures_count = 15` (fifteen contracts fail their data-shape check)
- `run_id = null`
- All 19 budget `value` fields are `None`
- `generated_at` is **2026-08-02**, frozen from a historical real-perf run

`scripts/report_swarm_claim_readiness.py --gate` reports
`perf_budget_summary` as a blocker **only** because
`extension_benchmark_stratification` is intentionally fail-closed without a
finite full-e2e Rust-vs-Node/Bun ratio. There is **no active fail-closed
budget** in the 14 missing-artifact budgets below; they are listed as
`ci_no_data` so the report can be re-driven after a fresh perf run.

## 2. The 14 missing criterion / perf artifacts

These are the paths that `data_contract_failures_count = 15` flags as
`missing_or_stale_budget_artifact`. None of them currently exist on disk; the
first path in each list is the one the validator accepts.

| Budget | Expected artifact (first match) | Profile |
|---|---|---|
| `startup_version_p95` | `target/criterion/startup/version/warm/new/estimates.json` | hyperfine |
| `ext_cold_load_simple_p95` | `target/criterion/ext_load_init/load_init_cold/hello/new/estimates.json` | criterion |
| `tool_call_latency_p99` | `target/perf/pijs_workload_perf.jsonl` (also `release/` `debug/` `pijs_workload.jsonl` `results/pijs_workload.jsonl`) | pijs workload |
| `tool_call_throughput_min` | same five paths as above | pijs workload |
| `context_graph_build_cold_p95` | `target/criterion/semantic_context/graph_build_cold/large_workspace/new/estimates.json` | criterion |
| `context_graph_build_warm_p95` | `target/criterion/semantic_context/graph_build_warm/large_workspace/new/estimates.json` | criterion |
| `context_incremental_update_p95` | `target/criterion/semantic_context/incremental_update/large_workspace/new/estimates.json` | criterion |
| `context_planning_p95` | `target/criterion/semantic_context/planning/large_workspace/new/estimates.json` | criterion |
| `context_bundle_serialization_p95` | `target/criterion/semantic_context/bundle_serialization/large_workspace/new/estimates.json` | criterion |
| `context_bundle_estimated_bytes_max` | `target/perf/context_intelligence_planner_budget.json` (also `results/` `context_intelligence/perf_budget.json` `tests/perf/reports/`) | planner budget |
| `policy_eval_p99` | `target/criterion/ext_policy/evaluate` | criterion |
| `protocol_parse_p99` | `target/criterion/ext_protocol/parse_and_validate` | criterion |
| `binary_size_release` | (release binary size measurement) | release binary |
| `idle_memory_rss` | (idle RSS measurement) | runtime RSS |

## 3. The three stale (not missing) evidence files

These exist on disk but are flagged stale by the >24h freshness rule:

| Artifact | Age | Notes |
|---|---|---|
| `tests/perf/reports/extension_benchmark_stratification.json` | **~1598 hours old** (~66 days) | Last regenerated 2026-05-10 by DarkGoose for `bd-2zcs5.51` |
| `tests/perf/reports/phase1_matrix_validation.json` | **~1598 hours old** | Same regeneration date as above |
| `tests/perf/reports/context_intelligence_planner_budget.json` | (missing; same root cause as the 14 above) | |

The 1598h stratification and phase1 files are the artifacts that actually
fail `scripts/report_swarm_claim_readiness.py --gate` (because they are
checked-in and have a freshness contract), not the criterion artifacts
themselves. Those are detected only via the budget validator.

## 4. Why this is a "known gap" not a "regression"

- Every active bead in the 2zcs5 series (`bd-2zcs5.1` ... `bd-2zcs5.73`) is
  `closed`. `br ready --json` returns `[]`; `br list --status=open --json`
  returns `{"issues": [], "total": 0}`. There is no active tracker bead
  for this gap.
- `tests/bench_schema.rs` orchestrate tests (six in total) **pass under the
  fake toolchain stub** with `PERF_SKIP_CRITERION=1` and `--no-rch`. They
  are not failing in CI; they are contract tests, not real perf runs.
- `budget_summary.json` `ci_fail = 0` means no claim is currently being
  rejected by CI. The gap is visible to humans/agents but not blocking
  shipping.

## 5. Why we cannot close this gap from this local machine

- 2026-05-09 historical attempt by MagentaOak:
  - `cargo bench --bench extensions --profile perf ext_load_init` was
    **stopped after 31 minutes** with no estimates.
  - `./scripts/perf/orchestrate.sh --profile full --require-rch` was
    **stopped while `cargo test --no-run --profile perf` sat at
    `sqlmodel-core/sqlmodel-sqlite`** with no report artifacts.
  - The local dev toolchain cannot finish these workloads in bounded time.
- User-confirmed hard constraint (Session ID 1, 2026-08-09):
  > "之前测试/bench 太多并行 会用巨量的内存,会让机器卡死"
  Recorded in `task_plan.md` as:
  - `cargo test` / `cargo bench` must use `--jobs / -j <= 2`
  - Criterion must be single-thread (`--jobs 0` is forbidden)
  - Long tasks must pre-check `vm_stat` / `top` and record in WORKLOG
  - OOM must be killed, never retried
- This machine, at the time of writing, has:
  - `top` Load Avg: **30.03 / 16.83 / 9.59** (1m / 5m / 15m)
  - `vm_stat` free pages: ~3.7 GB free, but the dev profile codegen for
    `asupersync` (pedantic + nursery lints + sccache) took >4 minutes for
    a single `--no-run` test binary compile and was aborted.
- RCH (`~/.local/bin/rch`) is the documented offload path. Per
  `tests/bench_schema.rs:4789`, all orchestrate contract tests already
  pass `--no-rch` for deterministic local runs; the real perf path is
  intentionally RCH-only.

## 6. How to close this gap (for whoever has the time and a clean machine)

1. Run RCH on a worker with sufficient headroom:
   ```bash
   rch exec -- env PERF_CARGO_RUNNER=local \
     ./scripts/perf/orchestrate.sh --profile full --require-rch
   ```
   The script writes `target/perf/<run>/manifest.json` and the 14
   criterion/perf artifacts above.
2. Regenerate the stale checked-in evidence (the three in §3):
   ```bash
   PI_GENERATE_PHASE1_MATRIX=1 \
   PI_GENERATE_EXTENSION_STRATIFICATION=1 \
   PI_GENERATE_CONTEXT_INTELLIGENCE_BUDGET=1 \
     ./scripts/perf/orchestrate.sh --profile full --require-rch
   ```
   These are the `PI_GENERATE_*` opt-in switches added in commit
   `891390f9` so ordinary `cargo test` runs cannot rewrite tracked
   evidence mid-run.
3. After the run, rerun the budget validator:
   ```bash
   python3 scripts/report_swarm_claim_readiness.py --gate
   ```
   Expect `ci_fail = 0`, `ci_no_data = 0`, `data_contract_failures_count = 0`.

## 7. What local agents must NOT do

- Do NOT treat any "8 个遗留测试失败" or "orchestrate 5 (bench_schema)"
  plan item in a stale `task_plan.md` as an active failure that has to be
  fixed in this session. The bead tracker says there is no active work.
- Do NOT run `cargo bench --profile perf` or `cargo test --profile perf`
  on this machine. It will either timeout (MagentaOak: 31m no output) or
  push the machine into OOM (user-confirmed 2026-08-09).
- Do NOT regenerate `tests/perf/reports/budget_summary.json` from a
  half-completed local run. `data_contract_failures_count` will be
  non-zero and `extension_benchmark_stratification` will still be stale,
  producing a misleading "no improvement" report.
- Do NOT add the 14 missing artifacts as fake evidence. That would
  defeat the fail-closed contract that bead `bd-2zcs5.15` already
  enforced.

## 8. Pointer back into the repo

- This file is the human-readable companion to
  `tests/perf/reports/budget_summary.json`. The JSON is the validator
  output; this file is the "why it looks this way" explanation.
- `task_plan.md` references this file from the
  `[2026-08-09 14:25:00] 硬约束: 测试/bench 并行度上限` block.
- `EXPERIENCE.md` should be updated with a one-line pointer to this
  document once it is reviewed.
