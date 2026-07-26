# Deep control-flow recovery

This layer supplements IDA's conservative function list. It is structural
recovery, not a claim that 3,602 source-level C functions were reconstructed.

## Main SPARC results

For the exact pinned image, [`recover_sparc_structure.py`](../tools/recover_sparc_structure.py)
scans the mapped main code and independently recognizes direct `CALL` targets,
`SAVE` prologues, return boundaries, `JMPL`-based indirect transfers,
`SETHI`/`OR` absolute addresses, and simple callback registrations.

| Observation | Count |
|---|---:|
| IDA-defined starts | 3,074 |
| Internal direct-call targets | 2,674 |
| `SAVE` prologues | 2,612 |
| Union of callable-entry candidates | 3,602 |
| Candidates not defined by IDA | 528 |
| New high / medium / low confidence | 190 / 112 / 226 |
| Indirect calls | 131 |
| Computed jumps | 256 |
| Resolved absolute-memory references | 8,022 |
| Distinct absolute targets | 1,258 |
| Statically recovered callback bindings | 27 |

The 528 new entries are kept separate from IDA's function inventory. A direct
call target plus a `SAVE`, or a direct-call target immediately after a return
boundary, is strong structural evidence. A bare aligned `SAVE` is weaker
because code and inline tables can be confused without execution.

### Demonstrated IDA merge

IDA represents `0x1B5CE4..0x1B5D44` as one function, although direct calls
enter at all three labels:

```sparc
; VA 0x1B5CE4 / file 0x1E3CE4
; bytes 92 10 20 00 82 13 C0 00 7F FF FE 90 9E 10 40 00
1B5CE4  mov   0, %o1
1B5CE8  mov   %o7, %g1
1B5CEC  call  0x1B572C
1B5CF0  mov   %g1, %o7

; VA 0x1B5CF8 / file 0x1E3CF8
; bytes 92 10 20 01 82 13 C0 00 7F FF FE 8B 9E 10 40 00
1B5CF8  mov   1, %o1
1B5CFC  mov   %o7, %g1
1B5D00  call  0x1B572C
1B5D04  mov   %g1, %o7

; VA 0x1B5D0C / file 0x1E3D0C
; bytes 9D E3 BF 98 90 10 00 18 7F FF FE 86 92 10 20 00
1B5D0C  save  %sp, -0x68, %sp
1B5D10  mov   %i0, %o0
1B5D14  call  0x1B572C
1B5D18  mov   0, %o1
```

This explains a significant part of the old “unclassified function” count:
the disassembler's container is not always the firmware's callable-entry
boundary.

### Central diagnostic formatter

`VA 0x127854` / file `0x155854` has 2,271 recovered direct call sites. It
formats through `0x1E9B4C`, polls `0xA002C194`, and emits characters through
`0xA002C1A0`. It is therefore a UART/debug `printf`-like service, not a
business-logic function. Its huge fan-in also explains why naïve neighbor
category propagation can produce misleading labels.

## Callback recovery

The OSD/application callback bank occupies runtime slots
`0xA8037D80..0xA8037DE0`. Setters at `0x1A4DCC..0x1A4EEC` store callback
pointers, while wrappers at `0x1A4EF8..0x1A5310` load and invoke them.

Example invocation:

```sparc
; VA 0x1A4EF8 / file 0x1D2EF8
; bytes 9D E3 BF 98 03 2A 00 DF C2 00 61 84 80 A0 60 00
1A4EF8  save  %sp, -0x68, %sp
1A4EFC  sethi %hi(0xA8037C00), %g1
1A4F00  ld    [%g1+0x184], %g1       ; slot 0xA8037D84
1A4F04  cmp   %g1, 0
1A4F0C  and   %i0, 0xFF, %o0
1A4F10  call  %g1
```

Registration routine `VA 0x17A8FC` / file `0x1A88FC` binds this slot to
callback `0x1D27D8` at `0x17A914`. The generated callback CSV contains 27 such
bindings. Some targets are alternate leaf entries inside an IDA container,
which is another independent confirmation of merged boundaries.

Runtime-populated slots and table-indexed dispatches remain unresolved without
a RAM snapshot. The catalogs preserve every such site rather than assigning a
guessed target.

## 8051 reachable control flow

[`recover_8051_structure.py`](../tools/recover_8051_structure.py) decodes the
complete 256-opcode length table and follows reset/vector roots, direct calls,
direct/conditional branches and fall-through. `JMP @A+DPTR` is recorded as an
explicit analysis boundary.

| Record | Role | Reachable instructions | Reachable bytes | Entry candidates | Direct calls | Computed jumps |
|---:|---|---:|---:|---:|---:|---:|
| 0 | boot | 2,175 | 3,980 | 34 | 84 | 2 |
| 1 | STBC/control | 18,367 | 30,476 | 226 | 679 | 17 |
| 2 | USB updater | 3,718 | 5,931 | 63 | 212 | 3 |

These counts replace the earlier string-only description of records 1 and 2.
They still undercount paths selected through computed dispatch tables. The
tool reports 22 exact `JMP @A+DPTR` sites so future runtime traces can resume
from known boundaries.

## What remains unknowable statically

- callback values supplied only by runtime RAM, vendor ROM, or hardware;
- computed table entries whose index depends on live MMIO state;
- electrical support implied by common-platform code;
- source-level names/types for stripped leaf arithmetic and register helpers.

Those are recorded boundaries, not silently classified guesses.
