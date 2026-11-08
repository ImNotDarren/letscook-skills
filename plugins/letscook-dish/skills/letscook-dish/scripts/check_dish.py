#!/usr/bin/env python3
"""Validate a Let's Cook dish JSON and copy it to the macOS clipboard.

Usage:
    python3 check_dish.py dish.json      # validate and copy
    python3 check_dish.py - < dish.json  # read from stdin
    python3 check_dish.py --no-copy dish.json

Mirrors the dish parser and importer in the Let's Cook app.
Exit code 0 means the app will import the dish exactly as written.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

CATEGORIES = {"Mains", "Sides", "Sweets"}
TOKEN = re.compile(r"\[([^\]|]+)\|([^\]]+)\]|\{(\d+) min\}")
NUMBER = re.compile(r"^(\d+(\.\d+)?|\d+/\d+)$")


def check_step(step: str, where: str) -> list[str]:
    """Return problems in one step string."""
    problems: list[str] = []
    timers = 0
    for match in TOKEN.finditer(step):
        if match.group(3):
            timers += 1
            continue
        amount, _, unit = match.group(1).strip().partition(" ")
        if not NUMBER.match(amount) or unit[:1].isdigit():
            problems.append(
                f"{where}: amount '{match.group(1)}' must start with a number like 2, 0.5 or 1/2 "
                "(no ranges, no '1½', no '1 1/2'); otherwise it will not scale or total"
            )
    leftover = TOKEN.sub("", step)
    if any(c in leftover for c in "[]{}|"):
        problems.append(f"{where}: stray [ ] {{ }} or | outside a valid token: {step!r}")
    if timers > 1:
        problems.append(f"{where}: {timers} timers; Cook Mode only uses the first {{N min}} per step")
    return problems


def check_dish(dish: Any, where: str) -> list[str]:
    """Return problems in one dish object."""
    if not isinstance(dish, dict):
        return [f"{where}: must be an object"]
    problems: list[str] = []
    if dish.get("letscook") != 1:
        problems.append(f'{where}: needs "letscook": 1')
    if not isinstance(dish.get("name"), str) or not dish["name"].strip():
        problems.append(f"{where}: needs a non-empty name")
    if dish.get("category", "Mains") not in CATEGORIES:
        problems.append(f"{where}: category must be one of {sorted(CATEGORIES)}")
    serves = dish.get("serves", 4)
    if not isinstance(serves, int) or isinstance(serves, bool) or not 1 <= serves <= 24:
        problems.append(f"{where}: serves must be an integer from 1 to 24")
    steps = dish.get("steps")
    if not isinstance(steps, list) or not steps or not all(isinstance(s, str) and s.strip() for s in steps):
        problems.append(f"{where}: steps must be a non-empty list of non-empty strings")
        return problems
    for index, step in enumerate(steps, 1):
        problems += check_step(step, f"{where} step {index}")
    return problems


def main(argv: list[str]) -> int:
    copy = "--no-copy" not in argv
    args = [a for a in argv if a != "--no-copy"]
    source = args[0] if args else "-"
    text = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")
    try:
        data = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"Invalid JSON: {error}", file=sys.stderr)
        return 1
    dishes = data if isinstance(data, list) else [data]
    if not dishes:
        print("Empty list", file=sys.stderr)
        return 1
    problems = [p for i, d in enumerate(dishes, 1) for p in check_dish(d, d.get("name", f"dish {i}") if isinstance(d, dict) else f"dish {i}")]
    if problems:
        print("\n".join(problems), file=sys.stderr)
        return 1
    compact = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    if copy:
        try:
            subprocess.run(["pbcopy"], input=compact.encode("utf-8"), check=True)
        except FileNotFoundError:
            # ponytail: macOS only; elsewhere the user copies the printed JSON
            print(f"OK: {len(dishes)} dish(es) valid. pbcopy not found, copy this:\n{compact}")
            return 0
        print(f"OK: {len(dishes)} dish(es) copied to the clipboard ({len(compact)} chars).")
    else:
        print(f"OK: {len(dishes)} dish(es) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
