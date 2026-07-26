#!/usr/bin/env python3
"""Extract function-like symbol candidates embedded in debug strings.

Vendor release builds often keep messages such as
``SecLibPicture_DriveBlackLevel`` inside longer format strings. IDA does not
turn those tokens into symbols automatically. This tool maps each token to the
IDA function containing the string xref and reports ambiguity rather than
silently choosing a name.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

TOKEN = re.compile(
    r"(?:__|Sec|DRV_|SYSAPI_|USBCop_|Jay_|FRC_|HDMI_|"
    r"DP(?:RX|TX)?_|DPTX_|DPRX_|OSDLib|MApi_|MDrv_|MsOS_)"
    r"[A-Za-z0-9_]{3,120}"
)


@dataclass(frozen=True)
class FunctionRange:
    address: int
    end: int
    name: str


def load_functions(path: Path) -> list[FunctionRange]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return sorted(
        (
            FunctionRange(
                address=int(row["address"]),
                end=int(row["end"]),
                name=str(row["name"]),
            )
            for row in rows
        ),
        key=lambda row: row.address,
    )


def containing_function(
    functions: list[FunctionRange], address: int
) -> FunctionRange | None:
    low = 0
    high = len(functions) - 1
    while low <= high:
        middle = (low + high) // 2
        function = functions[middle]
        if address < function.address:
            high = middle - 1
        elif address >= function.end:
            low = middle + 1
        else:
            return function
    return None


def infer(functions_path: Path, strings_path: Path) -> list[dict[str, object]]:
    functions = load_functions(functions_path)
    strings = json.loads(strings_path.read_text(encoding="utf-8"))
    evidence: dict[tuple[int, str], dict[str, object]] = {}

    for item in strings:
        tokens = sorted(set(TOKEN.findall(str(item["text"]))))
        if not tokens:
            continue
        for xref in item["xrefs"]:
            function = containing_function(functions, int(xref))
            if function is None:
                continue
            for token in tokens:
                key = (function.address, token)
                row = evidence.setdefault(
                    key,
                    {
                        "function_address": function.address,
                        "ida_name": function.name,
                        "candidate": token,
                        "evidence_count": 0,
                        "string_addresses": set(),
                    },
                )
                row["evidence_count"] = int(row["evidence_count"]) + 1
                row["string_addresses"].add(int(item["address"]))

    candidate_counts: dict[int, int] = {}
    for function_address, _ in evidence:
        candidate_counts[function_address] = (
            candidate_counts.get(function_address, 0) + 1
        )

    output = []
    for row in evidence.values():
        addresses = sorted(row.pop("string_addresses"))
        row["function_address"] = f"0x{int(row['function_address']):08X}"
        row["evidence_addresses"] = " ".join(
            f"0x{address:08X}" for address in addresses
        )
        count = candidate_counts[int(row["function_address"], 16)]
        row["candidates_for_function"] = count
        row["confidence"] = (
            "single-candidate"
            if count == 1
            else "ranked-ambiguous"
        )
        output.append(row)
    output.sort(
        key=lambda row: (
            int(str(row["function_address"]), 16),
            -int(row["evidence_count"]),
            str(row["candidate"]),
        )
    )
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("functions_json", type=Path)
    parser.add_argument("strings_json", type=Path)
    parser.add_argument("output_csv", type=Path)
    args = parser.parse_args()
    rows = infer(args.functions_json, args.strings_json)
    if not rows:
        raise ValueError("no embedded debug-symbol candidates found")
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    with args.output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(
        json.dumps(
            {
                "rows": len(rows),
                "functions": len({row["function_address"] for row in rows}),
                "single_candidate_functions": len(
                    {
                        row["function_address"]
                        for row in rows
                        if row["confidence"] == "single-candidate"
                    }
                ),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
