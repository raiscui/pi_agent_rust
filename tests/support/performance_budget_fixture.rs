//! 供多个 integration test 复用的 canonical performance budget 定义。

/// 返回 release gate 认可的 19 项预算 inventory。
pub fn canonical_budgets() -> Vec<serde_json::Value> {
    [
        ("startup_version_p95", "startup", "p95 latency", "ms", 100.0, "maximum", true, "hyperfine: `rpi --version` (10 runs, 3 warmup)"),
        ("startup_full_agent_p95", "startup", "p95 latency", "ms", 200.0, "maximum", false, "hyperfine: `rpi --print '.'` with full init (10 runs, 3 warmup)"),
        ("ext_cold_load_simple_p95", "extension", "p95 cold load time", "ms", 5.0, "maximum", true, "criterion: load_init_cold for simple single-file extensions (10 samples)"),
        ("ext_cold_load_complex_p95", "extension", "p95 cold load time", "ms", 50.0, "maximum", false, "criterion: load_init_cold for multi-registration extensions (10 samples)"),
        ("ext_load_60_total", "extension", "total load time (60 official extensions)", "ms", 10_000.0, "maximum", false, "conformance runner: sequential load of all 60 official extensions"),
        ("tool_call_latency_mean", "tool_call", "mean per-call latency", "us", 200.0, "maximum", true, "pijs_workload: arithmetic mean across exactly 2000 iterations x 1 tool call, executable-path-verified perf profile"),
        ("tool_call_throughput_min", "tool_call", "minimum calls/sec", "calls/sec", 5_000.0, "minimum", true, "pijs_workload: aggregate throughput across exactly 2000 iterations x 10 tool calls, executable-path-verified perf profile"),
        ("event_dispatch_p99", "event_dispatch", "p99 dispatch latency", "us", 5_000.0, "maximum", false, "criterion: event_hook dispatch for before_agent_start (100 samples)"),
        ("context_graph_build_cold_p95", "context_intelligence", "p95 cold graph build latency", "ms", 500.0, "maximum", true, "criterion: semantic_context/graph_build_cold on large filesystem fixture"),
        ("context_graph_build_warm_p95", "context_intelligence", "p95 warm graph build latency", "ms", 250.0, "maximum", true, "criterion: semantic_context/graph_build_warm on large filesystem fixture"),
        ("context_incremental_update_p95", "context_intelligence", "p95 single-change rebuild latency", "ms", 250.0, "maximum", true, "criterion: semantic_context/incremental_update rebuild after one changed file"),
        ("context_planning_p95", "context_intelligence", "p95 planner latency", "ms", 50.0, "maximum", true, "criterion: semantic_context/planning on large graph fixture"),
        ("context_bundle_serialization_p95", "context_intelligence", "p95 bundle serialization latency", "ms", 25.0, "maximum", true, "criterion: semantic_context/bundle_serialization on large bundle fixture"),
        ("context_bundle_estimated_bytes_max", "context_intelligence", "bundle estimated size", "bytes", 262_144.0, "maximum", true, "semantic_context budget artifact: estimated selected bundle bytes"),
        ("policy_eval_p99", "policy", "p99 evaluation time", "ns", 500.0, "maximum", true, "criterion: ext_policy/evaluate with various modes and capabilities"),
        ("idle_memory_rss", "memory", "RSS at idle", "MB", 50.0, "maximum", true, "sysinfo: measure RSS after startup, before any user input"),
        ("sustained_load_rss_growth", "memory", "RSS growth under 30s sustained load", "percent", 5.0, "maximum", false, "stress test: 15 extensions, 50 events/sec for 30 seconds"),
        ("binary_size_release", "binary", "release binary size", "MB", 22.0, "maximum", true, "ls -la target/release/rpi (stripped)"),
        ("protocol_parse_p99", "protocol", "p99 parse+validate time", "us", 50.0, "maximum", true, "criterion: ext_protocol/parse_and_validate for host_call and log messages"),
    ]
    .into_iter()
    .map(
        |(name, category, metric, unit, threshold, comparison, ci_enforced, methodology)| {
            serde_json::json!({
                "name": name,
                "category": category,
                "metric": metric,
                "unit": unit,
                "threshold": threshold,
                "comparison": comparison,
                "ci_enforced": ci_enforced,
                "methodology": methodology,
            })
        },
    )
    .collect()
}
