#!/usr/bin/env python3
"""Summarize address-level agreement between independent analyzers."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def starts(path: Path, field: str = "address") -> set[int]:
    return {int(row[field], 16) for row in read(path)}


def comparison(name: str, tools: dict[str, set[int]]) -> dict[str, object]:
    union = set().union(*tools.values())
    common = set.intersection(*tools.values()) if tools else set()
    membership: dict[str, int] = defaultdict(int)
    for item in union:
        key = "+".join(sorted(tool for tool, values in tools.items() if item in values))
        membership[key] += 1
    return {
        "region": name,
        "tool_counts": {tool: len(values) for tool, values in tools.items()},
        "union": len(union),
        "all_tools_intersection": len(common),
        "membership_counts": dict(sorted(membership.items())),
    }


def build(generated: Path) -> dict[str, object]:
    raw_8051: dict[int, set[int]] = defaultdict(set)
    for row in read(generated / "8051_function_candidates.csv"):
        raw_8051[int(row["record_index"])].add(int(row["address"], 16))
    regions = [
        comparison(
            "main_sparc",
            {
                "IDA": starts(generated / "main_functions.csv"),
                "Ghidra": starts(
                    generated / "ghidra" / "ghidra_main_sparc_functions.csv"
                ),
                "raw_scanner": starts(
                    generated / "main_recovered_function_candidates.csv"
                ),
            },
        ),
        comparison(
            "link_sparc",
            {
                "IDA": starts(generated / "aux_functions.csv"),
                "Ghidra": starts(
                    generated / "ghidra" / "ghidra_link_sparc_functions.csv"
                ),
            },
        ),
        comparison(
            "boot8051",
            {
                "IDA": starts(generated / "boot8051_functions.csv"),
                "Ghidra": starts(
                    generated / "ghidra" / "ghidra_boot8051_functions.csv"
                ),
                "raw_scanner": raw_8051[0],
            },
        ),
        comparison(
            "stbc8051",
            {
                "Ghidra": starts(
                    generated / "ghidra" / "ghidra_stbc8051_functions.csv"
                ),
                "raw_scanner": raw_8051[1],
            },
        ),
        comparison(
            "updater8051",
            {
                "Ghidra": starts(
                    generated / "ghidra" / "ghidra_updater8051_functions.csv"
                ),
                "raw_scanner": raw_8051[2],
            },
        ),
        comparison(
            "trap_sparc",
            {
                "Ghidra": starts(
                    generated / "ghidra" / "ghidra_trap_sparc_functions.csv"
                )
            },
        ),
    ]
    return {"regions": regions}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generated_dir", type=Path)
    parser.add_argument("output_json", type=Path)
    args = parser.parse_args()
    report = build(args.generated_dir)
    args.output_json.write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
