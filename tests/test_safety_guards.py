"""Regression tests for optimized-Python firmware safety guards."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build_mga_only.py"
VERIFY = ROOT / "tools" / "verify_mga_only.py"


class OptimizedModeSafetyTests(unittest.TestCase):
    def run_tool(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-O", *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_builder_rejects_wrong_image_under_optimized_python(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            wrong = directory / "wrong.img"
            wrong.write_bytes(b"not firmware")

            result = self.run_tool(
                str(BUILD),
                str(wrong),
                "--output-dir",
                str(directory / "output"),
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERROR: unexpected firmware size", result.stderr)
            self.assertFalse((directory / "output").exists())

    def test_verifier_rejects_wrong_images_under_optimized_python(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            base = directory / "base.img"
            generated = directory / "generated.img"
            base.write_bytes(b"not firmware")
            generated.write_bytes(b"not firmware either")

            result = self.run_tool(str(VERIFY), str(base), str(generated))

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERROR: unexpected base firmware size", result.stderr)


if __name__ == "__main__":
    unittest.main()
