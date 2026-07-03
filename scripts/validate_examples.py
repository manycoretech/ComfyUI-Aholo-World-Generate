#!/usr/bin/env python3
"""Validate example workflow JSON files."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_API_NODES = {"aholo.world_generate", "aholo.world_wait"}


def main() -> int:
    examples = Path(__file__).resolve().parents[1] / "examples"
    errors: list[str] = []

    for path in sorted(examples.glob("*.json")):
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            errors.append(f"{path.name}: invalid JSON ({exc})")
            continue

        if path.name.endswith(".api.json"):
            types = {node.get("class_type") for node in data.values() if isinstance(node, dict)}
            missing = REQUIRED_API_NODES - types
            if missing:
                errors.append(f"{path.name}: missing nodes {sorted(missing)}")
        elif "nodes" not in data or "links" not in data:
            errors.append(f"{path.name}: expected UI workflow with nodes/links")

    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1

    print(f"OK: {len(list(examples.glob('*.json')))} workflow files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
