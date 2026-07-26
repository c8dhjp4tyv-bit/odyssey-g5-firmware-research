from __future__ import annotations

import importlib.util
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "inventory_firmware", ROOT / "tools" / "inventory_firmware.py"
)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


def package(*payloads: tuple[int, bytes, int | None]) -> bytes:
    result = bytearray(MODULE.MAGIC.ljust(MODULE.GLOBAL_HEADER_SIZE, b"\xff"))
    for target, payload, checksum in payloads:
        field = MODULE.byte_sum16(payload) if checksum is None else checksum
        result.extend(struct.pack(">IIII", target, len(payload), field, MODULE.RECORD_TAG))
        result.extend(b"\x00" * 16)
        result.extend(payload)
    return bytes(result)


class InventoryTests(unittest.TestCase):
    def test_parse_valid_records_and_sentinel(self) -> None:
        blob = package(
            (0x10000, b"\x01\x02\x03", None),
            (0x20000, b"abc", 0xFFFFFFFF),
        )
        records = MODULE.parse_records(blob)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].checksum_status, "match")
        self.assertEqual(records[0].checksum_computed, 6)
        self.assertEqual(records[1].checksum_status, "sentinel")
        self.assertEqual(
            records[1].payload_offset, records[1].header_offset + 0x20
        )

    def test_checksum_mismatch_is_reported_not_hidden(self) -> None:
        records = MODULE.parse_records(package((0x10000, b"\x01\x02", 0)))
        self.assertEqual(records[0].checksum_status, "mismatch")
        self.assertEqual(records[0].checksum_computed, 3)

    def test_rejects_bad_magic_tag_reserved_and_truncation(self) -> None:
        valid = bytearray(package((0x10000, b"\x01\x02", None)))

        bad_magic = bytearray(valid)
        bad_magic[0] = 0
        with self.assertRaises(ValueError):
            MODULE.parse_records(bytes(bad_magic))

        bad_tag = bytearray(valid)
        bad_tag[0x2C:0x30] = b"\x00\x00\x00\x00"
        with self.assertRaises(ValueError):
            MODULE.parse_records(bytes(bad_tag))

        bad_reserved = bytearray(valid)
        bad_reserved[0x30] = 1
        with self.assertRaises(ValueError):
            MODULE.parse_records(bytes(bad_reserved))

        with self.assertRaises(ValueError):
            MODULE.parse_records(bytes(valid[:-1]))


if __name__ == "__main__":
    unittest.main()
