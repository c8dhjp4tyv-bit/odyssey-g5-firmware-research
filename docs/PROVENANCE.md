# Analysis and AI provenance

## Authorship boundary

Codex generated the analysis scripts, derived catalogs, documentation prose,
and most static interpretations in this repository. The owner supplied the
firmware and operated the physical monitor. No claim in this repository has
received an independent human reverse-engineering review unless explicitly
marked otherwise.

## Evidence classes

| Label | Meaning |
|---|---|
| `STATIC_IDA` | IDA disassembly/xref/function evidence |
| `STATIC_RAW` | independent instruction/byte scanner |
| `STATIC_GHIDRA` | Ghidra headless second-tool result |
| `EMULATOR` | purpose-built SPARC interpreter with controlled state/stubs |
| `HARDWARE` | owner-observed behavior on `LS32CG552EUXUF` |
| `UNRESOLVED` | required evidence is absent; no guess substituted |

Generated registries retain tool sources and confidence per row. Narrative
claims include addresses/disassembly or link to the generated evidence.

## Hardware-confirmed observations

- Long joystick-UP opened the MGA factory screen.
- Enabling only MGA `supported` displayed all 35 existing rows.
- MGA rows remained read-only.
- Enabling the shared Factory Picture condition removed normal Game/Picture
  categories; restoring it restored those categories.
- Grey normal settings with no source became usable after a computer/input was
  connected.
- One update remained at 1% for about an hour and then rebooted normally.
- The final two-byte MGA-only image booted and showed version `1014.0`.

These observations are not independent laboratory reproduction.

## Emulator-only conclusions

- Forced MGA kind 4 writes unrelated general configuration selectors and
  truncates the declared 10-bit range.
- EQ PreAEQ tables provide scan candidates; RunAEQ runtime results replace
  those candidates.
- Selected gate/renderer paths behaved as documented with controlled stubs.

The execution emulator is not yet public, so these results are not currently
independently reproducible from this repository alone. They are labeled
accordingly and are not used to justify additional released patches.

## Second-tool status

Ghidra independently analyzed six executable regions. Address-level agreement
is recorded in
[`function_tool_crosscheck.json`](generated/function_tool_crosscheck.json);
Ghidra-only and IDA/raw-only starts remain separate registry entries with
single-tool confidence. Only stable function entry addresses are retained:
Ghidra body sizes, generated switch labels, and call edges varied at a few
ambiguous sites between clean runs. The reduced catalogs were byte-identical
across two repetitions. This is independent software-tool corroboration, not
independent human review.

## Physical evidence still required

- UART boot/update log;
- runtime RAM snapshot for populated callback slots;
- non-destructive complete SPI flash dump for absent footer regions;
- board/panel part numbers and traced nets;
- I²C/SPI/GPIO/PWM logic-analyzer captures.

Until supplied, affected fields remain `UNRESOLVED`.
