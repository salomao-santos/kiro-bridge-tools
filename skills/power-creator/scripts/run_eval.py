#!/usr/bin/env python3
from __future__ import annotations
"""Run trigger evaluation for a Power description.

Tests whether a Power's description causes the configured backend to trigger
(invoke / read the Power) for a set of queries. Outputs results as JSON.

Adapted from skill-creator/scripts/run_eval.py:
  - Replaces direct `claude -p` subprocess with scripts.runtime.invoke()
  - SKILL.md → POWER.md
  - .claude/commands/ → .kiro/powers/ (configurable via KIRO_POWERS_DIR)
"""

import argparse
import json
import os
import sys
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from scripts.runtime import invoke, select_backend
from scripts.utils import parse_power_md


def find_project_root() -> Path:
    """Walk up from cwd looking for .kiro/ (then .claude/ as fallback)."""
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".kiro").is_dir():
            return parent
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


def run_single_query(
    query: str,
    power_name: str,
    power_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single query through the runtime adapter and return whether the
    Power was triggered.

    Writes a temporary trampoline POWER.md into the project's
    .kiro/powers/<unique>/ so the backend can discover it. Cleans up on exit.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{power_name}-power-{unique_id}"
    powers_subdir = os.environ.get("KIRO_POWERS_DIR", ".kiro/powers")
    power_dir = Path(project_root) / powers_subdir / clean_name
    power_md = power_dir / "POWER.md"

    try:
        power_dir.mkdir(parents=True, exist_ok=True)
        indented_desc = "\n  ".join(power_description.split("\n"))
        content = (
            f"---\n"
            f"name: {clean_name}\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {power_name}\n\n"
            f"This Power handles: {power_description}\n"
        )
        power_md.write_text(content)

        accumulated_partial = ""
        triggered = False
        for ev in invoke(
            query,
            power_dir=str(power_dir),
            model=model,
            timeout=timeout,
            cwd=project_root,
        ):
            t = ev.get("type")
            if t == "tool_use":
                tool_name = ev.get("name", "")
                tool_input = ev.get("input") or {}
                if tool_name in ("Power", "Skill", "Read"):
                    inp_text = json.dumps(tool_input)
                    if clean_name in inp_text:
                        triggered = True
                        break
            elif t == "tool_use_delta":
                accumulated_partial += ev.get("partial_json", "")
                if clean_name in accumulated_partial:
                    triggered = True
                    break
            elif t == "done":
                break
            elif t == "error":
                print(f"Warning: backend error: {ev.get('message')}", file=sys.stderr)
                break
        return triggered
    finally:
        try:
            if power_md.exists():
                power_md.unlink()
            if power_dir.exists():
                power_dir.rmdir()
        except OSError:
            pass


def run_eval(
    eval_set: list[dict],
    power_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return aggregated results."""
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    power_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            query_triggers.setdefault(query, [])
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                print(f"Warning: query failed: {e}", file=sys.stderr)
                query_triggers[query].append(False)

    results = []
    for query, triggers in query_triggers.items():
        item = query_items[query]
        trigger_rate = sum(triggers) / len(triggers)
        should_trigger = item["should_trigger"]
        if should_trigger:
            did_pass = trigger_rate >= trigger_threshold
        else:
            did_pass = trigger_rate < trigger_threshold
        results.append({
            "query": query,
            "should_trigger": should_trigger,
            "trigger_rate": trigger_rate,
            "triggers": sum(triggers),
            "runs": len(triggers),
            "pass": did_pass,
        })

    passed = sum(1 for r in results if r["pass"])
    total = len(results)
    return {
        "power_name": power_name,
        "skill_name": power_name,  # back-compat for downstream report scripts
        "description": description,
        "backend": select_backend(),
        "results": results,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": total - passed,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a Power")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--power-path", "--skill-path", dest="power_path", required=True,
                        help="Path to Power directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--runs-per-query", type=int, default=3)
    parser.add_argument("--trigger-threshold", type=float, default=0.5)
    parser.add_argument("--model", default=None)
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    power_path = Path(args.power_path)
    name, original_description, _ = parse_power_md(power_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Backend: {select_backend()}", file=sys.stderr)
        print(f"Evaluating: {description}", file=sys.stderr)

    output = run_eval(
        eval_set=eval_set,
        power_name=name,
        description=description,
        num_workers=args.num_workers,
        timeout=args.timeout,
        project_root=project_root,
        runs_per_query=args.runs_per_query,
        trigger_threshold=args.trigger_threshold,
        model=args.model,
    )

    if args.verbose:
        s = output["summary"]
        print(f"Results: {s['passed']}/{s['total']} passed", file=sys.stderr)
        for r in output["results"]:
            status = "PASS" if r["pass"] else "FAIL"
            print(f"  [{status}] rate={r['triggers']}/{r['runs']} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
