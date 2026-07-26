import importlib.util
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
SPEC = importlib.util.spec_from_file_location(
    "inventory_companion_records", TOOLS / "inventory_companion_records.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = MODULE
SPEC.loader.exec_module(MODULE)


class CompanionRecordTests(unittest.TestCase):
    def test_read_exception_table_accepts_expected_schema(self):
        payload = bytearray(4 + len(MODULE.EXCEPTION_IDS) * 8)
        struct.pack_into(">I", payload, 0, 0x05B8D800)
        for index, trap_id in enumerate(MODULE.EXCEPTION_IDS):
            struct.pack_into(
                ">II", payload, 4 + index * 8, trap_id, 0x1F1000 + index * 4
            )
        table = MODULE.read_exception_table(
            bytes(payload), 0, 0x1F0000, 0x2F0000
        )
        self.assertEqual(table["entry_count"], 17)
        self.assertEqual(table["entries"][-1]["id"], 0x2B)

    def test_read_exception_table_rejects_wrong_id(self):
        payload = bytearray(4 + len(MODULE.EXCEPTION_IDS) * 8)
        struct.pack_into(">I", payload, 0, 0x05B8D800)
        for index, trap_id in enumerate(MODULE.EXCEPTION_IDS):
            struct.pack_into(
                ">II", payload, 4 + index * 8, trap_id, 0x1F1000 + index * 4
            )
        struct.pack_into(">I", payload, 4, 99)
        with self.assertRaisesRegex(ValueError, "unexpected trap id"):
            MODULE.read_exception_table(bytes(payload), 0, 0x1F0000, 0x2F0000)
