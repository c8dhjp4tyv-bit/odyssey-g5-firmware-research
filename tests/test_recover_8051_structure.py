from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "recover_8051_structure.py"
SPEC = importlib.util.spec_from_file_location("recover_8051_structure", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class Structure8051Tests(unittest.TestCase):
    def test_opcode_table_is_complete(self) -> None:
        self.assertEqual(len(MODULE.LENGTHS), 256)
        self.assertEqual(MODULE.LENGTHS[0x12], 3)
        self.assertEqual(MODULE.LENGTHS[0x22], 1)

    def test_direct_call_target_becomes_candidate(self) -> None:
        code = bytes(
            [
                0x12,
                0x00,
                0x06,  # 0000: LCALL 0006
                0x22,  # 0003: RET
                0x00,
                0x00,
                0x22,  # 0006: RET
            ]
        )

        functions, computed, summary = MODULE.analyze_record(code, 1, 0x100)

        self.assertEqual([row.address for row in functions], [0, 6])
        self.assertEqual(functions[1].direct_call_count, 1)
        self.assertEqual(computed, [])
        self.assertEqual(summary["reachable_instructions"], 3)

    def test_absolute_11bit_target_uses_current_page(self) -> None:
        self.assertEqual(
            MODULE.absolute_11bit_target(0x1234, 0x11, 0x56),
            0x1056,
        )


if __name__ == "__main__":
    unittest.main()
