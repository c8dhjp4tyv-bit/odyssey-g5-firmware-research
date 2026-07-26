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

`tools/export_ida_inventory.py` opens a user-created IDB read-only through
IDA 9.x IDALib and exports segment, function, string-xref, and call-edge
metadata. A typical licensed local environment is:

```bash
IDADIR=/path/to/ida \
PYTHONPATH=/path/to/ida/idalib/python \
python tools/export_ida_inventory.py firmware.i64 inventory/
```

The generated public CSV catalogs contain derived metadata only, not IDB or
firmware bytes.

## Read-only package inventory

`tools/inventory_firmware.py` requires only the Python standard library. It
validates the NVTSC container, walks all records, reports hashes, entropy and
record checksums, and does not modify the input:

```bash
python3 tools/inventory_firmware.py /path/to/firmware.img
python3 tools/inventory_firmware.py /path/to/firmware.img --json
```

`tools/inventory_companion_records.py` validates the homologous 17-entry
exception-name tables in records 4 and 8:

```bash
python3 tools/inventory_companion_records.py /path/to/firmware.img
```

## Static structural recovery

The dependency-free scanners operate directly on a locally supplied,
SHA-256-pinned image and never modify it:

```bash
python3 tools/recover_sparc_structure.py \
  /path/to/firmware.img inventory/main/functions.json output-dir/
python3 tools/recover_8051_structure.py /path/to/firmware.img output-dir/
python3 tools/infer_debug_symbols.py \
  inventory/main/functions.json inventory/main/strings.json \
  output-dir/main_embedded_symbol_candidates.csv
```

The SPARC scanner recovers direct-call targets, `SAVE` prologues, indirect
`JMPL` sites, absolute addresses, and simple callback registration patterns.
The 8051 scanner follows reachable control flow with a full opcode-length
table and stops explicitly at computed dispatch. Embedded-symbol inference
extracts function-like names from longer diagnostic strings; its ambiguity
columns must be retained.

## Strict coverage and registries

```bash
python3 tools/classify_firmware_bytes.py \
  /path/to/firmware.img docs/generated/byte_classification.csv
python3 tools/classify_indirect_control_flow.py \
  docs/generated docs/generated/indirect_control_flow_detailed.csv
python3 tools/build_hardware_access_map.py \
  docs/generated/main_absolute_memory_refs.csv \
  docs/generated/hardware_absolute_accesses.csv
python3 tools/build_function_registry.py \
  docs/generated docs/generated/function_registry.csv \
  docs/generated/function_memory_effects.csv
```

The byte classifier rejects gaps, overlaps, malformed records, or violated
padding/sentinel invariants. The registry never leaves a required field empty:
missing names, boundaries, ABI, return semantics, and effects are explicitly
`UNRESOLVED` with a reason.

## Ghidra second-tool cross-check

```bash
python3 tools/run_ghidra_crosscheck.py \
  /path/to/firmware.img docs/generated/ghidra
python3 tools/compare_function_tools.py \
  docs/generated docs/generated/function_tool_crosscheck.json
```

Temporary raw slices/projects are deleted; only derived metadata remains.
Ghidra independently analyzes boot, STBC, updater, trap, main, and link
regions. Address disagreements with IDA/raw recovery are preserved. The
exporter intentionally records function entry addresses only: clean-project
repetitions showed that some Ghidra-generated boundaries, switch labels, and
call edges were scheduler-dependent. Two repetitions of the address-only
catalog were byte-identical.

To verify the deterministic boundary, generate a second output directory and
compare it recursively:

```bash
python3 tools/run_ghidra_crosscheck.py \
  /path/to/firmware.img /tmp/odyssey-ghidra-repeat
diff -qr docs/generated/ghidra /tmp/odyssey-ghidra-repeat
```

## IDA reproduction material

`tools/ida/odyssey_nvt_loader.py` offers six executable analysis views and
maps both verified main code/data segments. `odyssey_types.h` contains only
validated types. `apply_odyssey_symbols.py` applies unique debug-backed
anchors; `export_ida_inventory.py` exports metadata.

The loader source could not be CLI-smoke-tested locally because that IDA
installation reported an unavailable command-line license and unconfigured
Python target. The connected MCP database remains the actual IDA evidence;
the loader is marked provided but runtime-unvalidated.

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

The public release includes the deterministic image builder/verifier, static
recovery and cross-tool scanners, generated catalogs, and regression tests.
The larger research
emulator is not public yet and should be published only after its generic tests
and firmware-independent fixtures are separated from local analysis
assumptions. Emulator-derived claims in this repository therefore include raw
static evidence and captured inputs/outputs; they are not presented as fully
publicly executable reproductions.

## Image builder

`tools/build_mga_only.py`:

- refuses unknown firmware hashes
- uses explicit runtime guards that remain active under `python3 -O`
- verifies pinned base-image offsets and invariants
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

`tests/test_safety_guards.py` confirms that malformed images are rejected in
optimized Python. `tests/test_inventory_firmware.py` covers valid records,
sentinels, mismatches, malformed magic/tag/reserved bytes, and truncation.
GitHub Actions runs the tests in both normal and optimized modes. Positive-path validation
against the proprietary base image remains a local test because that image
is intentionally not distributed.
