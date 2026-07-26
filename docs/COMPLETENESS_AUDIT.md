# Strict completeness audit

This audit uses the strict acceptance criteria introduced after the first
package-wide release. “Complete” here means every item is either evidenced or
explicitly unresolved; it does not mean that missing physical evidence was
fabricated.

| Requirement | Artifact/result | Status |
|---|---|---|
| Every byte classified | 66 gap-free ranges covering exactly `0x34A3A0` bytes in `byte_classification.csv` | Complete as classification; six executable payload ranges explicitly remain mixed code/data |
| Every recovered function/entry recorded | 4,740-entry union in `function_registry.csv` | Complete for IDA/raw/Ghidra recovered starts |
| No blank/unclassified function | every registry field populated; missing semantics say `UNRESOLVED` with reason | Complete as evidence accounting |
| Address and size | address/file offset on every row; analyzer disagreement retained | Complete; disputed/missing boundaries explicitly unresolved |
| Callers/callees | raw direct edges and IDA graphs merged; Ghidra contributes stable starts only | Complete for recovered static edges; computed/runtime targets unresolved |
| Parameters/return/side effects | explicit fields plus 8,022 assigned memory effects | Incomplete semantically; stripped ABI and non-main effects often unresolved |
| Every indirect transfer classified | 409 sites: 256 SPARC computed dispatches, 131 indirect calls, 22 8051 computed jumps | Complete as site accounting; runtime targets remain unresolved |
| Data structures | `data_structure_catalog.csv` and IDA C types | Partial; known layouts explicit, unknown fields named |
| Hardware map | 1,258 absolute targets plus interface ledger | Partial; GPIO/I²C/SPI register bits and board nets need physical/vendor evidence |
| State machines | seven evidenced high-level diagrams | Partial at low level; live interrupt/timer/mailbox edges unresolved |
| Evidence per claim | addresses/instructions/xrefs and generated source columns | High for published conclusions; not every stripped helper has semantics |
| Dynamic validation | emulator/hardware matrix | Partial; no UART, runtime dump, or logic analyzer capture |
| Reproducible IDA analysis | loader, types, symbols, exporter, MCP ledger | Partial; loader source included but local CLI smoke test was blocked by IDA license/Python configuration |
| Second-tool cross-check | Ghidra headless on six executable regions | Complete for function starts; two clean runs produced byte-identical catalogs |
| AI provenance | `PROVENANCE.md` and dynamic matrix | Complete |

## Quantitative cross-tool union

| Region | Tools | Union |
|---|---|---:|
| Main SPARC | IDA 3,074; Ghidra 3,514; raw 3,602 | 3,625 |
| Link SPARC | IDA 565; Ghidra 590 | 597 |
| Boot 8051 | IDA 46; Ghidra 34; raw 34 | 53 |
| STBC 8051 | Ghidra 289; raw 226 | 316 |
| Updater 8051 | Ghidra 65; raw 63 | 80 |
| Trap SPARC | Ghidra | 69 |

Total unique registry entries: **4,740**.

## Ghidra determinism boundary

A first exporter included Ghidra-created function sizes, names, and call edges.
Clean-project repetitions changed a small number of those fields around
ambiguous stripped switch code even though all six function-start sets and
counts stayed identical. The release exporter therefore retains only entry
addresses. Two clean headless runs of that reduced catalog were compared with
`diff -qr` and were byte-identical. Size and call-graph evidence comes from the
raw scanners and IDA exports; Ghidra-only boundaries are explicitly
`UNRESOLVED`.

## External blockers

The remaining partial items cannot be converted to confirmed results from the
firmware package alone. They require the captures listed in
[DYNAMIC_VALIDATION.md](DYNAMIC_VALIDATION.md). Until those are supplied, the
repository must not claim “every function understood” or “all hardware
registers decoded.”
