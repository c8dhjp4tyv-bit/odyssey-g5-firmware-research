import importlib.util
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "classify_firmware_bytes", TOOLS / "classify_firmware_bytes.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class ByteClassificationTests(unittest.TestCase):
    def test_gap_or_overlap_is_rejected_by_construction(self):
        global_header = bytearray(0x20)
        global_header[: len(MODULE.MAGIC)] = MODULE.MAGIC
        payload = b"\x00" * 0x60
        record = (
            struct.pack(">IIII", 0x6000, len(payload), sum(payload), 0x04000000)
            + b"\x00" * 16
            + payload
        )
        rows = MODULE.classify(bytes(global_header) + record)
        self.assertEqual(rows[0].start, 0)
        self.assertEqual(rows[-1].end, len(global_header) + len(record))
        for left, right in zip(rows, rows[1:]):
            self.assertEqual(left.end, right.start)

    def test_unknown_mixed_is_explicit_for_8051(self):
        global_header = bytearray(0x20)
        global_header[: len(MODULE.MAGIC)] = MODULE.MAGIC
        payload = b"\x02\x00\x00"
        record = (
            struct.pack(">IIII", 0, len(payload), sum(payload), 0x04000000)
            + b"\x00" * 16
            + payload
        )
        rows = MODULE.classify(bytes(global_header) + record)
        self.assertEqual(rows[-1].classification, "UNRESOLVED_MIXED_CODE_DATA")
