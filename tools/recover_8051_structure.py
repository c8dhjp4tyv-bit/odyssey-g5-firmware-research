#!/usr/bin/env python3
"""Recover reachable 8051 call targets in NVTSC_IMG records 0, 1, and 2.

This is a small control-flow decoder, not an 8051 emulator. It follows reset
and interrupt-vector paths, direct calls, direct jumps, and conditional
branches. Computed ``JMP @A+DPTR`` sites are reported as explicit boundaries.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

from inventory_firmware import parse_records

EXPECTED_IMAGE_SHA256 = (
    "2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7"
)

# Intel MCS-51 instruction lengths, indexed by opcode.
LENGTHS = (
    1, 2, 3, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    3, 2, 3, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    3, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    3, 2, 1, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 3, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 1, 2, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    3, 2, 2, 1, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    2, 2, 2, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    1, 1, 3, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    3, 2, 2, 1, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2,
    1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 2, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
)


@dataclass(frozen=True)
class FunctionCandidate:
    record_index: int
    address: int
    file_offset: int
    vector_root: bool
    direct_call_count: int
    first_opcode: int


@dataclass(frozen=True)
class ComputedJump:
    record_index: int
    address: int
    file_offset: int
    opcode: int


@dataclass(frozen=True)
class DirectCallEdge:
    record_index: int
    site: int
    file_offset: int
    target: int
    target_internal: bool


def signed_byte(value: int) -> int:
    return value - 0x100 if value & 0x80 else value


def absolute_11bit_target(address: int, opcode: int, low: int) -> int:
    return ((address + 2) & 0xF800) | ((opcode & 0xE0) << 3) | low


def vector_roots(code: bytes) -> set[int]:
    candidates = {0, *(range(3, min(len(code), 0x84), 8))}
    roots = {0}
    for address in candidates:
        if address >= len(code):
            continue
        opcode = code[address]
        if opcode in (0x02, 0x32) or opcode & 0x1F == 0x01:
            roots.add(address)
    return roots


def analyze_record(
    code: bytes, record_index: int, payload_offset: int
) -> tuple[
    list[FunctionCandidate],
    list[ComputedJump],
    list[DirectCallEdge],
    dict[str, int],
]:
    roots = vector_roots(code)
    calls: Counter[int] = Counter()
    reachable: set[int] = set()
    computed: list[ComputedJump] = []
    call_edges: list[DirectCallEdge] = []
    work = list(roots)

    while work:
        address = work.pop()
        if address in reachable or not 0 <= address < len(code):
            continue
        opcode = code[address]
        length = LENGTHS[opcode]
        if address + length > len(code):
            continue
        reachable.add(address)
        following = address + length

        if opcode == 0x12:  # LCALL addr16
            target = (code[address + 1] << 8) | code[address + 2]
            calls[target] += 1
            call_edges.append(
                DirectCallEdge(
                    record_index, address, payload_offset + address,
                    target, 0 <= target < len(code),
                )
            )
            work.extend((target, following))
        elif opcode & 0x1F == 0x11:  # ACALL addr11
            target = absolute_11bit_target(address, opcode, code[address + 1])
            calls[target] += 1
            call_edges.append(
                DirectCallEdge(
                    record_index, address, payload_offset + address,
                    target, 0 <= target < len(code),
                )
            )
            work.extend((target, following))
        elif opcode == 0x02:  # LJMP addr16
            work.append((code[address + 1] << 8) | code[address + 2])
        elif opcode & 0x1F == 0x01:  # AJMP addr11
            work.append(
                absolute_11bit_target(address, opcode, code[address + 1])
            )
        elif opcode == 0x80:  # SJMP rel
            work.append(following + signed_byte(code[address + 1]))
        elif opcode == 0x73:  # JMP @A+DPTR
            computed.append(
                ComputedJump(
                    record_index=record_index,
                    address=address,
                    file_offset=payload_offset + address,
                    opcode=opcode,
                )
            )
        elif opcode in (0x22, 0x32):  # RET / RETI
            continue
        elif opcode in (0x10, 0x20, 0x30, 0xB4, 0xB5, 0xB6, 0xB7, 0xD5) or (
            0xB8 <= opcode <= 0xBF
        ):
            work.extend(
                (
                    following,
                    following + signed_byte(code[address + length - 1]),
                )
            )
        elif opcode in (0x40, 0x50, 0x60, 0x70) or 0xD8 <= opcode <= 0xDF:
            work.extend(
                (
                    following,
                    following + signed_byte(code[address + length - 1]),
                )
            )
        else:
            work.append(following)

    entries = roots | {target for target in calls if 0 <= target < len(code)}
    functions = [
        FunctionCandidate(
            record_index=record_index,
            address=address,
            file_offset=payload_offset + address,
            vector_root=address in roots,
            direct_call_count=calls[address],
            first_opcode=code[address],
        )
        for address in sorted(entries)
    ]
    summary = {
        "record_index": record_index,
        "payload_length": len(code),
        "vector_roots": len(roots),
        "reachable_instructions": len(reachable),
        "reachable_bytes": sum(LENGTHS[code[address]] for address in reachable),
        "function_entry_candidates": len(functions),
        "direct_call_sites": sum(calls.values()),
        "external_call_targets": sum(
            count for target, count in calls.items() if not 0 <= target < len(code)
        ),
        "computed_jumps": len(computed),
    }
    return functions, computed, call_edges, summary


def write_csv(path: Path, rows: list[object]) -> None:
    dictionaries = [asdict(row) for row in rows]
    if not dictionaries:
        return
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(dictionaries[0]), lineterminator="\n"
        )
        writer.writeheader()
        for row in dictionaries:
            for key in ("address", "file_offset", "first_opcode", "opcode"):
                if key in row:
                    width = 2 if key in ("first_opcode", "opcode") else 8
                    row[key] = f"0x{row[key]:0{width}X}"
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--allow-unpinned", action="store_true")
    args = parser.parse_args()

    image = args.image.read_bytes()
    digest = hashlib.sha256(image).hexdigest()
    if not args.allow_unpinned and digest != EXPECTED_IMAGE_SHA256:
        raise ValueError("base firmware SHA-256 mismatch")
    records = parse_records(image)

    all_functions: list[FunctionCandidate] = []
    all_computed: list[ComputedJump] = []
    all_call_edges: list[DirectCallEdge] = []
    summaries = []
    for index in (0, 1, 2):
        record = records[index]
        code = image[
            record.payload_offset : record.payload_offset + record.length
        ]
        functions, computed, call_edges, summary = analyze_record(
            code, index, record.payload_offset
        )
        all_functions.extend(functions)
        all_computed.extend(computed)
        all_call_edges.extend(call_edges)
        summaries.append(summary)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "function_candidates.csv", all_functions)
    write_csv(args.output_dir / "computed_jumps.csv", all_computed)
    write_csv(args.output_dir / "direct_call_edges.csv", all_call_edges)
    (args.output_dir / "summary.json").write_text(
        json.dumps({"image_sha256": digest, "records": summaries}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summaries, indent=2))


if __name__ == "__main__":
    main()
