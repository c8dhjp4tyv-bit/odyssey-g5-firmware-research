#!/usr/bin/env python3
"""Classify every recovered indirect transfer without inventing targets."""

from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path


def read(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def classify(generated: Path) -> list[dict[str, str]]:
    callbacks: dict[int, set[int]] = defaultdict(set)
    for row in read(generated / "main_callback_bindings.csv"):
        callbacks[int(row["slot"], 16)].add(int(row["callback"], 16))

    result: list[dict[str, str]] = []
    for row in read(generated / "main_indirect_control_flow.csv"):
        source = row["target_source"]
        absolute = re.fullmatch(r"mem\[0x([0-9A-Fa-f]+)\]", source)
        targets: set[int] = set()
        if row["kind"] == "computed-jump":
            dispatch = (
                "jump-table-global-slot"
                if absolute
                else "jump-table-or-computed-dispatch"
            )
            status = "UNRESOLVED_RUNTIME_INDEX_OR_TABLE"
            evidence = "JMPL with rd=%g0; table/index contents not statically fixed"
        elif absolute and int(absolute.group(1), 16) in callbacks:
            slot = int(absolute.group(1), 16)
            dispatch = "callback-static-registration"
            targets = callbacks[slot]
            status = "STATIC_TARGET_SET_RECOVERED"
            evidence = f"slot 0x{slot:08X} matched registration stores"
        elif absolute:
            dispatch = "runtime-populated-global-function-pointer"
            status = "UNRESOLVED_RUNTIME_POPULATED"
            evidence = "absolute RAM slot recovered; no static registration matched"
        else:
            dispatch = "function-pointer-register"
            status = "UNRESOLVED_DATAFLOW_OR_RUNTIME"
            evidence = "indirect call target loaded/computed through register"
        result.append(
            {
                "architecture": "SPARC-V8-BE32",
                "record": "5",
                "site": row["address"],
                "file_offset": row["file_offset"],
                "raw_kind": row["kind"],
                "dispatch_class": dispatch,
                "target_source": source,
                "static_targets": (
                    " ".join(f"0x{target:08X}" for target in sorted(targets))
                    or "NONE"
                ),
                "resolution_status": status,
                "containing_function": row["ida_function"] or "UNRESOLVED",
                "evidence": evidence,
            }
        )

    for row in read(generated / "8051_computed_jumps.csv"):
        result.append(
            {
                "architecture": "MCS-51/8051",
                "record": row["record_index"],
                "site": row["address"],
                "file_offset": row["file_offset"],
                "raw_kind": "computed-jump",
                "dispatch_class": "jump-table-A-plus-DPTR",
                "target_source": "code[DPTR + A]",
                "static_targets": "NONE",
                "resolution_status": "UNRESOLVED_RUNTIME_INDEX_OR_TABLE",
                "containing_function": "UNRESOLVED",
                "evidence": "opcode 0x73 JMP @A+DPTR; live DPTR/A not captured",
            }
        )
    result.sort(key=lambda row: (int(row["record"]), int(row["site"], 16)))
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generated_dir", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()
    result = classify(args.generated_dir)
    write(args.output_csv, result)
    print(f"indirect_sites={len(result)}")


if __name__ == "__main__":
    main()
