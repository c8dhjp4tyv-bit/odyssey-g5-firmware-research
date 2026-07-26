# Tooling

## IDA Pro

The SPARC application was imported as big-endian SPARC V8 with two mapped
segments:

```text
LOAD  file 0x12E000, VA 0x100000, length 0xEFCE0
DATA  file 0x21DD00, VA 0x1F0000, length 0xFB9C0
```

Cross-references to absolute data commonly need recognition of the
`SETHI %hi(X)` plus `OR %lo(X)` pair.

IDA databases are not distributed because they contain proprietary firmware
content.

## SPARC V8 analysis emulator

The research harness is a small dependency-free interpreter, not a
cycle-accurate hardware emulator. It models the instruction and state needed
for selected functions:

- big-endian loads/stores
- SPARC register windows and `SAVE`/`RESTORE`
- delayed control transfer
- `SETHI`, arithmetic, branches, `CALL`, `JMPL`, and switch paths
- mapped firmware segments, synthetic RAM, and logged MMIO
- call stubbing with controlled return values

It was used as corroborating evidence, never as proof of real panel hardware.
Hardware-dependent MMIO, USB co-processor behavior, flash programming, and
TCON signaling are outside its model.

The cleaned public release currently includes the deterministic image builder,
verifier, and optimized-mode safety regression tests. The larger research
emulator is not public yet and should be published only after its generic tests
and firmware-independent fixtures are separated from local analysis
assumptions. Emulator-derived claims in this repository therefore include raw
static evidence and captured inputs/outputs; they are not presented as fully
publicly executable reproductions.

## Image builder

`tools/build_mga_only.py`:

- refuses unknown firmware hashes
- uses explicit runtime guards that remain active under `python3 -O`
- verifies stock offsets and invariants
- applies exactly two byte changes
- validates the output hash and checksum
- never searches for “similar” patterns in another image

## Image verifier

`tools/verify_mga_only.py` independently reloads both files and checks:

- exact hashes and size
- exact diff offsets
- embedded version
- MGA and shared Picture bytes
- unchanged key-dispatch and checksum-placeholder regions

## Safety regression tests

`tests/test_safety_guards.py` executes both public tools through optimized
Python and confirms that malformed images are still rejected. GitHub Actions
runs the tests in both normal and optimized modes. Positive-path validation
against the proprietary stock image remains a local test because that image
is intentionally not distributed.
