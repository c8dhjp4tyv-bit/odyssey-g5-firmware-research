from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "infer_debug_symbols.py"
SPEC = importlib.util.spec_from_file_location("infer_debug_symbols", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class DebugSymbolTests(unittest.TestCase):
    def test_embedded_symbol_is_mapped_to_containing_function(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            functions = directory / "functions.json"
            strings = directory / "strings.json"
            functions.write_text(
                json.dumps(
                    [
                        {
                            "address": 0x1000,
                            "end": 0x1100,
                            "name": "sub_1000",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            strings.write_text(
                json.dumps(
                    [
                        {
                            "address": 0x2000,
                            "text": "[D] SecLibPicture_DriveBlackLevel: %d",
                            "xrefs": [0x1040],
                        }
                    ]
                ),
                encoding="utf-8",
            )

            rows = MODULE.infer(functions, strings)

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["function_address"], "0x00001000")
            self.assertEqual(
                rows[0]["candidate"], "SecLibPicture_DriveBlackLevel"
            )
            self.assertEqual(rows[0]["confidence"], "single-candidate")


if __name__ == "__main__":
    unittest.main()
