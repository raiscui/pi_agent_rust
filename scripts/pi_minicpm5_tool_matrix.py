#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import selectors
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

DEFAULT_PI_BIN = Path('/Users/cuiluming/local_doc/l_dev/my/rust/pi_agent_rust/target/debug/rpi')
DEFAULT_MODEL = Path('/Users/cuiluming/local_doc/l_dev/my/rust/fast-infer/models/MiniCPM5-1B')
DEFAULT_SERVER_URL = 'http://127.0.0.1:18081/v1'
PARSE_ERROR_TOOL_NAME = '__minicpm5_tool_parse_error'
WEAK_OPENAI_COMPATIBLE_PROMPT = """\
- If a task needs a tool, output the tool call first. No prose before the tool call.
- Do not say the task is done until after the tool result is returned.
- Use the requested tool name and arguments. Do not invent files or directories.
- File-system facts must come from tools: use read to read files, grep to search file contents, find to find file names, ls to list directories, and edit or write to change files.
- Do not answer file contents, search results, directory listings, or edit success from the user request, file name, or guesses before the tool result.
- Copy literal arguments exactly from the user request: path, pattern, oldText, newText, and content.
- File tools are read, edit, write, and hashline_edit; their path must be the requested relative file name.
- If the user says current directory and also names file.txt, set file-tool path to file.txt.
- Search/list tools are grep, find, and ls; omit optional path when the user gives no explicit path.
- Do not use current-directory markers as a file path.
- Never include quote characters inside path.
- Absolute paths are invalid for every tool.
- After a successful tool call, do not repeat the same tool call with the same arguments.
- After any tool result, answer only from the returned tool result. Do not invent rows, files, directories, or content.
- For read results, do not expand one returned line into a JSON array, numbered list, or extra line records.
- read may return lines like 1→TEXT; 1→ is tool metadata, and TEXT is the file content. Do not continue it as 2→....
- If read returns exactly one line, copy only the returned TEXT once, or say it was read.
- Do not fabricate line numbers, timestamps, counters, or shortened tokens such as P1, P2, or P100.
- If a tool returns an error, report that error once. Do not guess a new absolute path."""
FILE_PATH_DESCRIPTION = (
    "Relative file path copied from the user's request. If the user gives a filename, use that "
    "filename exactly. Never use current-directory markers as a file path. Do not use absolute "
    "paths. Do not include quote characters inside the path value."
)
OPTIONAL_PATH_DESCRIPTION = (
    "Optional relative file or directory path copied from the user's request. If the user gives no "
    "explicit path and the tool can use the current directory by default, omit this argument. Do "
    "not use absolute paths. Do not include quote characters inside the path value."
)
GENERIC_PATH_DESCRIPTION = (
    "Relative file or directory path copied from the user's request. Do not use absolute paths. "
    "Do not include quote characters inside the path value."
)

@dataclass(frozen=True)
class Scenario:
    name: str
    tool: str
    prompt_builder: Callable[[int], str]
    setup: Callable[[Path, int], dict[str, str]]
    expected_result: Callable[[Path, int], str]
    final_check: Callable[[Path, int], bool]

@dataclass
class TrialResult:
    scenario: str
    index: int
    classification: str
    workdir: str
    stdout_path: str
    stderr_path: str
    event_counts: dict[str, int]
    tool_events: list[dict[str, Any]]
    assistant_text: str
    assistant_text_chars: int
    agent_end_seen: bool
    exit_code: int | None
    expected: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Run Pi local MiniCPM5 read/grep/find/ls/edit matrix.')
    parser.add_argument('--trials', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--pi-bin', default=str(DEFAULT_PI_BIN))
    parser.add_argument('--provider', default='local-minicpm5')
    parser.add_argument('--model', default=str(DEFAULT_MODEL))
    parser.add_argument('--server-url', default=DEFAULT_SERVER_URL)
    parser.add_argument('--output-root', default='')
    return parser.parse_args()


def check_server(server_url: str) -> None:
    models_url = server_url.rstrip('/') + '/models'
    with urllib.request.urlopen(models_url, timeout=10) as response:
        body = response.read(4096).decode('utf-8', errors='replace')
    if 'MiniCPM5' not in body:
        raise SystemExit(f'Unexpected /models response from {models_url}: {body[:500]}')


def write_profiled_models_json(args: argparse.Namespace, output_root: Path) -> Path:
    config_dir = output_root / 'pi-agent-config'
    config_dir.mkdir(parents=True, exist_ok=True)
    models_json = {
        'toolUseProfiles': {
            'weak-openai-compatible': {
                'appendSystemPrompt': WEAK_OPENAI_COMPATIBLE_PROMPT,
                'pathSchema': {
                    'fileTools': ['read', 'edit', 'write', 'hashline_edit'],
                    'optionalPathTools': ['grep', 'find', 'ls'],
                    'filePathDescription': FILE_PATH_DESCRIPTION,
                    'optionalPathDescription': OPTIONAL_PATH_DESCRIPTION,
                    'genericPathDescription': GENERIC_PATH_DESCRIPTION,
                },
                'argumentRepair': {
                    'repairDegeneratePathFromUserText': True,
                    'repairGrepDegenerateGlob': True,
                },
                'postToolGuard': {
                    'rewriteRepeatedSuccessfulToolCall': True,
                    'stripReadLinePrefixes': True,
                },
            }
        },
        'providers': {
            args.provider: {
                'api': 'openai-completions',
                'baseUrl': args.server_url.rstrip('/'),
                'apiKey': 'local-minicpm5-test-key',
                'authHeader': False,
                'toolUseProfile': 'weak-openai-compatible',
                'compat': {
                    'supportsTools': True,
                    'supportsStreaming': True,
                    'supportsUsageInStreaming': False,
                    'supportsParallelToolCalls': False,
                },
                'models': [
                    {
                        'id': args.model,
                        'name': 'MiniCPM5-1B focused matrix',
                        'contextWindow': 131072,
                        'maxTokens': 4096,
                        'reasoning': False,
                        'input': ['text'],
                    }
                ],
            }
        },
    }
    (config_dir / 'models.json').write_text(
        json.dumps(models_json, ensure_ascii=False, indent=2)
    )
    return config_dir


def setup_read(workdir: Path, index: int) -> dict[str, str]:
    expected = f'PI_MINICPM5_MATRIX_READ_OK_{index:02d}'
    name = f'matrix_read_{index:02d}.txt'
    (workdir / name).write_text(expected)
    return {'file': name, 'expected': expected}


def setup_grep(workdir: Path, index: int) -> dict[str, str]:
    expected = f'PI_MINICPM5_MATRIX_GREP_OK_{index:02d}'
    name = f'matrix_grep_{index:02d}.txt'
    (workdir / name).write_text(f'alpha\n{expected}\nomega\n')
    return {'file': name, 'expected': expected}


def setup_find(workdir: Path, index: int) -> dict[str, str]:
    name = f'matrix_find_{index:02d}_target.txt'
    (workdir / name).write_text(f'PI_MINICPM5_MATRIX_FIND_OK_{index:02d}')
    (workdir / f'matrix_find_{index:02d}_other.md').write_text('other')
    return {'file': name, 'expected': name}


def setup_ls(workdir: Path, index: int) -> dict[str, str]:
    name = f'matrix_ls_{index:02d}_marker.txt'
    (workdir / name).write_text(f'PI_MINICPM5_MATRIX_LS_OK_{index:02d}')
    return {'file': name, 'expected': name}


def setup_edit(workdir: Path, index: int) -> dict[str, str]:
    old = f'OLD_TOKEN_{index:02d}'
    new = f'PI_MINICPM5_MATRIX_EDIT_OK_{index:02d}'
    name = f'matrix_edit_{index:02d}.txt'
    (workdir / name).write_text(f'prefix {old} suffix\n')
    return {'file': name, 'old': old, 'expected': new}


def read_prompt(index: int) -> str:
    name = f'matrix_read_{index:02d}.txt'
    return f'你必须调用 read 工具读取当前目录里的文件 {name}。不要只用文字回答, 必须先发真实 read tool call。工具返回后只回答读到的原文, 不要扩写成 JSON, 不要补造行列表。'


def grep_prompt(index: int) -> str:
    name = f'matrix_grep_{index:02d}.txt'
    needle = f'PI_MINICPM5_MATRIX_GREP_OK_{index:02d}'
    return f'你必须调用 grep 工具在当前目录的 {name} 里搜索 {needle}。不要只用文字回答, 必须先发真实 grep tool call。工具返回后只根据 grep 返回结果简短回答。'


def find_prompt(index: int) -> str:
    name = f'matrix_find_{index:02d}_target.txt'
    return f'你必须调用 find 工具在当前目录查找文件 {name}。不要只用文字回答, 必须先发真实 find tool call。工具返回后只根据 find 返回结果回答找到的文件名。'


def ls_prompt(index: int) -> str:
    name = f'matrix_ls_{index:02d}_marker.txt'
    return f'你必须调用 ls 工具列出当前目录, 确认是否包含 {name}。不要只用文字回答, 必须先发真实 ls tool call。工具返回后只根据 ls 返回结果简短回答。'


def edit_prompt(index: int) -> str:
    name = f'matrix_edit_{index:02d}.txt'
    old = f'OLD_TOKEN_{index:02d}'
    new = f'PI_MINICPM5_MATRIX_EDIT_OK_{index:02d}'
    return f'你必须调用 edit 工具把当前目录文件 {name} 中的 {old} 替换为 {new}。不要只用文字回答, 必须先发真实 edit tool call。edit 的 newText 必须完全等于 {new}。成功后只根据 edit 返回结果简短回答。'


def expected_from_setup(workdir: Path, index: int) -> str:
    meta_path = workdir / 'scenario-meta.json'
    return json.loads(meta_path.read_text())['expected']


def final_read(_: Path, __: int) -> bool:
    return True


def final_edit(workdir: Path, index: int) -> bool:
    name = f'matrix_edit_{index:02d}.txt'
    new = f'PI_MINICPM5_MATRIX_EDIT_OK_{index:02d}'
    old = f'OLD_TOKEN_{index:02d}'
    path = workdir / name
    return path.exists() and new in path.read_text() and old not in path.read_text()


SCENARIOS = [
    Scenario('read', 'read', read_prompt, setup_read, expected_from_setup, final_read),
    Scenario('grep', 'grep', grep_prompt, setup_grep, expected_from_setup, final_read),
    Scenario('find', 'find', find_prompt, setup_find, expected_from_setup, final_read),
    Scenario('ls', 'ls', ls_prompt, setup_ls, expected_from_setup, final_read),
    Scenario('edit', 'edit', edit_prompt, setup_edit, expected_from_setup, final_edit),
]


def run_trial(args: argparse.Namespace, scenario: Scenario, index: int, output_root: Path) -> TrialResult:
    workdir = output_root / scenario.name / f'trial-{index:02d}'
    workdir.mkdir(parents=True, exist_ok=True)
    meta = scenario.setup(workdir, index)
    (workdir / 'scenario-meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    expected = scenario.expected_result(workdir, index)

    stdout_path = workdir / 'pi-rpc-stdout.jsonl'
    stderr_path = workdir / 'pi-rpc-stderr.txt'

    cmd = [
        args.pi_bin,
        '--mode', 'rpc',
        '--provider', args.provider,
        '--model', args.model,
        '--thinking', 'off',
        '--tools', scenario.tool,
        '--no-extensions',
        '--no-skills',
        '--no-prompt-templates',
        '--hide-cwd-in-prompt',
        '--request-timeout', '600',
        '--max-tool-iterations', '4',
    ]
    request = {
        'type': 'prompt',
        'id': f'minicpm5-matrix-{scenario.name}-{index:02d}',
        'message': scenario.prompt_builder(index),
    }
    env = os.environ.copy()
    env.setdefault('RUST_LOG', 'warn')
    env['PI_CODING_AGENT_DIR'] = str(Path(args.pi_config_dir))

    process = subprocess.Popen(
        cmd,
        cwd=workdir,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        env=env,
    )
    stdout_lines = collect_rpc_output(process, request, args.timeout)
    stderr = read_and_stop_process(process)
    stdout_path.write_text(''.join(stdout_lines))
    stderr_path.write_text(stderr)

    events = parse_events(stdout_lines)
    tool_events = [event for event in events if event.get('type') in {'tool_execution_start', 'tool_execution_update', 'tool_execution_end'}]
    assistant_text = collect_assistant_text(events)
    classification = classify_result(scenario, tool_events, events, assistant_text, expected, workdir, index)

    return TrialResult(
        scenario=scenario.name,
        index=index,
        classification=classification,
        workdir=str(workdir),
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        event_counts=count_events(events),
        tool_events=tool_events,
        assistant_text=assistant_text,
        assistant_text_chars=len(assistant_text),
        agent_end_seen=any(event.get('type') == 'agent_end' for event in events),
        exit_code=process.returncode,
        expected=expected,
    )


def collect_rpc_output(process: subprocess.Popen[str], request: dict[str, Any], timeout: int) -> list[str]:
    if process.stdin is None or process.stdout is None:
        raise RuntimeError('Pi process pipes were not created')
    process.stdin.write(json.dumps(request, ensure_ascii=False) + '\n')
    process.stdin.flush()

    stdout_lines: list[str] = []
    started_at = time.monotonic()
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    try:
        while time.monotonic() - started_at < timeout:
            if process.poll() is not None:
                break
            remaining = max(0.0, timeout - (time.monotonic() - started_at))
            events = selector.select(timeout=min(0.5, remaining))
            if not events:
                continue
            line = process.stdout.readline()
            if not line:
                continue
            stdout_lines.append(line)
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if event.get('type') == 'agent_end':
                break
    finally:
        selector.unregister(process.stdout)
        selector.close()
    return stdout_lines


def read_and_stop_process(process: subprocess.Popen[str]) -> str:
    if process.stdin is not None:
        process.stdin.close()
    if process.poll() is None:
        try:
            process.terminate()
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=10)
    if process.stderr is None:
        return ''
    return process.stderr.read()


def parse_events(stdout_lines: list[str]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line in stdout_lines:
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(value)
    return events


def count_events(events: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for event in events:
        event_type = str(event.get('type'))
        counts[event_type] = counts.get(event_type, 0) + 1
    return counts


def collect_assistant_text(events: list[dict[str, Any]]) -> str:
    final_text = collect_final_assistant_text(events)
    if final_text is not None:
        return final_text

    fragments: list[str] = []
    for event in events:
        message_event = event.get('assistantMessageEvent')
        if not isinstance(message_event, dict):
            continue
        if message_event.get('type') == 'text_delta':
            fragments.append(str(message_event.get('delta', '')))
    return ''.join(fragments)


def collect_final_assistant_text(events: list[dict[str, Any]]) -> str | None:
    for event in reversed(events):
        if event.get('type') == 'agent_end':
            messages = event.get('messages')
            if isinstance(messages, list):
                for message in reversed(messages):
                    text = assistant_message_text(message)
                    if text is not None:
                        return text
        if event.get('type') in {'message_end', 'turn_end'}:
            text = assistant_message_text(event.get('message'))
            if text is not None:
                return text
    return None


def assistant_message_text(message: Any) -> str | None:
    if not isinstance(message, dict) or message.get('role') != 'assistant':
        return None

    content = message.get('content')
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        fragments: list[str] = []
        for block in content:
            if isinstance(block, dict) and block.get('type') == 'text':
                fragments.append(str(block.get('text', '')))
        if fragments:
            return '\n'.join(fragments)
    return None


def classify_result(
    scenario: Scenario,
    tool_events: list[dict[str, Any]],
    events: list[dict[str, Any]],
    assistant_text: str,
    expected: str,
    workdir: Path,
    index: int,
) -> str:
    tool_names = [str(event.get('toolName', '')) for event in tool_events]
    if scenario.tool not in tool_names:
        if PARSE_ERROR_TOOL_NAME in tool_names:
            return 'parse_error_tool'
        return 'wrong_or_no_tool_call' if tool_events else 'no_tool_call'

    end_events = [event for event in tool_events if event.get('type') == 'tool_execution_end' and event.get('toolName') == scenario.tool]
    if not end_events:
        return 'tool_not_ended'
    if any(event.get('isError') for event in end_events):
        return 'tool_error'

    result_blob = json.dumps(end_events, ensure_ascii=False)
    if expected not in result_blob:
        return 'tool_result_mismatch'
    if not scenario.final_check(workdir, index):
        return 'side_effect_mismatch'

    agent_end_seen = any(event.get('type') == 'agent_end' for event in events)
    if not agent_end_seen:
        return 'tool_success_no_agent_end'
    if len(assistant_text) > 2000:
        return 'post_tool_runaway_text'
    if scenario.name == 'read':
        forbidden_read_expansions = [
            '2→',
            '3→',
            '"line": 2',
            'line 2',
            'P2',
            'P3',
        ]
        if any(fragment in assistant_text for fragment in forbidden_read_expansions):
            return 'read_fabricated_extra_lines'
    return 'tool_success'


def main() -> None:
    args = parse_args()
    if args.trials < 1:
        raise SystemExit('--trials must be >= 1')
    check_server(args.server_url)
    if args.output_root:
        output_root = Path(args.output_root).resolve()
        output_root.mkdir(parents=True, exist_ok=True)
    else:
        output_root = Path(tempfile.mkdtemp(prefix='pi-minicpm5-tool-matrix-'))
    config_dir = write_profiled_models_json(args, output_root)
    args.pi_config_dir = str(config_dir)

    results: list[TrialResult] = []
    for scenario in SCENARIOS:
        for index in range(1, args.trials + 1):
            print(f'RUN {scenario.name} trial {index}', file=sys.stderr, flush=True)
            results.append(run_trial(args, scenario, index, output_root))

    counts: dict[str, int] = {}
    by_scenario: dict[str, dict[str, int]] = {}
    for result in results:
        counts[result.classification] = counts.get(result.classification, 0) + 1
        scenario_counts = by_scenario.setdefault(result.scenario, {})
        scenario_counts[result.classification] = scenario_counts.get(result.classification, 0) + 1
    summary = {
        'output_root': str(output_root),
        'pi_config_dir': str(config_dir),
        'models_json': str(config_dir / 'models.json'),
        'counts': counts,
        'by_scenario': by_scenario,
        'trials': [result.__dict__ for result in results],
    }
    (output_root / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if any(result.classification != 'tool_success' for result in results):
        sys.exit(1)

if __name__ == '__main__':
    main()
