#!/usr/bin/env python3
"""Regenerate all non-curated public analysis catalogs.

Inputs are the owner-supplied pinned image and read-only IDA inventory
directories produced by export_ida_inventory.py. Ghidra is invoked as the
independent second tool unless --skip-ghidra is used with existing catalogs.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path


def execute(command: list[str], output: Path | None = None) -> None:
    completed = subprocess.run(command, text=True, capture_output=True)
    if completed.returncode:
        raise RuntimeError(
            f"command failed: {' '.join(command)}\n"
            f"{completed.stdout}\n{completed.stderr}"
        )
    if output is not None:
        output.write_text(completed.stdout, encoding="utf-8")


def normalized_copy(source: Path, destination: Path) -> None:
    destination.write_text(
        source.read_text(encoding="utf-8").replace("\r\n", "\n"),
        encoding="utf-8",
    )


def regenerate(
    image: Path,
    ida_root: Path,
    output: Path,
    skip_ghidra: bool,
    ghidra: Path,
) -> None:
    tools = Path(__file__).resolve().parent
    output.mkdir(parents=True, exist_ok=True)
    python = sys.executable
    main = ida_root / "main"
    aux = ida_root / "aux"
    boot = ida_root / "boot8051"
    for directory in (main, aux, boot):
        if not (directory / "functions.json").exists():
            raise ValueError(f"missing IDA inventory: {directory}")

    execute(
        [python, str(tools / "inventory_firmware.py"), str(image), "--json"],
        output / "package_inventory.json",
    )
    execute(
        [python, str(tools / "inventory_companion_records.py"), str(image)],
        output / "companion_records.json",
    )
    execute(
        [
            python,
            str(tools / "classify_firmware_bytes.py"),
            str(image),
            str(output / "byte_classification.csv"),
        ]
    )

    execute(
        [
            "node",
            str(tools / "classify_ida_inventory.js"),
            str(main),
            str(output / "main_functions.csv"),
        ]
    )
    execute(
        [
            "node",
            str(tools / "classify_ida_inventory.js"),
            str(aux),
            str(output / "aux_functions.csv"),
        ]
    )
    execute(
        [
            "node",
            str(tools / "infer_symbol_anchors.js"),
            str(main),
            str(output / "main_symbol_anchors.csv"),
        ]
    )
    execute(
        [
            "node",
            str(tools / "infer_symbol_anchors.js"),
            str(aux),
            str(output / "aux_symbol_anchors.csv"),
        ]
    )
    normalized_copy(boot / "functions.csv", output / "boot8051_functions.csv")
    normalized_copy(main / "callgraph.csv", output / "main_ida_callgraph.csv")
    normalized_copy(aux / "callgraph.csv", output / "aux_ida_callgraph.csv")

    execute(
        [
            python,
            str(tools / "infer_debug_symbols.py"),
            str(main / "functions.json"),
            str(main / "strings.json"),
            str(output / "main_embedded_symbol_candidates.csv"),
        ]
    )
    execute(
        [
            python,
            str(tools / "infer_debug_symbols.py"),
            str(aux / "functions.json"),
            str(aux / "strings.json"),
            str(output / "aux_embedded_symbol_candidates.csv"),
        ]
    )

    with tempfile.TemporaryDirectory(prefix="odyssey-regenerate-") as temporary:
        temp = Path(temporary)
        sparc = temp / "sparc"
        i8051 = temp / "8051"
        execute(
            [
                python,
                str(tools / "recover_sparc_structure.py"),
                str(image),
                str(main / "functions.json"),
                str(sparc),
            ]
        )
        execute(
            [
                python,
                str(tools / "recover_8051_structure.py"),
                str(image),
                str(i8051),
            ]
        )
        mappings = {
            sparc / "function_candidates.csv": "main_recovered_function_candidates.csv",
            sparc / "indirect_sites.csv": "main_indirect_control_flow.csv",
            sparc / "absolute_memory_refs.csv": "main_absolute_memory_refs.csv",
            sparc / "callback_bindings.csv": "main_callback_bindings.csv",
            sparc / "direct_call_edges.csv": "main_direct_call_edges.csv",
            sparc / "summary.json": "main_structure_summary.json",
            i8051 / "function_candidates.csv": "8051_function_candidates.csv",
            i8051 / "computed_jumps.csv": "8051_computed_jumps.csv",
            i8051 / "direct_call_edges.csv": "8051_direct_call_edges.csv",
            i8051 / "summary.json": "8051_structure_summary.json",
        }
        for source, name in mappings.items():
            normalized_copy(source, output / name)

    if not skip_ghidra:
        execute(
            [
                python,
                str(tools / "run_ghidra_crosscheck.py"),
                str(image),
                str(output / "ghidra"),
                "--ghidra",
                str(ghidra),
            ]
        )
    elif not (output / "ghidra" / "ghidra_main_sparc_functions.csv").exists():
        raise ValueError("--skip-ghidra requires existing Ghidra catalogs")

    commands = (
        (
            "compare_function_tools.py",
            [str(output), str(output / "function_tool_crosscheck.json")],
        ),
        (
            "build_function_registry.py",
            [
                str(output),
                str(output / "function_registry.csv"),
                str(output / "function_memory_effects.csv"),
            ],
        ),
        (
            "classify_indirect_control_flow.py",
            [str(output), str(output / "indirect_control_flow_detailed.csv")],
        ),
        (
            "build_hardware_access_map.py",
            [
                str(output / "main_absolute_memory_refs.csv"),
                str(output / "hardware_absolute_accesses.csv"),
            ],
        ),
    )
    for script, arguments in commands:
        execute([python, str(tools / script), *arguments])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("ida_inventory_root", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--skip-ghidra", action="store_true")
    parser.add_argument(
        "--ghidra",
        type=Path,
        default=Path("/opt/ghidra/support/analyzeHeadless"),
    )
    args = parser.parse_args()
    regenerate(
        args.image,
        args.ida_inventory_root,
        args.output_dir,
        args.skip_ghidra,
        args.ghidra,
    )
    print("REGENERATE_ANALYSIS=PASS")


if __name__ == "__main__":
    main()
