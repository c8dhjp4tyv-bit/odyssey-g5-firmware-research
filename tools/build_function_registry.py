#!/usr/bin/env python3
"""Build one provenance-rich registry for every recovered callable entry.

Unknown ABI and semantic fields are written as UNRESOLVED with a reason.
Tool disagreement is preserved rather than resolved by guessing.
"""

from __future__ import annotations

import argparse
import bisect
import csv
from collections import defaultdict
from pathlib import Path


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def address(value: str) -> int:
    return int(value, 16)


def address_list(value: str) -> set[int]:
    return {int(item, 16) for item in value.split() if item}


def write(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(records[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(records)


def load_graph(path: Path) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
    callers: dict[int, set[int]] = defaultdict(set)
    callees: dict[int, set[int]] = defaultdict(set)
    for row in rows(path):
        caller, callee = address(row["caller"]), address(row["callee"])
        callees[caller].add(callee)
        callers[callee].add(caller)
    return callers, callees


def symbol_map(generated: Path, prefix: str) -> dict[int, tuple[str, str]]:
    result: dict[int, tuple[str, str]] = {}
    anchors = generated / f"{prefix}_symbol_anchors.csv"
    if anchors.exists():
        for row in rows(anchors):
            result[address(row["function_address"])] = (
                row["inferred_name"],
                f"debug-string-anchor:{row['evidence_address']}",
            )
    embedded = generated / f"{prefix}_embedded_symbol_candidates.csv"
    if embedded.exists():
        for row in rows(embedded):
            item = address(row["function_address"])
            if item not in result and row["confidence"] == "single-candidate":
                result[item] = (
                    row["candidate"],
                    f"embedded-debug-token:{row['evidence_addresses']}",
                )
    return result


def format_addresses(values: set[int]) -> str:
    return " ".join(f"0x{item:08X}" for item in sorted(values)) or "NONE_RECOVERED"


def choose_size(tool_sizes: dict[str, int]) -> tuple[str, str]:
    if not tool_sizes:
        return "UNRESOLVED", "no analyzer established an end boundary"
    values = set(tool_sizes.values())
    rendered = ";".join(f"{name}=0x{value:X}" for name, value in tool_sizes.items())
    if len(values) == 1:
        return f"0x{next(iter(values)):X}", rendered
    return "UNRESOLVED", f"tool boundary disagreement: {rendered}"


def registry_row(
    *,
    key: str,
    architecture: str,
    record: str,
    runtime_address: int,
    file_offset: int,
    name: str,
    name_evidence: str,
    size: str,
    size_evidence: str,
    callers: set[int],
    callees: set[int],
    parameters: str,
    return_value: str,
    side_effects: str,
    confidence: str,
    sources: set[str],
    unresolved: list[str],
) -> dict[str, object]:
    return {
        "function_id": key,
        "architecture": architecture,
        "record": record,
        "runtime_address": f"0x{runtime_address:08X}",
        "file_offset": f"0x{file_offset:08X}",
        "size": size,
        "name": name,
        "callers": format_addresses(callers),
        "callees": format_addresses(callees),
        "parameters": parameters,
        "return_value": return_value,
        "side_effects": side_effects,
        "confidence": confidence,
        "sources": "|".join(sorted(sources)),
        "name_evidence": name_evidence,
        "size_evidence": size_evidence,
        "unresolved_reason": "; ".join(unresolved) if unresolved else "NONE",
    }


def build(generated: Path) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    registry: list[dict[str, object]] = []
    effects: list[dict[str, object]] = []

    # Main SPARC: raw candidates are the primary union.
    main_candidate_rows = rows(
        generated / "main_recovered_function_candidates.csv"
    )
    main_candidates = {
        address(row["address"]): row for row in main_candidate_rows
    }
    main_ida = {
        address(row["address"]): row for row in rows(generated / "main_functions.csv")
    }
    main_ghidra = {
        address(row["address"]): row
        for row in rows(generated / "ghidra" / "ghidra_main_sparc_functions.csv")
    }
    main_starts = sorted(set(main_candidates) | set(main_ghidra))
    main_symbols = symbol_map(generated, "main")
    ida_callers, ida_callees = load_graph(generated / "main_ida_callgraph.csv")
    raw_callers: dict[int, set[int]] = defaultdict(set)
    raw_callees: dict[int, set[int]] = defaultdict(set)
    for edge in rows(generated / "main_direct_call_edges.csv"):
        caller, callee = address(edge["structural_caller"]), address(edge["target"])
        raw_callers[callee].add(caller)
        raw_callees[caller].add(callee)
    effect_counts: dict[int, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for ref in rows(generated / "main_absolute_memory_refs.csv"):
        site = address(ref["site"])
        position = bisect.bisect_right(main_starts, site) - 1
        owner = main_starts[position] if position >= 0 else 0
        effect_counts[owner][ref["access"]] += 1
        effects.append(
            {
                "function_id": f"main-sparc:0x{owner:08X}",
                "site": ref["site"],
                "file_offset": ref["file_offset"],
                "target": ref["target"],
                "access": ref["access"],
                "width": ref["width"],
                "assignment_confidence": "nearest-structural-entry",
                "evidence": ref["ida_function"] or "raw-sethi/low-part recovery",
            }
        )

    for start in main_starts:
        candidate = main_candidates.get(start)
        ida, gh = main_ida.get(start), main_ghidra.get(start)
        tool_sizes: dict[str, int] = {}
        if ida:
            tool_sizes["IDA"] = address(ida["size"])
        if gh and gh.get("size"):
            tool_sizes["Ghidra"] = int(gh["size"])
        size, size_evidence = choose_size(tool_sizes)
        if start in main_symbols:
            name, name_evidence = main_symbols[start]
        elif ida and not ida["name"].startswith(("sub_", "loc_")):
            name, name_evidence = ida["name"], "IDA user/entry name"
        else:
            name, name_evidence = "UNRESOLVED", "stripped; no unique debug-token anchor"
        unresolved = []
        if name == "UNRESOLVED":
            unresolved.append("semantic name unavailable")
        if size == "UNRESOLVED":
            unresolved.append(size_evidence)
        parameters = "UNRESOLVED"
        return_value = "UNRESOLVED"
        unresolved.extend(
            [
                "parameter ABI not validated",
                "return semantics not validated",
            ]
        )
        counts = effect_counts.get(start, {})
        side_effects = (
            f"MEMORY_REFS(load={counts.get('load',0)},store={counts.get('store',0)});"
            " see function_memory_effects.csv"
            if counts
            else "NONE_RECOVERED; MMIO/runtime effects may remain unresolved"
        )
        sources = set()
        if candidate:
            sources.add("raw-sparc")
        if ida:
            sources.add("IDA")
        if gh:
            sources.add("Ghidra")
        registry.append(
            registry_row(
                key=f"main-sparc:0x{start:08X}",
                architecture="SPARC-V8-BE32",
                record="5",
                runtime_address=start,
                file_offset=(
                    address(candidate["file_offset"])
                    if candidate
                    else 0x12E000 + start - 0x100000
                ),
                name=name,
                name_evidence=name_evidence,
                size=size,
                size_evidence=size_evidence,
                callers=raw_callers[start] | ida_callers[start],
                callees=raw_callees[start] | ida_callees[start],
                parameters=parameters,
                return_value=return_value,
                side_effects=side_effects,
                confidence=(
                    candidate["confidence"] if candidate else "single-tool-ghidra"
                ),
                sources=sources,
                unresolved=unresolved,
            )
        )

    # Auxiliary/link SPARC is the union of IDA and Ghidra starts.
    aux_ida = {
        address(row["address"]): row for row in rows(generated / "aux_functions.csv")
    }
    aux_gh = {
        address(row["address"]): row
        for row in rows(generated / "ghidra" / "ghidra_link_sparc_functions.csv")
    }
    aux_symbols = symbol_map(generated, "aux")
    aux_ida_callers, aux_ida_callees = load_graph(
        generated / "aux_ida_callgraph.csv"
    )
    for start in sorted(set(aux_ida) | set(aux_gh)):
        ida, gh = aux_ida.get(start), aux_gh.get(start)
        tool_sizes = {}
        if ida:
            tool_sizes["IDA"] = address(ida["size"])
        if gh and gh.get("size"):
            tool_sizes["Ghidra"] = int(gh["size"])
        size, size_evidence = choose_size(tool_sizes)
        if start in aux_symbols:
            name, name_evidence = aux_symbols[start]
        elif ida and not ida["name"].startswith(("sub_", "loc_")):
            name, name_evidence = ida["name"], "IDA user/entry name"
        else:
            name, name_evidence = "UNRESOLVED", "stripped; no unique debug-token anchor"
        callers = set(aux_ida_callers[start])
        callees = set(aux_ida_callees[start])
        unresolved = ["parameter ABI not validated", "return semantics not validated", "side effects not exhaustively assigned"]
        if name == "UNRESOLVED":
            unresolved.append("semantic name unavailable")
        if size == "UNRESOLVED":
            unresolved.append(size_evidence)
        registry.append(
            registry_row(
                key=f"link-sparc:0x{start:08X}",
                architecture="SPARC-V8-BE32",
                record="7",
                runtime_address=start,
                file_offset=0x3196E0 + start - 0xA0060000,
                name=name,
                name_evidence=name_evidence,
                size=size,
                size_evidence=size_evidence,
                callers=callers,
                callees=callees,
                parameters="UNRESOLVED",
                return_value="UNRESOLVED",
                side_effects="UNRESOLVED; link MMIO assignment not yet exhaustive",
                confidence="cross-tool" if ida and gh else "single-tool",
                sources={item for item, present in (("IDA", ida), ("Ghidra", gh)) if present},
                unresolved=unresolved,
            )
        )

    # 8051 records: raw reachable candidates unioned with independently seeded Ghidra.
    raw_8051: dict[int, set[int]] = defaultdict(set)
    for row in rows(generated / "8051_function_candidates.csv"):
        raw_8051[int(row["record_index"])].add(address(row["address"]))
    raw_8051_edges: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for row in rows(generated / "8051_direct_call_edges.csv"):
        if row["target_internal"].lower() != "true":
            continue
        raw_8051_edges[int(row["record_index"])].append(
            (address(row["site"]), address(row["target"]))
        )
    boot_ida = {
        address(row["address"]): row for row in rows(generated / "boot8051_functions.csv")
    }
    gh_names = {0: "boot", 1: "stbc", 2: "updater"}
    payload_offsets = {0: 0x40, 1: 0x8060, 2: 0x17B40}
    for record in (0, 1, 2):
        gh = {
            address(row["address"]): row
            for row in rows(
                generated / "ghidra" / f"ghidra_{gh_names[record]}8051_functions.csv"
            )
        }
        starts = set(raw_8051[record]) | set(gh)
        if record == 0:
            starts |= set(boot_ida)
        ordered_starts = sorted(starts)
        raw_callers: dict[int, set[int]] = defaultdict(set)
        raw_callees: dict[int, set[int]] = defaultdict(set)
        for site, target in raw_8051_edges[record]:
            position = bisect.bisect_right(ordered_starts, site) - 1
            if position < 0:
                continue
            caller = ordered_starts[position]
            raw_callers[target].add(caller)
            raw_callees[caller].add(target)
        for start in ordered_starts:
            ida = boot_ida.get(start) if record == 0 else None
            grow = gh.get(start)
            tool_sizes = {}
            if ida:
                tool_sizes["IDA"] = address(ida["size"])
            if grow and grow.get("size"):
                tool_sizes["Ghidra"] = int(grow["size"])
            size, size_evidence = choose_size(tool_sizes)
            name = (
                ida["name"]
                if ida and not ida["name"].startswith("sub_")
                else "UNRESOLVED"
            )
            callers = set(raw_callers[start])
            callees = set(raw_callees[start])
            unresolved = [
                "parameter ABI not validated",
                "return semantics not validated",
                "XDATA/SFR side effects not exhaustively assigned",
                "caller ownership uses nearest recovered structural entry; computed dispatch remains unresolved",
            ]
            if name == "UNRESOLVED":
                unresolved.append("semantic name unavailable")
            if size == "UNRESOLVED":
                unresolved.append(size_evidence)
            sources = set()
            if start in raw_8051[record]:
                sources.add("raw-8051-CFG")
            if ida:
                sources.add("IDA")
            if grow:
                sources.add("Ghidra")
            registry.append(
                registry_row(
                    key=f"record{record}-8051:0x{start:04X}",
                    architecture="MCS-51/8051",
                    record=str(record),
                    runtime_address=start,
                    file_offset=payload_offsets[record] + start,
                    name=name,
                    name_evidence="IDA vector name" if name != "UNRESOLVED" else "none",
                    size=size,
                    size_evidence=size_evidence,
                    callers=callers,
                    callees=callees,
                    parameters="UNRESOLVED",
                    return_value="UNRESOLVED",
                    side_effects="UNRESOLVED; SFR/XDATA map incomplete",
                    confidence="cross-tool" if len(sources) >= 2 else "single-tool",
                    sources=sources,
                    unresolved=unresolved,
                )
            )

    # Record 3 currently has an independent Ghidra catalog; runtime base remains probable.
    for row in rows(generated / "ghidra" / "ghidra_trap_sparc_functions.csv"):
        start = address(row["address"])
        registry.append(
            registry_row(
                key=f"trap-sparc:0x{start:08X}",
                architecture="SPARC-V8-BE32",
                record="3",
                runtime_address=start,
                file_offset=0x23CE0 + start - 0xA00E0000,
                name="UNRESOLVED",
                name_evidence="stripped; vector role only",
                size="UNRESOLVED",
                size_evidence="Ghidra cross-check retains starts only; boundary not independently stable",
                callers=set(),
                callees=set(),
                parameters="UNRESOLVED",
                return_value="UNRESOLVED",
                side_effects="UNRESOLVED; startup/trap special-register effects expected",
                confidence="single-tool; runtime-base-probable",
                sources={"Ghidra"},
                unresolved=[
                    "semantic name unavailable",
                    "function boundary and size unresolved",
                    "callers/callees unresolved; deterministic Ghidra export retains starts only",
                    "parameter/return ABI not applicable or unresolved for trap entry",
                    "runtime base not observed in loader trace",
                    "side effects not exhaustively assigned",
                ],
            )
        )

    registry.sort(key=lambda row: (int(row["record"]), row["runtime_address"]))
    return registry, effects


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generated_dir", type=Path)
    parser.add_argument("registry_csv", type=Path)
    parser.add_argument("effects_csv", type=Path)
    args = parser.parse_args()
    registry, effects = build(args.generated_dir)
    write(args.registry_csv, registry)
    write(args.effects_csv, effects)
    print(f"registry={len(registry)} effects={len(effects)}")


if __name__ == "__main__":
    main()
