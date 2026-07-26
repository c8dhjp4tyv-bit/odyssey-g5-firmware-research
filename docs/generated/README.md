# Generated analysis catalogs

These CSV files are derived metadata. They contain no Samsung firmware bytes.

| File | Rows | Meaning |
|---|---:|---|
| `byte_classification.csv` | 66 | Gap-free classification covering every package byte |
| `function_registry.csv` | 4,740 | Cross-tool union with ABI/effect/confidence/unresolved fields |
| `function_memory_effects.csv` | 8,022 | Absolute memory effects assigned to structural main entries |
| `function_tool_crosscheck.json` | 6 regions | IDA/raw/Ghidra address-level agreement |
| `main_functions.csv` | 3,074 | IDA-discovered functions in the main SPARC image |
| `main_symbol_anchors.csv` | 250 | Function-name inferences backed by debug-string xrefs |
| `main_embedded_symbol_candidates.csv` | 411 | Function-like names recovered from embedded diagnostic text; 288 containing functions |
| `main_recovered_function_candidates.csv` | 3,602 | Union of IDA starts, direct-call targets, and `SAVE` prologues |
| `main_indirect_control_flow.csv` | 387 | 131 indirect calls and 256 computed jumps |
| `main_absolute_memory_refs.csv` | 8,022 | Resolved `SETHI`/low-part RAM or MMIO references |
| `main_callback_bindings.csv` | 27 | Static callback-slot registrations |
| `main_direct_call_edges.csv` | 20,645 | Raw SPARC direct calls: 19,828 internal and 817 external/runtime |
| `main_ida_callgraph.csv` | 8,677 | IDA main direct caller/callee edges |
| `main_structure_summary.json` | 1 | Counts, mapping, and exact image hash for the structural scan |
| `aux_functions.csv` | 565 | IDA-discovered functions in the separate link/EQ SPARC image |
| `aux_symbol_anchors.csv` | 22 | Named HDMI/DP functions backed by string xrefs |
| `aux_embedded_symbol_candidates.csv` | 37 | Additional names embedded in link-image diagnostic strings |
| `aux_ida_callgraph.csv` | 1,358 | IDA link-image direct caller/callee edges |
| `boot8051_functions.csv` | 46 | Conservatively defined functions in the 8051 boot partition |
| `8051_function_candidates.csv` | 323 | Reachable call/vector entry candidates across records 0–2 |
| `8051_direct_call_edges.csv` | 975 | Reachable `LCALL`/`ACALL` sites and targets; caller ownership is structural |
| `8051_computed_jumps.csv` | 22 | Exact `JMP @A+DPTR` analysis boundaries |
| `8051_structure_summary.json` | 1 | Per-record reachable CFG statistics |
| `indirect_control_flow_detailed.csv` | 409 | Every recovered indirect transfer classified by dispatch mechanism |
| `data_structure_catalog.csv` | 20 | Struct/enum/table/state/message/persistent-layout ledger |
| `hardware_absolute_accesses.csv` | 1,258 | Aggregated absolute RAM/probable-MMIO targets |
| `hardware_interfaces.csv` | 14 | Interface-level GPIO/bus/panel evidence and unresolved fields |
| `dynamic_validation_matrix.csv` | 16 | Static/emulator/hardware/capture provenance per major claim |

The `ghidra/` subdirectory contains independent second-tool function-start
catalogs for boot, STBC, updater, trap, main, and link executable regions.
Counts are 34, 289, 65, 69, 3,514, and 590 respectively. They intentionally
contain only addresses: boundaries, auto-generated names, and call edges were
not stable at a few ambiguous sites between clean Ghidra projects.

`direct_categories` are keyword classifications from strings referenced
inside the function. `graph_inferred_categories` are lower-confidence labels
propagated from at least two neighboring labeled functions when one category
held at least 60% of the votes. An empty graph label means no inference was
made. These labels are navigation aids, not recovered source-level types.

IDA can merge function tails or miss indirect calls in stripped SPARC code.
The structural scanner demonstrates both cases and preserves confidence and
container information. The address and byte bounds are useful, but counts are
analysis observations rather than recovered source ground truth.

`UNRESOLVED` is a classification, not a blank. It identifies the exact field
whose evidence is unavailable and why it cannot safely be inferred.
