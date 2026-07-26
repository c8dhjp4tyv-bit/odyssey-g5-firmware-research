#!/usr/bin/env python3
"""Recover SPARC V8 function-entry and indirect-control-flow candidates.

IDA can merge adjacent SPARC leaf functions or switch-table targets when a
stripped image has no symbols. This read-only companion scan decodes the
control-transfer and SAVE instructions directly from an owner-supplied image,
then compares them with an exported IDA functions.json inventory.

The output is evidence, not an instruction-perfect disassembler. High and
medium candidates are useful review targets; low candidates require manual
confirmation because executable records may contain inline data.
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

MAIN_FILE_OFFSET = 0x12E000
MAIN_VA = 0x100000
MAIN_LENGTH = 0xEFCE0
EXPECTED_IMAGE_SIZE = 3_449_760
EXPECTED_IMAGE_SHA256 = (
    "2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7"
)


@dataclass(frozen=True)
class Candidate:
    address: int
    file_offset: int
    ida_defined: bool
    direct_call_count: int
    save_prologue: bool
    follows_return_delay_slot: bool
    ida_container: str
    confidence: str
    reasons: str


@dataclass(frozen=True)
class IndirectSite:
    address: int
    file_offset: int
    rd: int
    rs1: int
    immediate: bool
    displacement: int
    kind: str
    target_source: str
    ida_function: str


@dataclass(frozen=True)
class MemoryReference:
    site: int
    file_offset: int
    target: int
    access: str
    width: int
    data_register: int
    ida_function: str


@dataclass(frozen=True)
class CallbackBinding:
    slot: int
    setter: int
    registration_site: int
    callback: int
    callback_file_offset: int
    callback_is_candidate_start: bool


@dataclass(frozen=True)
class DirectCallEdge:
    site: int
    file_offset: int
    target: int
    target_scope: str
    ida_caller: str
    structural_caller: int
    caller_confidence: str


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def signed(value: int, bits: int) -> int:
    sign_bit = 1 << (bits - 1)
    return value - (1 << bits) if value & sign_bit else value


def fields(word: int) -> dict[str, int]:
    return {
        "op": word >> 30,
        "rd": (word >> 25) & 0x1F,
        "op2": (word >> 22) & 0x7,
        "op3": (word >> 19) & 0x3F,
        "rs1": (word >> 14) & 0x1F,
        "i": (word >> 13) & 1,
        "simm13": signed(word & 0x1FFF, 13),
    }


def is_save_prologue(word: int) -> bool:
    item = fields(word)
    return (
        item["op"] == 2
        and item["op3"] == 0x3C
        and item["rd"] == 14
        and item["rs1"] == 14
        and item["i"] == 1
        and item["simm13"] < 0
    )


def is_return(word: int) -> bool:
    item = fields(word)
    return (
        item["op"] == 2
        and item["op3"] == 0x38
        and item["rd"] == 0
        and item["i"] == 1
        and item["simm13"] == 8
        and item["rs1"] in (15, 31)
    )


def resolve_indirect_source(words: list[int], index: int, register: int) -> str:
    """Describe the closest load that populated an indirect target register."""
    lower = max(0, index - 16)
    load_index = None
    load = None
    for previous in range(index - 1, lower - 1, -1):
        item = fields(words[previous])
        # LD word: op=3, op3=0. Its rd field is the destination.
        if item["op"] == 3 and item["op3"] == 0 and item["rd"] == register:
            load_index = previous
            load = item
            break
        # A nearer arithmetic write makes an older load irrelevant.
        if item["op"] in (2, 3) and item["rd"] == register:
            break
        if item["op"] == 0 and item["op2"] == 4 and item["rd"] == register:
            break
    if load_index is None or load is None:
        return f"%r{register}"

    displacement = load["simm13"] if load["i"] else 0
    base_register = load["rs1"]
    base_value = None
    for previous in range(load_index - 1, max(-1, load_index - 16), -1):
        item = fields(words[previous])
        if item["op"] == 0 and item["op2"] == 4 and item["rd"] == base_register:
            base_value = (words[previous] & 0x3FFFFF) << 10
            break
    if base_value is not None and load["i"]:
        slot = (base_value + displacement) & 0xFFFFFFFF
        return f"mem[0x{slot:08X}]"
    suffix = f"{displacement:+#x}" if load["i"] and displacement else ""
    return f"mem[%r{base_register}{suffix}]"


def resolve_register_constant(
    words: list[int],
    before_index: int,
    register: int,
    depth: int = 0,
    visited: frozenset[tuple[int, int]] = frozenset(),
) -> int | None:
    """Recover a nearby SETHI plus optional OR/ADD-immediate address."""
    if depth > 6 or (before_index, register) in visited:
        return None
    visited = visited | {(before_index, register)}
    for previous in range(before_index - 1, max(-1, before_index - 16), -1):
        item = fields(words[previous])
        if item["op"] == 0 and item["op2"] == 4 and item["rd"] == register:
            return ((words[previous] & 0x3FFFFF) << 10) & 0xFFFFFFFF
        if item["op"] == 2 and item["rd"] == register:
            if item["op3"] in (0x00, 0x02):
                if item["i"]:
                    base = resolve_register_constant(
                        words,
                        previous,
                        item["rs1"],
                        depth + 1,
                        visited,
                    )
                    if base is None:
                        return None
                    if item["op3"] == 0x02:
                        return (base | (item["simm13"] & 0x1FFF)) & 0xFFFFFFFF
                    return (base + item["simm13"]) & 0xFFFFFFFF
                rs2 = words[previous] & 0x1F
                source = rs2 if item["rs1"] == 0 else item["rs1"] if rs2 == 0 else None
                if source is not None:
                    return resolve_register_constant(
                        words, previous, source, depth + 1, visited
                    )
            return None
        if item["op"] == 3 and item["rd"] == register and item["op3"] <= 0x0B:
            return None
    return None


def load_ida_functions(path: Path) -> list[dict[str, object]]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return sorted(rows, key=lambda row: int(row["address"]))


def scan(
    image: bytes, ida_functions: list[dict[str, object]]
) -> tuple[
    list[Candidate],
    list[IndirectSite],
    list[MemoryReference],
    list[CallbackBinding],
    list[DirectCallEdge],
    dict[str, int],
]:
    code = image[MAIN_FILE_OFFSET : MAIN_FILE_OFFSET + MAIN_LENGTH]
    require(len(code) == MAIN_LENGTH, "main SPARC region is truncated")

    words = [
        int.from_bytes(code[offset : offset + 4], "big")
        for offset in range(0, len(code) - 3, 4)
    ]
    direct_calls: dict[int, int] = {}
    direct_call_sites: dict[int, list[int]] = {}
    all_direct_call_sites: list[tuple[int, int]] = []
    save_starts: set[int] = set()
    indirect_sites: list[IndirectSite] = []
    memory_references: list[MemoryReference] = []
    ida_starts = {int(row["address"]) for row in ida_functions}

    def ida_function_at(address: int) -> dict[str, object] | None:
        low = 0
        high = len(ida_functions) - 1
        while low <= high:
            middle = (low + high) // 2
            row = ida_functions[middle]
            start = int(row["address"])
            end = int(row["end"])
            if address < start:
                high = middle - 1
            elif address >= end:
                low = middle + 1
            else:
                return row
        return None

    for index, word in enumerate(words):
        address = MAIN_VA + index * 4
        item = fields(word)
        if item["op"] == 1:
            displacement = signed(word & 0x3FFFFFFF, 30) << 2
            target = (address + displacement) & 0xFFFFFFFF
            all_direct_call_sites.append((address, target))
            if MAIN_VA <= target < MAIN_VA + MAIN_LENGTH and target % 4 == 0:
                direct_calls[target] = direct_calls.get(target, 0) + 1
                direct_call_sites.setdefault(target, []).append(address)
        if is_save_prologue(word):
            save_starts.add(address)
        if item["op"] == 2 and item["op3"] == 0x38:
            if is_return(word):
                continue
            kind = "indirect-call" if item["rd"] == 15 else "computed-jump"
            container = ida_function_at(address)
            indirect_sites.append(
                IndirectSite(
                    address=address,
                    file_offset=address - MAIN_VA + MAIN_FILE_OFFSET,
                    rd=item["rd"],
                    rs1=item["rs1"],
                    immediate=bool(item["i"]),
                    displacement=item["simm13"] if item["i"] else 0,
                    kind=kind,
                    target_source=resolve_indirect_source(
                        words, index, item["rs1"]
                    ),
                    ida_function=(
                        f"0x{int(container['address']):08X}:{container['name']}"
                        if container
                        else ""
                    ),
                )
            )
        memory_operations = {
            0x00: ("load", 4),
            0x01: ("load", 1),
            0x02: ("load", 2),
            0x03: ("load", 8),
            0x04: ("store", 4),
            0x05: ("store", 1),
            0x06: ("store", 2),
            0x07: ("store", 8),
            0x09: ("load", 1),
            0x0A: ("load", 2),
        }
        if item["op"] == 3 and item["i"] and item["op3"] in memory_operations:
            base_value = resolve_register_constant(words, index, item["rs1"])
            if base_value is not None:
                target = (base_value + item["simm13"]) & 0xFFFFFFFF
                if target >= 0x80000000:
                    container = ida_function_at(address)
                    access, width = memory_operations[item["op3"]]
                    memory_references.append(
                        MemoryReference(
                            site=address,
                            file_offset=address - MAIN_VA + MAIN_FILE_OFFSET,
                            target=target,
                            access=access,
                            width=width,
                            data_register=item["rd"],
                            ida_function=(
                                f"0x{int(container['address']):08X}:{container['name']}"
                                if container
                                else ""
                            ),
                        )
                    )

    all_starts = ida_starts | set(direct_calls) | save_starts
    candidates: list[Candidate] = []
    for address in sorted(all_starts):
        ida_defined = address in ida_starts
        call_count = direct_calls.get(address, 0)
        save = address in save_starts
        index = (address - MAIN_VA) // 4
        follows_return = index >= 2 and is_return(words[index - 2])
        container = ida_function_at(address)
        reasons = []
        if ida_defined:
            reasons.append("ida")
        if call_count:
            reasons.append(f"direct-call-x{call_count}")
        if save:
            reasons.append("save-prologue")
        if follows_return:
            reasons.append("after-return-delay-slot")

        if ida_defined:
            confidence = "ida-defined"
        elif call_count >= 3 or (save and call_count >= 1):
            confidence = "high"
        elif call_count >= 2 or (save and follows_return):
            confidence = "medium"
        else:
            confidence = "low"
        candidates.append(
            Candidate(
                address=address,
                file_offset=address - MAIN_VA + MAIN_FILE_OFFSET,
                ida_defined=ida_defined,
                direct_call_count=call_count,
                save_prologue=save,
                follows_return_delay_slot=follows_return,
                ida_container=(
                    f"0x{int(container['address']):08X}:{container['name']}"
                    if container and int(container["address"]) != address
                    else ""
                ),
                confidence=confidence,
                reasons="|".join(reasons),
            )
        )

    summary = {
        "ida_defined_starts": len(ida_starts),
        "internal_direct_call_targets": len(direct_calls),
        "save_prologues": len(save_starts),
        "recovered_start_union": len(all_starts),
        "new_start_candidates": len(all_starts - ida_starts),
        "new_high": sum(
            row.confidence == "high" and not row.ida_defined for row in candidates
        ),
        "new_medium": sum(
            row.confidence == "medium" and not row.ida_defined for row in candidates
        ),
        "new_low": sum(
            row.confidence == "low" and not row.ida_defined for row in candidates
        ),
        "indirect_calls": sum(row.kind == "indirect-call" for row in indirect_sites),
        "computed_jumps": sum(row.kind == "computed-jump" for row in indirect_sites),
        "absolute_memory_references": len(memory_references),
        "absolute_memory_targets": len({row.target for row in memory_references}),
    }

    candidate_addresses = sorted(row.address for row in candidates)
    callback_bindings: list[CallbackBinding] = []
    seen_bindings: set[tuple[int, int, int]] = set()
    for reference in memory_references:
        if reference.access != "store" or reference.data_register != 8:
            continue
        position = bisect.bisect_right(candidate_addresses, reference.site) - 1
        if position < 0:
            continue
        setter = candidate_addresses[position]
        if reference.site - setter > 0x20 or setter not in direct_call_sites:
            continue
        for registration_site in direct_call_sites[setter]:
            call_index = (registration_site - MAIN_VA) // 4
            callback = resolve_register_constant(words, call_index + 2, 8)
            if callback is None or not (
                MAIN_VA <= callback < MAIN_VA + MAIN_LENGTH
            ):
                continue
            key = (reference.target, registration_site, callback)
            if key in seen_bindings:
                continue
            seen_bindings.add(key)
            callback_bindings.append(
                CallbackBinding(
                    slot=reference.target,
                    setter=setter,
                    registration_site=registration_site,
                    callback=callback,
                    callback_file_offset=callback - MAIN_VA + MAIN_FILE_OFFSET,
                    callback_is_candidate_start=callback in candidate_addresses,
                )
            )
    callback_bindings.sort(
        key=lambda row: (row.slot, row.registration_site, row.callback)
    )
    direct_call_edges: list[DirectCallEdge] = []
    for site, target in all_direct_call_sites:
        container = ida_function_at(site)
        position = bisect.bisect_right(candidate_addresses, site) - 1
        structural_caller = candidate_addresses[position] if position >= 0 else 0
        direct_call_edges.append(
            DirectCallEdge(
                site=site,
                file_offset=site - MAIN_VA + MAIN_FILE_OFFSET,
                target=target,
                target_scope=(
                    "main-internal"
                    if MAIN_VA <= target < MAIN_VA + MAIN_LENGTH
                    else "external-or-runtime"
                ),
                ida_caller=(
                    f"0x{int(container['address']):08X}:{container['name']}"
                    if container
                    else ""
                ),
                structural_caller=structural_caller,
                caller_confidence=(
                    "ida-container" if container else "nearest-candidate"
                ),
            )
        )
    direct_call_edges.sort(key=lambda row: (row.site, row.target))
    summary["static_callback_bindings"] = len(callback_bindings)
    summary["static_callback_slots"] = len({row.slot for row in callback_bindings})
    summary["direct_call_edges"] = len(direct_call_edges)
    summary["internal_direct_call_edges"] = sum(
        row.target_scope == "main-internal" for row in direct_call_edges
    )
    summary["external_direct_call_edges"] = sum(
        row.target_scope == "external-or-runtime" for row in direct_call_edges
    )
    return (
        candidates,
        indirect_sites,
        memory_references,
        callback_bindings,
        direct_call_edges,
        summary,
    )


def write_csv(path: Path, rows: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dictionaries = [asdict(row) for row in rows]
    require(bool(dictionaries), f"no rows for {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(dictionaries[0]), lineterminator="\n"
        )
        writer.writeheader()
        for row in dictionaries:
            for key in (
                "address",
                "site",
                "file_offset",
                "target",
                "slot",
                "setter",
                "registration_site",
                "callback",
                "callback_file_offset",
                "structural_caller",
            ):
                if key in row:
                    row[key] = f"0x{row[key]:08X}"
            writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("ida_functions_json", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--allow-unpinned",
        action="store_true",
        help="analyze another same-layout image without the D43B hash guard",
    )
    args = parser.parse_args()

    image = args.image.read_bytes()
    require(len(image) == EXPECTED_IMAGE_SIZE, "unexpected firmware size")
    digest = hashlib.sha256(image).hexdigest()
    if not args.allow_unpinned:
        require(digest == EXPECTED_IMAGE_SHA256, "base firmware SHA-256 mismatch")

    ida_functions = load_ida_functions(args.ida_functions_json)
    (
        candidates,
        indirect_sites,
        memory_references,
        callback_bindings,
        direct_call_edges,
        summary,
    ) = scan(image, ida_functions)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    write_csv(args.output_dir / "function_candidates.csv", candidates)
    write_csv(args.output_dir / "indirect_sites.csv", indirect_sites)
    write_csv(args.output_dir / "absolute_memory_refs.csv", memory_references)
    write_csv(args.output_dir / "callback_bindings.csv", callback_bindings)
    write_csv(args.output_dir / "direct_call_edges.csv", direct_call_edges)
    (args.output_dir / "summary.json").write_text(
        json.dumps(
            {
                "image_sha256": digest,
                "mapping": {
                    "file_offset": MAIN_FILE_OFFSET,
                    "virtual_address": MAIN_VA,
                    "length": MAIN_LENGTH,
                },
                **summary,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
