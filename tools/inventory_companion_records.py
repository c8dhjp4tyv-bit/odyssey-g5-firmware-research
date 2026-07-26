#!/usr/bin/env python3
"""Inspect the paired SPARC companion-data records in an NVTSC image.

This tool is deliberately read-only.  It reports the exception-name table
shared by records 4 and 8 and validates that every string pointer falls in the
expected main/link address range.  It does not attempt to invent an undocumented
loader ABI.
"""

from __future__ import annotations

import argparse
import json
import struct
from pathlib import Path

from inventory_firmware import parse_records

EXCEPTION_IDS = (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 0x20, 0x28, 0x24, 0x2A, 0x2B)


def read_exception_table(
    payload: bytes, offset: int, pointer_min: int, pointer_max: int
) -> dict[str, object]:
    signature = struct.unpack_from(">I", payload, offset)[0]
    if signature != 0x05B8D800:
        raise ValueError(f"bad exception-table header at +0x{offset:X}")
    cursor = offset + 4
    entries: list[dict[str, int]] = []
    for expected_id in EXCEPTION_IDS:
        trap_id, pointer = struct.unpack_from(">II", payload, cursor)
        if trap_id != expected_id:
            raise ValueError(
                f"unexpected trap id 0x{trap_id:X} at +0x{cursor:X}"
            )
        if not pointer_min <= pointer < pointer_max:
            raise ValueError(
                f"exception pointer 0x{pointer:X} outside expected address range"
            )
        entries.append({"id": trap_id, "string_pointer": pointer})
        cursor += 8
    return {
        "offset": offset,
        "signature": signature,
        "entry_count": len(entries),
        "entries": entries,
        "end_offset": cursor,
    }


def inspect(path: Path) -> dict[str, object]:
    blob = path.read_bytes()
    records = parse_records(blob)
    if len(records) != 10:
        raise ValueError(f"expected 10 records, found {len(records)}")

    payloads = [
        blob[row.payload_offset : row.payload_offset + row.length] for row in records
    ]
    main = read_exception_table(payloads[4], 0xB4, 0x001F0000, 0x002F0000)
    link = read_exception_table(payloads[8], 0, 0xA0060000, 0xA0090000)
    return {
        "main_companion": {
            "record": 4,
            "flash_target": records[4].target,
            **main,
        },
        "link_companion": {
            "record": 8,
            "flash_target": records[8].target,
            **link,
        },
        "same_trap_id_sequence": [row["id"] for row in main["entries"]]
        == [row["id"] for row in link["entries"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inspect paired main/link SPARC companion-data records"
    )
    parser.add_argument("image", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.image), indent=2))


if __name__ == "__main__":
    main()
