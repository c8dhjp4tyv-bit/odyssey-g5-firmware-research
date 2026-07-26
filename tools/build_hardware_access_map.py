#!/usr/bin/env python3
"""Aggregate every statically recovered absolute RAM/MMIO access."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


def classify(target: int) -> tuple[str, str]:
    if 0xA8000000 <= target < 0xA9000000:
        return "RUNTIME_RAM", "HIGH"
    if 0xC0000000 <= target < 0xE0000000:
        return "PROBABLE_MMIO", "PROBABLE"
    return "UNRESOLVED_ABSOLUTE_TARGET", "UNRESOLVED"


def build(input_csv: Path) -> list[dict[str, str]]:
    grouped: dict[int, list[dict[str, str]]] = defaultdict(list)
    with input_csv.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            grouped[int(row["target"], 16)].append(row)
    result = []
    for target, refs in sorted(grouped.items()):
        target_class, confidence = classify(target)
        functions = sorted(
            {row["ida_function"] for row in refs if row["ida_function"]}
        )
        sites = sorted({row["site"] for row in refs})
        widths = sorted({int(row["width"]) for row in refs})
        result.append(
            {
                "target": f"0x{target:08X}",
                "target_class": target_class,
                "reads": str(sum(row["access"] == "load" for row in refs)),
                "writes": str(sum(row["access"] == "store" for row in refs)),
                "widths": " ".join(map(str, widths)),
                "sites": " ".join(sites),
                "functions": " | ".join(functions) or "UNRESOLVED",
                "confidence": confidence,
                "bit_semantics": "UNRESOLVED",
                "evidence": "SETHI/OR-or-ADD plus load/store immediate",
            }
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()
    result = build(args.input_csv)
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(result[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(result)
    print(f"absolute_targets={len(result)}")


if __name__ == "__main__":
    main()
