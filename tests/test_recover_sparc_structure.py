from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "recover_sparc_structure.py"
SPEC = importlib.util.spec_from_file_location("recover_sparc_structure", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def format3(rd: int, op3: int, rs1: int, immediate: int) -> int:
    return (
        (2 << 30)
        | (rd << 25)
        | (op3 << 19)
        | (rs1 << 14)
        | (1 << 13)
        | (immediate & 0x1FFF)
    )


class SparcStructureTests(unittest.TestCase):
    def test_save_and_returns_are_recognized(self) -> None:
        save_sp = format3(14, 0x3C, 14, -0x68)
        ret = format3(0, 0x38, 31, 8)
        retl = format3(0, 0x38, 15, 8)

        self.assertTrue(MODULE.is_save_prologue(save_sp))
        self.assertTrue(MODULE.is_return(ret))
        self.assertTrue(MODULE.is_return(retl))

    def test_indirect_call_is_not_a_return(self) -> None:
        indirect_call = format3(15, 0x38, 16, 0)

        self.assertFalse(MODULE.is_return(indirect_call))
        self.assertEqual(MODULE.fields(indirect_call)["rd"], 15)

    def test_signed_fields(self) -> None:
        self.assertEqual(MODULE.signed(0x1F98, 13), -0x68)
        self.assertEqual(MODULE.signed(0x18, 13), 0x18)

    def test_indirect_callback_slot_is_recovered(self) -> None:
        register = 1
        base = 0xA8037C00
        sethi = (register << 25) | (4 << 22) | ((base >> 10) & 0x3FFFFF)
        load = (
            (3 << 30)
            | (register << 25)
            | (register << 14)
            | (1 << 13)
            | 0x184
        )

        self.assertEqual(
            MODULE.resolve_indirect_source([sethi, load, 0], 2, register),
            "mem[0xA8037D84]",
        )

    def test_sethi_or_constant_is_recovered(self) -> None:
        register = 4
        base = 0xA8037C00
        sethi = (register << 25) | (4 << 22) | ((base >> 10) & 0x3FFFFF)
        or_immediate = format3(register, 0x02, register, 0x184)

        self.assertEqual(
            MODULE.resolve_register_constant([sethi, or_immediate, 0], 2, register),
            0xA8037D84,
        )

    def test_delay_slot_or_can_use_another_base_register(self) -> None:
        base_register = 16
        output_register = 8
        base = 0x001D2400
        sethi = (
            (base_register << 25)
            | (4 << 22)
            | ((base >> 10) & 0x3FFFFF)
        )
        or_immediate = format3(output_register, 0x02, base_register, 0x3D8)

        self.assertEqual(
            MODULE.resolve_register_constant([sethi, 0, or_immediate, 0], 3, output_register),
            0x001D27D8,
        )


if __name__ == "__main__":
    unittest.main()
