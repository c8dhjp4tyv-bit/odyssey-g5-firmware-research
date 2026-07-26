#!/usr/bin/env python3
"""Read-only inventory tool for Novatek NVTSC_IMG monitor firmware packages."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import struct
from dataclasses import asdict, dataclass
from pathlib import Path

MAGIC = b"\x7fNVTSC_IMG\n"
GLOBAL_HEADER_SIZE = 0x20
RECORD_HEADER_SIZE = 0x20
RECORD_TAG = 0x04000000


@dataclass(frozen=True)
class Record:
    index: int
    header_offset: int
    payload_offset: int
    target: int
    length: int
    checksum_field: int
    checksum_computed: int
    checksum_status: str
    sha256: str
    entropy: float


def byte_sum16(data: bytes) -> int:
    return sum(data) & 0xFFFF


def shannon_entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = [0] * 256
    for value in data:
        counts[value] += 1
    size = len(data)
    return -sum(
        (count / size) * math.log2(count / size) for count in counts if count
    )


def parse_records(blob: bytes) -> list[Record]:
    if len(blob) < GLOBAL_HEADER_SIZE or not blob.startswith(MAGIC):
        raise ValueError("not an NVTSC_IMG package")

    records: list[Record] = []
    cursor = GLOBAL_HEADER_SIZE
    while cursor < len(blob):
        if len(blob) - cursor < RECORD_HEADER_SIZE:
            raise ValueError(f"truncated record header at 0x{cursor:X}")
        target, length, checksum, tag = struct.unpack_from(">IIII", blob, cursor)
        reserved = blob[cursor + 0x10 : cursor + RECORD_HEADER_SIZE]
        if tag != RECORD_TAG:
            raise ValueError(f"unexpected record tag 0x{tag:08X} at 0x{cursor:X}")
        if any(reserved):
            raise ValueError(f"nonzero reserved bytes at 0x{cursor + 0x10:X}")

        payload_offset = cursor + RECORD_HEADER_SIZE
        payload_end = payload_offset + length
        if payload_end > len(blob):
            raise ValueError(
                f"record {len(records)} extends beyond EOF: 0x{payload_end:X}"
            )
        payload = blob[payload_offset:payload_end]
        computed = byte_sum16(payload)
        if checksum == 0xFFFFFFFF:
            status = "sentinel"
        elif checksum == computed:
            status = "match"
        else:
            status = "mismatch"
        records.append(
            Record(
                index=len(records),
                header_offset=cursor,
                payload_offset=payload_offset,
                target=target,
                length=length,
                checksum_field=checksum,
                checksum_computed=computed,
                checksum_status=status,
                sha256=hashlib.sha256(payload).hexdigest(),
                entropy=round(shannon_entropy(payload), 4),
            )
        )
        cursor = payload_end

    if cursor != len(blob):
        raise ValueError(f"unparsed trailing bytes begin at 0x{cursor:X}")
    return records


def inventory(path: Path) -> dict[str, object]:
    blob = path.read_bytes()
    records = parse_records(blob)
    return {
        "filename": path.name,
        "size": len(blob),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "sum16": byte_sum16(blob),
        "magic": MAGIC.hex(),
        "records": [asdict(record) for record in records],
    }


def print_text(report: dict[str, object]) -> None:
    print(f"file:   {report['filename']}")
    print(f"size:   0x{report['size']:X} ({report['size']:,})")
    print(f"sha256: {report['sha256']}")
    print(f"sum16:  0x{report['sum16']:04X}")
    print()
    print(
        "idx  header    payload   target    length    field       calc  status    entropy"
    )
    for row in report["records"]:
        print(
            f"{row['index']:>3}  "
            f"0x{row['header_offset']:06X} "
            f"0x{row['payload_offset']:06X} "
            f"0x{row['target']:06X} "
            f"0x{row['length']:06X} "
            f"0x{row['checksum_field']:08X} "
            f"0x{row['checksum_computed']:04X} "
            f"{row['checksum_status']:<9} "
            f"{row['entropy']:.4f}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inventory an owner-supplied NVTSC_IMG firmware package"
    )
    parser.add_argument("image", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    report = inventory(args.image)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print_text(report)


if __name__ == "__main__":
    main()
