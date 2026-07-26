#!/usr/bin/env python3
"""Run a reproducible second-tool function-start cross-check with Ghidra.

The script creates temporary raw slices and a temporary Ghidra project.  Only
derived CSV/JSON metadata is copied to the requested output directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

PINNED_SHA256 = "2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7"

REGIONS = (
    ("boot8051", 0x40, 0x8000, "0x0", "8051:BE:16:default"),
    ("stbc8051", 0x8060, 0xFAC0, "0x0", "8051:BE:16:default"),
    ("updater8051", 0x17B40, 0xC180, "0x0", "8051:BE:16:default"),
    ("trap_sparc", 0x23CE0, 0x7760, "0xA00E0000", "sparc:BE:32:default"),
    ("main_sparc", 0x12E000, 0xEFCE0, "0x100000", "sparc:BE:32:default"),
    ("link_sparc", 0x3196E0, 0x2FB00, "0xA0060000", "sparc:BE:32:default"),
)


def parse_addresses(path: Path) -> set[int]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {int(row["address"], 16) for row in csv.DictReader(handle)}


def run(image: Path, output: Path, ghidra: Path, script_dir: Path) -> None:
    blob = image.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != PINNED_SHA256:
        raise SystemExit(f"refusing unpinned image SHA-256 {digest}")
    output.mkdir(parents=True, exist_ok=True)
    properties = ghidra.resolve().parents[1] / "Ghidra" / "application.properties"
    ghidra_version = "UNRESOLVED"
    if properties.exists():
        for line in properties.read_text(encoding="utf-8").splitlines():
            if line.startswith("application.version="):
                ghidra_version = line.split("=", 1)[1]
                break
    summaries = []
    with tempfile.TemporaryDirectory(prefix="odyssey-ghidra-") as temporary:
        temp = Path(temporary)
        project = temp / "project"
        project.mkdir()
        for name, offset, length, base, processor in REGIONS:
            raw = temp / f"{name}.bin"
            raw.write_bytes(blob[offset : offset + length])
            catalog = output / f"ghidra_{name}_functions.csv"
            command = [
                str(ghidra),
                str(project),
                f"crosscheck_{name}",
                "-import",
                str(raw),
                "-overwrite",
                "-loader",
                "BinaryLoader",
                "-loader-baseAddr",
                base,
                "-processor",
                processor,
                "-analysisTimeoutPerFile",
                "900",
                "-scriptPath",
                str(script_dir),
            ]
            if processor.startswith("8051:"):
                command.extend(["-preScript", "Seed8051Vectors.java"])
            command.extend(
                [
                    "-postScript",
                    "ExportAnalysisCatalog.java",
                    str(catalog),
                    "-deleteProject",
                ]
            )
            completed = subprocess.run(
                command, text=True, capture_output=True, check=False
            )
            if completed.returncode:
                raise RuntimeError(
                    f"Ghidra failed for {name}\n{completed.stdout}\n{completed.stderr}"
                )
            starts = parse_addresses(catalog)
            summaries.append(
                {
                    "region": name,
                    "file_offset": offset,
                    "length": length,
                    "runtime_base": int(base, 16),
                    "processor": processor,
                    "ghidra_function_starts": len(starts),
                }
            )
    (output / "ghidra_crosscheck_summary.json").write_text(
        json.dumps(
            {
                "image_sha256": digest,
                "ghidra_headless": str(ghidra),
                "ghidra_version": ghidra_version,
                "regions": summaries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--ghidra",
        type=Path,
        default=Path("/opt/ghidra/support/analyzeHeadless"),
    )
    args = parser.parse_args()
    run(
        args.image,
        args.output_dir,
        args.ghidra,
        Path(__file__).resolve().parent / "ghidra",
    )


if __name__ == "__main__":
    main()
