#!/usr/bin/env python3
"""
rdog-rpc-bench.py: 用 pi --mode rpc (JSON-RPC over stdio) 跑 rdog-control benchmark.

为什么用 RPC 而不是 -p:
  pi -p (print mode) 在弱本地 model + 本机 MLX server 组合下不稳定,
  60s timeout 内可能拿不到完整数据 (见 docs/discuss/phase0-baseline-20260618.md 第 5.2 节).
  --mode rpc 是 JSON-RPC 2.0 over stdio, 给 agent 完整可编程的 event stream,
  能在 model 真卡死时主动中断, 拿完整 turn 数 + tool call 列表.

用法:
  python3 docs/discuss/rdog-rpc-bench.py \
      --pi-bin /Users/cuiluming/.cargo/bin/pi \
      --cwd /Users/cuiluming/local_doc/l_dev/my/rust/pi_agent_rust \
      --provider local \
      --model /Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/Qwen3.5-2B-OptiQ-4bit \
      --prompt "在左侧的chrome浏览器窗口新建标签,打开 www.xiaohongshu.com ,并点击左侧列表中的'首页'刷新内容" \
      --timeout 120 \
      --out /tmp/pi_bench_qwen_rpc.json

输出 JSON 报告:
  {
    "model": "...",
    "prompt": "...",
    "wall_time_sec": 87.3,
    "turn_count": 5,
    "tool_calls": [
      {"tool": "read", "path": "~/.pi/agent/skills/rdog-control.md", "turn": 1},
      {"tool": "bash", "command": "printf '@ping\\n' | rdog control mac.lab", "turn": 2}
    ],
    "text_responses": ["..."],
    "errors": [],
    "exit_reason": "completed" | "timeout" | "broken_pipe" | "error"
  }
"""
import argparse
import json
import os
import re
import select
import subprocess
import sys
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="pi --mode rpc benchmark for rdog-control skill"
    )
    p.add_argument(
        "--pi-bin",
        default=os.environ.get("PI_BIN", "/Users/cuiluming/.cargo/bin/pi"),
        help="path to pi binary (default: $PI_BIN or /Users/cuiluming/.cargo/bin/pi)",
    )
    p.add_argument(
        "--cwd",
        default=os.environ.get("PI_CWD", "/Users/cuiluming/local_doc/l_dev/my/rust/pi_agent_rust"),
        help="cwd for pi subprocess (default: $PI_CWD or pi_agent_rust path)",
    )
    p.add_argument(
        "--provider",
        default=os.environ.get("PI_PROVIDER", "local"),
        help="provider id (default: $PI_PROVIDER or 'local')",
    )
    p.add_argument(
        "--model",
        required=True,
        help="model id (path or model name) passed via --model",
    )
    p.add_argument(
        "--prompt",
        required=True,
        help="user prompt text",
    )
    p.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="wall-time timeout in seconds (default: 120)",
    )
    p.add_argument(
        "--out",
        default=None,
        help="optional path to write JSON report",
    )
    p.add_argument(
        "--debug",
        action="store_true",
        help="also print every event line to stderr",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    pi_bin = Path(args.pi_bin)
    if not pi_bin.exists():
        print(f"pi binary not found: {pi_bin}", file=sys.stderr)
        return 2

    cmd = [
        str(pi_bin),
        "--mode",
        "rpc",
        "--provider",
        args.provider,
        "--model",
        args.model,
    ]
    if args.debug:
        print(f"spawning: {' '.join(cmd)} (cwd={args.cwd})", file=sys.stderr)

    started = time.time()
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=args.cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
    except OSError as err:
        print(f"failed to spawn pi: {err}", file=sys.stderr)
        return 2

    # 我们通过 stdin 发 prompt 请求, 通过 stdout 读 events
    # RPC 协议: {"type":"prompt","id":"bench-1","message":"<prompt>"}
    # 期望: stdout 是 newline-delimited JSON
    prompt_req = {
        "type": "prompt",
        "id": "bench-1",
        "message": args.prompt,
    }
    try:
        proc.stdin.write((json.dumps(prompt_req) + "\n").encode("utf-8"))
        proc.stdin.flush()
    except BrokenPipeError:
        proc.wait()
        report = {
            "model": args.model,
            "prompt": args.prompt,
            "wall_time_sec": round(time.time() - started, 2),
            "turn_count": 0,
            "tool_calls": [],
            "text_responses": [],
            "errors": ["broken_pipe_on_prompt_send"],
            "exit_reason": "broken_pipe",
        }
        if args.out:
            Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=False))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1

    events: list[dict] = []
    tool_calls: list[dict] = []
    text_responses: list[str] = []
    turn_count = 0
    errors: list[str] = []
    exit_reason = "completed"

    def drain() -> None:
        """非阻塞读 stdout, 直到没数据."""
        nonlocal turn_count, tool_calls, text_responses, errors
        while True:
            r, _, _ = select.select([proc.stdout], [], [], 0.05)
            if not r:
                break
            line = proc.stdout.readline()
            if not line:
                break
            try:
                evt = json.loads(line.decode("utf-8", errors="replace").rstrip("\n"))
            except json.JSONDecodeError as err:
                errors.append(f"json_decode_error: {err}; line={line[:200]!r}")
                continue
            events.append(evt)
            if args.debug:
                print(f"event: {evt}", file=sys.stderr)
            evt_type = evt.get("type", "")
            if evt_type in ("turn_start", "turn_end", "turn"):
                turn_count += 1
            elif evt_type == "tool_call":
                tool_name = evt.get("name", "")
                tool_args = evt.get("arguments", {}) or {}
                tool_calls.append(
                    {
                        "tool": tool_name,
                        "path": tool_args.get("path", ""),
                        "command": tool_args.get("command", ""),
                        "turn": turn_count,
                    }
                )
            elif evt_type in ("text", "assistant", "content_block_delta", "message"):
                content = (
                    evt.get("content")
                    or evt.get("text")
                    or evt.get("delta")
                    or ""
                )
                if isinstance(content, str) and content:
                    text_responses.append(content)

    # 主循环: 等 model 跑完, 用 wall-time 兜底
    deadline = started + args.timeout
    while True:
        now = time.time()
        if now >= deadline:
            exit_reason = "timeout"
            break
        drain()
        if proc.poll() is not None:
            # 子进程已结束, 再 drain 一次拿尾巴
            drain()
            break
        time.sleep(0.1)

    if proc.poll() is None:
        # 主动杀
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        except OSError:
            pass
        drain()

    stderr_tail = b""
    try:
        stderr_tail = proc.stderr.read() or b""
    except OSError:
        pass

    wall_time = round(time.time() - started, 2)
    # 统计 read SKILL.md 次数
    skill_reads = sum(
        1
        for tc in tool_calls
        if tc["tool"] == "read" and ("rdog-control" in tc["path"] or "rdog-control" in tc.get("path", ""))
    )
    rdog_bash_calls = sum(
        1
        for tc in tool_calls
        if tc["tool"] == "bash" and "rdog" in tc["command"]
    )

    report = {
        "model": args.model,
        "prompt": args.prompt,
        "wall_time_sec": wall_time,
        "turn_count": turn_count,
        "tool_calls": tool_calls,
        "text_responses": text_responses,
        "skill_reads": skill_reads,
        "rdog_bash_calls": rdog_bash_calls,
        "errors": errors,
        "exit_reason": exit_reason,
        "stderr_tail": stderr_tail.decode("utf-8", errors="replace")[-2000:],
    }
    serialized = json.dumps(report, indent=2, ensure_ascii=False)
    print(serialized)
    if args.out:
        Path(args.out).write_text(serialized)
    return 0


if __name__ == "__main__":
    sys.exit(main())
