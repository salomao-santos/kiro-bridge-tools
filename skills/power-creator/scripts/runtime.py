#!/usr/bin/env python3
"""Runtime backend adapter for power-creator.

The eval scripts (run_eval.py, run_loop.py, improve_description.py) call into
this module instead of shelling out to `claude -p` directly. This lets the
same eval pipeline run against Kiro CLI, Kiro IDE (via terminal or prompt),
the legacy Claude CLI, or a deterministic mock backend used in CI.

Public surface:
    invoke(query, *, power_dir=None, model=None, timeout=30, mode="stream") -> Iterator[dict]
    invoke_once(prompt, *, model=None, timeout=300) -> str
    select_backend() -> str
    available_backends() -> list[str]

Event schema (yielded by invoke):
    {"type": "tool_use", "name": str, "input": dict}
    {"type": "text", "text": str}
    {"type": "done", "result": dict|None}
    {"type": "error", "message": str}
"""

from __future__ import annotations

import json
import os
import select
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Iterator


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

_BACKENDS = ("kiro_cli", "kiro_ide_terminal", "kiro_ide_prompt", "claude_cli", "mock")


def select_backend() -> str:
    """Pick a backend. Honor KIRO_POWER_RUNTIME, else auto-detect."""
    forced = os.environ.get("KIRO_POWER_RUNTIME", "").strip()
    if forced:
        if forced not in _BACKENDS:
            raise RuntimeError(
                f"KIRO_POWER_RUNTIME={forced!r} not in {_BACKENDS}"
            )
        return forced

    kiro_bin = os.environ.get("KIRO_BIN", "kiro")
    if shutil.which(kiro_bin):
        return "kiro_cli"
    if shutil.which("claude"):
        return "claude_cli"
    return "mock"


def available_backends() -> list[str]:
    """Return backends that have a binary on PATH (or are always-available)."""
    out = []
    if shutil.which(os.environ.get("KIRO_BIN", "kiro")):
        out.append("kiro_cli")
        out.append("kiro_ide_terminal")
    if os.environ.get("KIRO_IDE_PROMPT_FIFO"):
        out.append("kiro_ide_prompt")
    if shutil.which("claude"):
        out.append("claude_cli")
    out.append("mock")
    return out


# ---------------------------------------------------------------------------
# Streaming invoke (for trigger detection)
# ---------------------------------------------------------------------------

def invoke(
    query: str,
    *,
    power_dir: str | Path | None = None,
    model: str | None = None,
    timeout: int = 30,
    cwd: str | Path | None = None,
    backend: str | None = None,
) -> Iterator[dict]:
    """Invoke the model with `query` and yield events.

    Used by run_eval.py for trigger detection. Caller short-circuits on the
    first matching `tool_use` event.
    """
    b = backend or select_backend()
    if b in ("kiro_cli", "kiro_ide_terminal"):
        yield from _invoke_kiro_cli(query, model=model, timeout=timeout, cwd=cwd)
    elif b == "kiro_ide_prompt":
        yield from _invoke_kiro_ide_prompt(query, model=model, timeout=timeout)
    elif b == "claude_cli":
        yield from _invoke_claude_cli(query, model=model, timeout=timeout, cwd=cwd)
    elif b == "mock":
        yield from _invoke_mock(query, power_dir=power_dir)
    else:
        yield {"type": "error", "message": f"unknown backend: {b}"}


def invoke_once(prompt: str, *, model: str | None = None, timeout: int = 300, backend: str | None = None) -> str:
    """One-shot: send `prompt` on stdin, return full text response.

    Used by improve_description.py to rewrite the description.
    """
    b = backend or select_backend()
    if b in ("kiro_cli", "kiro_ide_terminal"):
        return _invoke_kiro_cli_text(prompt, model=model, timeout=timeout)
    if b == "kiro_ide_prompt":
        return _invoke_kiro_ide_prompt_text(prompt, timeout=timeout)
    if b == "claude_cli":
        return _invoke_claude_cli_text(prompt, model=model, timeout=timeout)
    if b == "mock":
        return _mock_rewrite_response(prompt)
    raise RuntimeError(f"unknown backend: {b}")


# ---------------------------------------------------------------------------
# Backend: kiro_cli (also handles kiro_ide_terminal)
# ---------------------------------------------------------------------------

def _kiro_cmd(query: str, model: str | None, stream: bool) -> list[str]:
    """Build a Kiro CLI command. All flags are env-overridable so this works
    even before we know the exact Kiro CLI surface."""
    binary = os.environ.get("KIRO_BIN", "kiro")
    prompt_flag = os.environ.get("KIRO_PROMPT_FLAG", "-p")
    cmd = [binary, prompt_flag, query]

    if stream:
        fmt = os.environ.get("KIRO_OUTPUT_FORMAT_FLAG", "--output-format stream-json").split()
        if fmt:
            cmd.extend(fmt)
        partial = os.environ.get("KIRO_INCLUDE_PARTIAL_FLAG", "--include-partial-messages").split()
        if partial:
            cmd.extend(partial)
        verbose = os.environ.get("KIRO_VERBOSE_FLAG", "--verbose").split()
        if verbose:
            cmd.extend(verbose)

    if model:
        model_flag = os.environ.get("KIRO_MODEL_FLAG", "--model")
        cmd.extend([model_flag, model])
    return cmd


def _invoke_kiro_cli(query: str, *, model: str | None, timeout: int, cwd) -> Iterator[dict]:
    cmd = _kiro_cmd(query, model, stream=True)
    yield from _run_stream(cmd, timeout=timeout, cwd=cwd)


def _invoke_kiro_cli_text(prompt: str, *, model: str | None, timeout: int) -> str:
    """One-shot text mode. Prompt on stdin."""
    binary = os.environ.get("KIRO_BIN", "kiro")
    prompt_flag = os.environ.get("KIRO_PROMPT_FLAG", "-p")
    cmd = [binary, prompt_flag]
    text_flag = os.environ.get("KIRO_TEXT_FORMAT_FLAG", "--output-format text").split()
    if text_flag:
        cmd.extend(text_flag)
    if model:
        cmd.extend([os.environ.get("KIRO_MODEL_FLAG", "--model"), model])

    env = _clean_env()
    result = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, env=env, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kiro exited {result.returncode}\nstderr: {result.stderr}")
    return result.stdout


# ---------------------------------------------------------------------------
# Backend: kiro_ide_prompt (FIFO-based)
# ---------------------------------------------------------------------------

def _invoke_kiro_ide_prompt(query: str, *, model, timeout: int) -> Iterator[dict]:
    fifo = os.environ.get("KIRO_IDE_PROMPT_FIFO")
    if not fifo:
        yield {"type": "error", "message": "KIRO_IDE_PROMPT_FIFO not set"}
        return

    out_path = Path(fifo + ".out")
    Path(fifo).write_text(query + "\n")

    deadline = time.time() + timeout
    while time.time() < deadline:
        if out_path.exists():
            text = out_path.read_text()
            out_path.unlink(missing_ok=True)
            # Trigger heuristic: look for tool_use marker in response.
            if '"type": "tool_use"' in text or '"tool_use"' in text:
                for line in text.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        ev = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    yield ev
            else:
                yield {"type": "text", "text": text}
            yield {"type": "done", "result": None}
            return
        time.sleep(0.5)
    yield {"type": "error", "message": "timeout waiting for FIFO response"}


def _invoke_kiro_ide_prompt_text(prompt: str, *, timeout: int) -> str:
    fifo = os.environ.get("KIRO_IDE_PROMPT_FIFO")
    if not fifo:
        raise RuntimeError("KIRO_IDE_PROMPT_FIFO not set")
    out_path = Path(fifo + ".out")
    Path(fifo).write_text(prompt + "\n")
    deadline = time.time() + timeout
    while time.time() < deadline:
        if out_path.exists():
            text = out_path.read_text()
            out_path.unlink(missing_ok=True)
            return text
        time.sleep(0.5)
    raise RuntimeError("timeout waiting for FIFO response")


# ---------------------------------------------------------------------------
# Backend: claude_cli (legacy)
# ---------------------------------------------------------------------------

def _invoke_claude_cli(query: str, *, model, timeout: int, cwd) -> Iterator[dict]:
    cmd = [
        "claude", "-p", query,
        "--output-format", "stream-json",
        "--verbose",
        "--include-partial-messages",
    ]
    if model:
        cmd.extend(["--model", model])
    yield from _run_stream(cmd, timeout=timeout, cwd=cwd, parse=_parse_claude_event)


def _invoke_claude_cli_text(prompt: str, *, model, timeout: int) -> str:
    cmd = ["claude", "-p", "--output-format", "text"]
    if model:
        cmd.extend(["--model", model])
    env = _clean_env()
    result = subprocess.run(
        cmd, input=prompt, capture_output=True, text=True, env=env, timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude exited {result.returncode}\nstderr: {result.stderr}")
    return result.stdout


# ---------------------------------------------------------------------------
# Backend: mock (deterministic, no network)
# ---------------------------------------------------------------------------

def _invoke_mock(query: str, *, power_dir) -> Iterator[dict]:
    """Mock: trigger when the trampoline Power's description keywords appear
    in the query. Reads POWER.md from power_dir, extracts the description,
    uses a simple keyword-overlap heuristic. Lets validate-eval.sh exercise
    the pipeline without a model."""
    trampoline_name = ""
    description = ""
    if power_dir:
        trampoline_name = Path(power_dir).name
        power_md = Path(power_dir) / "POWER.md"
        if power_md.exists():
            in_frontmatter = False
            collecting_desc = False
            for line in power_md.read_text().splitlines():
                if line.strip() == "---":
                    if in_frontmatter:
                        break
                    in_frontmatter = True
                    continue
                if not in_frontmatter:
                    continue
                if line.startswith("description:"):
                    description = line[len("description:"):].strip().strip("|>-").strip()
                    collecting_desc = True
                elif collecting_desc and (line.startswith("  ") or line.startswith("\t")):
                    description += " " + line.strip()
                elif collecting_desc and line and not line[0].isspace():
                    collecting_desc = False

    stop = {
        "this","that","when","where","user","with","from","into","have","been",
        "what","your","they","them","than","then","wants","want","uses","used",
        "using","should","could","would","might","needs","make","made","does",
        "doing","also","very","more","less","only","just","even","such","like",
        "kind","type","form","case","well","good","best","power","kiro",
        "skill","the","and","for","are","any","all","but","use","you","can",
        "phrases","trigger","triggers","mention","mentions","triggering","via",
    }
    q_low = query.lower()
    keywords = {
        w.strip(".,;:!?\"'()<>[]")
        for w in description.lower().split()
        if len(w) > 3 and w.strip(".,;:!?\"'()<>[]").lower() not in stop
    }
    matches = [k for k in keywords if k and k in q_low]
    triggered = bool(matches)

    if triggered:
        yield {
            "type": "tool_use",
            "name": "Power",
            "input": {"power": trampoline_name, "matched_keywords": matches[:5]},
        }
    else:
        yield {"type": "text", "text": "(mock) no Power triggered for this query"}
    yield {"type": "done", "result": None}


def _mock_rewrite_response(prompt: str) -> str:
    """Mock improve_description response: echo a trivially-modified description."""
    return "<new_description>Use this Power when the user mentions a kiro power related task.</new_description>"


# ---------------------------------------------------------------------------
# Stream parsing helpers
# ---------------------------------------------------------------------------

def _clean_env() -> dict:
    return {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}


def _run_stream(cmd: list[str], *, timeout: int, cwd, parse=None) -> Iterator[dict]:
    """Spawn `cmd`, stream stdout line-by-line, parse JSON, yield events.

    `parse` adapts backend-specific stream shapes to the unified event schema.
    If None, assume each line is already a unified event dict.
    """
    env = _clean_env()
    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            cwd=cwd, env=env,
        )
    except FileNotFoundError as e:
        yield {"type": "error", "message": f"backend binary missing: {e}"}
        return

    start = time.time()
    buffer = ""
    try:
        while time.time() - start < timeout:
            if process.poll() is not None:
                remaining = process.stdout.read()
                if remaining:
                    buffer += remaining.decode("utf-8", errors="replace")
                break

            ready, _, _ = select.select([process.stdout], [], [], 1.0)
            if not ready:
                continue

            chunk = os.read(process.stdout.fileno(), 8192)
            if not chunk:
                break
            buffer += chunk.decode("utf-8", errors="replace")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue
                try:
                    raw = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if parse is None:
                    yield raw
                    continue
                for ev in parse(raw):
                    yield ev
        yield {"type": "done", "result": None}
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def _parse_claude_event(raw: dict) -> Iterator[dict]:
    """Translate a `claude -p` stream-json event into our unified schema."""
    t = raw.get("type")
    if t == "stream_event":
        se = raw.get("event", {})
        if se.get("type") == "content_block_start":
            cb = se.get("content_block", {})
            if cb.get("type") == "tool_use":
                yield {
                    "type": "tool_use",
                    "name": cb.get("name", ""),
                    "input": cb.get("input") or {},
                }
        elif se.get("type") == "content_block_delta":
            delta = se.get("delta", {})
            if delta.get("type") == "input_json_delta":
                yield {
                    "type": "tool_use_delta",
                    "partial_json": delta.get("partial_json", ""),
                }
    elif t == "assistant":
        for c in raw.get("message", {}).get("content", []):
            if c.get("type") == "tool_use":
                yield {
                    "type": "tool_use",
                    "name": c.get("name", ""),
                    "input": c.get("input") or {},
                }
    elif t == "result":
        yield {"type": "done", "result": raw}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="power-creator runtime adapter")
    p.add_argument("--query", required=True)
    p.add_argument("--power-dir", default=None)
    p.add_argument("--model", default=None)
    p.add_argument("--timeout", type=int, default=30)
    p.add_argument("--backend", default=None, choices=_BACKENDS)
    args = p.parse_args()
    print(f"# backend: {args.backend or select_backend()}", file=sys.stderr)
    for ev in invoke(args.query, power_dir=args.power_dir, model=args.model,
                     timeout=args.timeout, backend=args.backend):
        print(json.dumps(ev))
