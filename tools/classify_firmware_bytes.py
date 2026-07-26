#!/usr/bin/env python3
"""Produce a gap-free, non-overlapping byte classification for the package.

The manifest deliberately distinguishes a proven class from an unresolved
mixed code/data region.  It never turns uncertainty into a guessed type.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

from inventory_firmware import GLOBAL_HEADER_SIZE, MAGIC, parse_records

EXPECTED_SHA256 = (
    "2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7"
)


@dataclass(frozen=True)
class Region:
    start: int
    end: int
    record: str
    classification: str
    detail: str
    confidence: str
    evidence: str

    @property
    def length(self) -> int:
        return self.end - self.start


def add(
    rows: list[Region],
    start: int,
    end: int,
    record: str,
    classification: str,
    detail: str,
    confidence: str,
    evidence: str,
) -> None:
    if end <= start:
        raise ValueError(f"invalid region 0x{start:X}..0x{end:X}")
    rows.append(
        Region(start, end, record, classification, detail, confidence, evidence)
    )


def classify(blob: bytes) -> list[Region]:
    records = parse_records(blob)
    rows: list[Region] = []
    add(rows, 0, len(MAGIC), "global", "HEADER", "NVTSC_IMG magic", "CONFIRMED", "literal magic")
    add(
        rows,
        len(MAGIC),
        GLOBAL_HEADER_SIZE,
        "global",
        "UNRESOLVED",
        "global header fields/reserved bytes; semantics not decoded",
        "UNRESOLVED",
        "container position and stable bytes only",
    )

    for record in records:
        base = record.header_offset
        label = str(record.index)
        add(rows, base, base + 4, label, "HEADER", "flash target", "CONFIRMED", "big-endian record field")
        add(rows, base + 4, base + 8, label, "HEADER", "payload length", "CONFIRMED", "big-endian record field")
        add(rows, base + 8, base + 12, label, "CHECKSUM", "payload byte-sum or sentinel", "CONFIRMED", record.checksum_status)
        add(rows, base + 12, base + 16, label, "HEADER", "record tag 0x04000000", "CONFIRMED", "validated constant")
        add(rows, base + 16, base + 32, label, "PADDING", "reserved zero bytes", "CONFIRMED", "validated all-zero")

        p = record.payload_offset
        e = p + record.length
        if record.index in (0, 1, 2):
            detail = {
                0: "8051 boot executable with inline tables/data; per-byte code/data boundary unresolved",
                1: "8051 STBC executable with inline tables/data; per-byte code/data boundary unresolved",
                2: "8051 updater executable with inline tables/data; per-byte code/data boundary unresolved",
            }[record.index]
            add(rows, p, e, label, "UNRESOLVED_MIXED_CODE_DATA", detail, "UNRESOLVED", "reachable CFG and strings prove both classes")
        elif record.index == 3:
            add(rows, p, e, label, "UNRESOLVED_MIXED_CODE_DATA", "SPARC trap/vector code with inline tables", "UNRESOLVED", "SPARC disassembly; exact inline-data boundaries incomplete")
        elif record.index == 4:
            add(rows, p, e, label, "DATA", "main SPARC companion trap/runtime/config data", "HIGH", "pointer tables, trap schema, named USB-data objects")
        elif record.index == 5:
            if blob[p : p + 0x10000] != b"\xFF" * 0x10000:
                raise ValueError("record 5 FF padding invariant failed")
            if blob[p + 0x10000 : p + 0x100000] != b"\x00" * 0xF0000:
                raise ValueError("record 5 zero padding invariant failed")
            add(rows, p, p + 0x10000, label, "PADDING", "0xFF application-container prefix", "CONFIRMED", "all bytes 0xFF")
            add(rows, p + 0x10000, p + 0x100000, label, "PADDING", "zero application-container prefix", "CONFIRMED", "all bytes zero")
            add(rows, p + 0x100000, p + 0x100320, label, "HEADER", "CHK marker/build metadata and padding", "HIGH", "AA557788/CHK marker; some fields unresolved")
            add(rows, p + 0x100320, e, label, "UNRESOLVED_MIXED_CODE_DATA", "main SPARC executable and inline constant tables", "UNRESOLVED", "IDA/raw CFG cover code; precise inline-table boundaries incomplete")
        elif record.index == 6:
            add(rows, p, e, label, "DATA", "main strings/resources/descriptors/EDID/persistent defaults", "HIGH", "mapped data segment and xrefs")
        elif record.index == 7:
            add(rows, p, e, label, "UNRESOLVED_MIXED_CODE_DATA", "link/EQ SPARC executable with inline tables", "UNRESOLVED", "IDA functions plus PreAEQ tables; exact boundaries incomplete")
        elif record.index == 8:
            add(rows, p, e, label, "DATA", "link SPARC companion trap/runtime/config data", "HIGH", "validated homologous trap schema and pointers")
        elif record.index == 9:
            if blob[p + 0x48 : e] != b"\xFF" * (e - (p + 0x48)):
                raise ValueError("record 9 footer sentinel invariant failed")
            add(rows, p, p + 0x48, label, "DATA", "nine footer partition target/length pairs", "CONFIRMED", "big-endian pair table")
            add(rows, p + 0x48, e, label, "PADDING", "0xFFFFFFFF footer terminators", "CONFIRMED", "three sentinel pairs")
        else:
            add(rows, p, e, label, "UNRESOLVED", "unknown record payload", "UNRESOLVED", "no semantic evidence")

    rows.sort(key=lambda row: row.start)
    cursor = 0
    for row in rows:
        if row.start != cursor:
            raise ValueError(
                f"coverage gap/overlap at 0x{cursor:X}; next starts 0x{row.start:X}"
            )
        cursor = row.end
    if cursor != len(blob):
        raise ValueError(f"coverage ends at 0x{cursor:X}, file ends at 0x{len(blob):X}")
    return rows


def write_csv(path: Path, rows: list[Region]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dictionaries = []
    for row in rows:
        item = asdict(row)
        item["start"] = f"0x{row.start:08X}"
        item["end"] = f"0x{row.end:08X}"
        item["length"] = f"0x{row.length:X}"
        dictionaries.append(item)
    fields = ("start", "end", "length", "record", "classification", "detail", "confidence", "evidence")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(dictionaries)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_csv", type=Path)
    parser.add_argument("--allow-unpinned", action="store_true")
    args = parser.parse_args()
    blob = args.image.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if not args.allow_unpinned and digest != EXPECTED_SHA256:
        raise SystemExit(f"refusing unpinned image SHA-256 {digest}")
    rows = classify(blob)
    write_csv(args.output_csv, rows)
    print(f"regions={len(rows)} bytes=0x{len(blob):X} coverage=PASS")


if __name__ == "__main__":
    main()
