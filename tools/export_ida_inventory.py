#!/usr/bin/env python3
"""Export read-only function/string/call metadata from an IDA database.

Run with IDA's IDALib Python environment. No database changes are saved.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import idapro
import ida_bytes
import ida_funcs
import ida_ida
import ida_segment
import ida_xref
import idautils


def clean(value: object) -> str:
    return str(value).replace("\x00", "").replace("\r", "\\r").replace("\n", "\\n")


def export_database(idb: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    result = idapro.open_database(str(idb), False)
    if result != 0:
        raise RuntimeError(f"IDA failed to open {idb}: return code {result}")

    try:
        segments = []
        for index in range(ida_segment.get_segm_qty()):
            segment = ida_segment.getnseg(index)
            segments.append(
                {
                    "name": ida_segment.get_segm_name(segment),
                    "class": ida_segment.get_segm_class(segment),
                    "start": segment.start_ea,
                    "end": segment.end_ea,
                    "size": segment.end_ea - segment.start_ea,
                    "permissions": segment.perm,
                    "bitness": segment.bitness,
                }
            )

        strings = []
        for item in idautils.Strings():
            refs = sorted(int(ref) for ref in idautils.DataRefsTo(item.ea))
            strings.append(
                {
                    "address": int(item.ea),
                    "length": int(item.length),
                    "type": int(item.strtype),
                    "text": clean(item),
                    "xref_count": len(refs),
                    "xrefs": refs,
                }
            )

        functions = []
        edges = set()
        for address in idautils.Functions():
            function = ida_funcs.get_func(address)
            if function is None:
                continue
            instructions = 0
            callees = set()
            for item_address in idautils.FuncItems(address):
                if ida_bytes.is_code(ida_bytes.get_flags(item_address)):
                    instructions += 1
                for target in idautils.CodeRefsFrom(item_address, False):
                    target_function = ida_funcs.get_func(target)
                    if target_function and target_function.start_ea != address:
                        callees.add(int(target_function.start_ea))
                        edges.add((int(address), int(target_function.start_ea)))
            callers = set()
            for xref in idautils.XrefsTo(address, ida_xref.XREF_FAR):
                source = ida_funcs.get_func(xref.frm)
                if source and source.start_ea != address:
                    callers.add(int(source.start_ea))
            functions.append(
                {
                    "address": int(address),
                    "end": int(function.end_ea),
                    "size": int(function.end_ea - address),
                    "name": ida_funcs.get_func_name(address),
                    "instructions": instructions,
                    "caller_count": len(callers),
                    "callees": sorted(callees),
                }
            )

        metadata = {
            "database": idb.name,
            "processor": ida_ida.inf_get_procname(),
            "big_endian": bool(ida_ida.inf_is_be()),
            "min_ea": int(ida_ida.inf_get_min_ea()),
            "max_ea": int(ida_ida.inf_get_max_ea()),
            "segments": segments,
            "function_count": len(functions),
            "string_count": len(strings),
            "call_edge_count": len(edges),
        }
        for name, value in (
            ("metadata.json", metadata),
            ("functions.json", functions),
            ("strings.json", strings),
        ):
            (output / name).write_text(
                json.dumps(value, indent=2, ensure_ascii=False) + "\n",
                encoding="utf-8",
            )

        with (output / "functions.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(
                ["address", "end", "size", "name", "instructions", "callers", "callees"]
            )
            for row in functions:
                writer.writerow(
                    [
                        f"0x{row['address']:08X}",
                        f"0x{row['end']:08X}",
                        f"0x{row['size']:X}",
                        row["name"],
                        row["instructions"],
                        row["caller_count"],
                        " ".join(f"0x{x:08X}" for x in row["callees"]),
                    ]
                )
        with (output / "callgraph.csv").open("w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["caller", "callee"])
            for caller, callee in sorted(edges):
                writer.writerow([f"0x{caller:08X}", f"0x{callee:08X}"])
    finally:
        idapro.close_database(False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("idb", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    export_database(args.idb.resolve(), args.output_dir.resolve())


if __name__ == "__main__":
    main()
