# Coverage, confidence, and unresolved boundaries

## What “full firmware analysis” means here

The package has been inventoried end-to-end: every byte belongs to one of ten
validated records, and every record has an architecture/role classification
or an explicitly bounded unknown. “Full” does not mean reconstructed source
code for every stripped function. It means there is no silently ignored
package region and claims are tied to evidence and confidence.

## Coverage ledger

| Region | Structural coverage | Semantic coverage | Status |
|---|---|---|---|
| Global/record headers | complete parser and checksum validation | format understood | Confirmed |
| Record 0, 8051 boot | 2,175 reachable instructions; 34 CFG entries; 2 computed-jump boundaries | flash/partition/startup mapped | High |
| Record 1, STBC | 18,367 reachable instructions; 226 CFG entries; 17 computed-jump boundaries | power/key/CC/CEC/mailbox roles mapped | High |
| Record 2, update 8051 | 3,718 reachable instructions; 63 CFG entries; 3 computed-jump boundaries | USB/filesystem/ISP role mapped | High |
| Record 3, SPARC vector | entire payload disassembled as SPARC | vector/boot role mapped | Runtime base probable |
| Record 4, config | entire payload inspected; 17-entry trap schema validated | main trap/runtime/USB-data config mapped | ABI partly unknown |
| Records 5+6, main app | full IDA plus raw structural scan | 3,074 IDA functions; 3,602 entry candidates; 411 embedded-name candidates; major subsystems mapped | High |
| Record 7, link image | full IDA segment | 565 functions, 22 EQ/link anchors | High |
| Record 8, aux config | entire payload inspected; homologous 17-entry trap schema validated | link trap/runtime/config role mapped | ABI partly unknown |
| Record 9, footer | every pair decoded | absent targets/padding noted | Confirmed |

## Main-function classification

Direct string-xref anchors classify at least:

| Category | Directly anchored functions |
|---|---:|
| boot/update | 76 |
| factory/service | 57 |
| OSD/UI | 120 |
| input/keys | 14 |
| persistent data | 47 |
| video/link/source | 92 |
| picture/PQ | 59 |
| scaler/panel | 118 |
| audio | 20 |
| USB/PD | 25 |
| DDC/CI | 13 |
| power | 33 |
| events/tasks | 44 |
| diagnostics | 33 |

Categories overlap. Another 788 previously unanchored IDA containers received
one lower-confidence graph label by a conservative neighbor-voting rule.
The old count of 1,928 unclassified IDA functions is retained as a **semantic**
metric, not a structural gap. Raw recovery found 528 additional callable-entry
candidates and demonstrated that IDA sometimes merges several independently
called entries into one container. The generated catalogs now preserve all
3,602 candidate entries, 387 indirect transfers, 8,022 absolute references,
27 static callback bindings, and 411 function-like embedded-name candidates.
Unknown arithmetic/register helpers remain honestly unnamed.

For the auxiliary image, 259 of 565 functions have a direct or conservative
graph-inferred category; 306 remain unclassified.

## Confidence vocabulary

- **Confirmed:** exact bytes/address plus direct code/data behavior or
  reproducible emulator/hardware result.
- **High:** multiple independent static indicators with no contradiction.
- **Probable:** best explanation of the data, but loader/runtime or hardware
  observation is missing.
- **Unresolved:** evidence is insufficient to choose safely.
- **Do not enable:** a missing/unsafe backend was demonstrated, or safe
  hardware support could not be established.

## Important negative findings

- MGA kind conversion writes the wrong persistent selectors and truncates
  values; do not enable writes.
- A reusable Local Dimming engine is compiled into the common scaler library,
  but the G55C path selects global PWM and no matching panel-zone hardware or
  reachable model integration was verified; do not expose it as zone dimming.
- PIP/PBP and Type-C/USB-hub code are genuine common-platform surfaces, not
  proof that this board exposes the required input pipelines or controllers.
- Raw 3D-LUT/hue/saturation/brightness/gamma/overdrive hooks are calibration
  primitives, not safe missing consumer settings.
- TCON/FPGA/PDIC/Panel Timing labels do not form working actions in this
  build.
- DP/HDMI EQ is real but automatic; data tables are training candidates, not
  manual settings.
- Factory Picture is real but shares a state field with the normal OSD;
  enabling it broke normal Game/Picture category visibility.
- Low Input Lag and FreeSync predicates are runtime safety/capability checks,
  not fixed SKU locks.

## Remaining hard boundaries

The following cannot be resolved from this package alone:

1. exact runtime loader/relocation ABI for records 3, 4, and 8, beyond the
   validated homologous exception-table contract;
2. contents of footer-described but absent flash targets `0x30000` and
   `0xB0000`;
3. indirect-call targets populated only in runtime RAM or vendor ROM;
4. electrical panel/backlight topology beyond what firmware selects;
5. exact reason for the observed one-hour 1% update display without UART/USB
   traces;
6. whether another G55C hardware revision uses different panel, TCON, or
   scaler companion parts;
7. exact source-level intent and types of every stripped leaf helper.

These are not reasons to guess. Resolving them would require at least one of:

- non-destructive SPI flash dump;
- UART trace during boot/update;
- board and panel part-number inspection;
- logic-analyzer capture of TCON/backlight buses;
- runtime memory snapshot;
- another verified firmware revision for differential analysis.

## Reproduction and audit artifacts

Public artifacts do not include Samsung firmware, extracted payloads, IDBs, or
private hardware dumps. They do include:

- deterministic MGA-only builder/verifier;
- read-only container inventory tool;
- exact hashes and address mappings;
- raw representative disassembly;
- generated function and symbol-anchor catalogs;
- independent SPARC/8051 control-flow, memory-reference, and callback catalogs;
- emulator observations with inputs/results;
- hardware incident and final-state notes.

This boundary keeps the repository legally and technically reproducible
without redistributing proprietary firmware.
