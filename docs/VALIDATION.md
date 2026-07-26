# Validation and reproducibility

## Validation record

```text
Validated on:             2026-07-26
Tested hardware:          LS32CG552EUXUF
Repository state:          release branch; see current commit/tag
```

## Build invariants

The builder refuses to run unless the exact pinned base image has:

- exact size `3,449,760`
- exact SHA-256
  `2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7`
- exact complete-file `sum16 = D43B`
- embedded version `1010.0` at the expected offset
- base MGA support byte `00`
- base shared Factory Picture byte `00`

## Final-image invariants

The verifier requires:

- exact two-byte diff at `0x273367` and `0x2D2776`
- embedded version `1014.0`
- MGA support byte `01`
- Factory Picture/shared normal-OSD byte `00`
- unchanged key dispatch cell at `0x2354BC`
- unchanged data checksum placeholder at `0x21DCE8..0x21DCEB`
- final complete-file `sum16 = D440`
- final SHA-256
  `815f28e8e1eaba498c07cd500d581c63b16a887ea0da274152d1297b8d237350`

## Dynamic checks performed during research

A purpose-built SPARC V8 emulator exercised:

- big-endian memory access
- `SETHI`, `CALL`, and delay-slot behavior
- `SAVE` and register windows
- switch/jump-table paths
- the factory category renderer
- controlled descriptor write paths
- model-gate branch behavior with stubbed dependencies
- MGA kind-2/3-to-kind-4 mutations with a sentinel resolver target
- the separate EQ partition's PreAEQ candidate selection
- RunAEQ replacement of candidates with controlled runtime RCT/CFT values

For the final MGA category:

```text
base renderer:    "Not supported", 0 item-value calls
patched renderer: 35 names, first "Back to upper", last "MGA On/Off"
```

The in-memory-only MGA safety probe produced:

```text
base kind 2/3: no resolver and no persistent write
forced kind 4: selector-based byte write and persistence
forced kind 4 at 0xFF with max 0x2FE: stored 0x00
MGA_KIND4_SAFETY=UNSAFE_CONFIRMED
```

The EQ-partition probe produced:

```text
PREAEQ_INDEX_STORAGE=RUNTIME_RAM
PREAEQ_TABLE_SELECTION=FLASH_CANDIDATE_TABLE_CONFIRMED
RUNAEQ_RUNTIME_RESULT_OVERRIDES_PREAEQ=CONFIRMED
```

## Public safety-guard regression

The public builder and verifier use explicit runtime guards rather than
optimization-removable `assert` statements. These commands pass:

```bash
python3 -m unittest discover -s tests -v
python3 -O -m unittest discover -s tests -v
```

The negative fixtures confirm that the mutating tools reject malformed
firmware under `python3 -O`; the inventory fixtures validate structural
failure handling. A positive optimized-mode run against the private, hash-matched
base image reproduced:

```text
output sha256=815f28e8e1eaba498c07cd500d581c63b16a887ea0da274152d1297b8d237350
sum16=0xD440
diffs=0x273367,0x2D2776
verification=PASS
```

The current public suite contains 17 tests in each mode. It additionally
checks the complete 8051 opcode-length table, direct-call recovery, SPARC
`SAVE`/return/indirect-call decoding, cross-register delay-slot address
recovery, callback slots, embedded-symbol mapping, and the companion-record
exception schema.

All generated structural artifacts were regenerated from the pinned private
image and exported IDA metadata, then byte-compared with
`docs/generated/*`:

```text
SPARC catalogs:       byte-identical
8051 catalogs:        byte-identical
embedded-name CSVs:   byte-identical
REPRODUCIBLE_OUTPUTS_PASS
```

## Hardware observations

- MGA page opened through the existing long-UP gesture.
- All 35 rows rendered.
- Rows were not editable, matching descriptor analysis.
- Enabling Factory Picture removed normal Game/Picture categories.
- Restoring the shared byte restored the normal categories.
- Grey normal settings were reproduced with no computer/source connected and
  became usable when the source was connected.

## Confidence vocabulary

- **CONFIRMED:** supported by exact static evidence and/or hardware observation.
- **HIGH:** multiple independent static signals, but not fully observed on
  hardware.
- **LIKELY:** best explanation with incomplete state capture.
- **UNRESOLVED:** insufficient evidence; no release action may depend on it.
