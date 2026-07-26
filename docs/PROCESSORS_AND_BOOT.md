# Processors, boot chain, and auxiliary controllers

The package contains code for at least two instruction sets and several
execution roles. Treating the entire file as one flat SPARC image or one
banked 8051 image produces false disassembly.

## Processor/role summary

| Component | ISA | Package record | Role | Confidence |
|---|---|---:|---|---|
| Bootloader | 8051 | 0 | Reset, flash setup, partition loading | Confirmed |
| STBC/control | 8051 | 1 | Power, keys, Type-C/CC, CEC, mailbox, Leon control | High |
| USB updater | 8051 | 2 | USB host/filesystem and update-state control | High |
| Trap/vector block | SPARC V8 BE | 3 | Trap/startup vectors and runtime handoff | High |
| Main application | SPARC V8 BE | 5+6 | OSD, PQ, source, storage, event system | Confirmed |
| Link/EQ image | SPARC V8 BE | 7+8 | HDMI/DP PHY training and EQ FSM | Confirmed |

## 8051 bootloader

Record 0 maps package file `0x40` to 8051 code address `0x0000`.

Reset:

```asm
0000  02 13 60    ljmp 0x1360
```

The startup at `0x1360` clears internal/XDATA state, sets the stack pointer,
and transfers to the main boot routine around `0x0F3F`. IDA conservatively
defined 46 functions; the generated list is
[`boot8051_functions.csv`](generated/boot8051_functions.csv).

The boot image handles:

- supported SPI-flash JEDEC IDs and single/dual/quad modes;
- partition-table loading;
- reset/interrupt vectors;
- STBC code handoff;
- basic UART diagnostics.

The flash-ID table includes Macronix, Winbond, SST, and ISSI identifiers. A
wrong or unsupported flash part is a real boot risk independent of any OSD
patch.

### Partition-loader success flag

The routine beginning at `0x0003` sets bit `RAM_20.2` near its start:

```asm
000C  D2 02       setb RAM_20.2
```

No path in that routine clears the bit. Its end copies the bit into carry:

```asm
05A0  A2 02       mov C, RAM_20.2
05A2  22          ret
```

The wrapper at `0x138D` interprets that result. This specific path is a loader,
not a cryptographic verifier. It does not prove that USB update has no checks:
the update path separately validates filename format, model, version, and
whole-file sum16 before programming.

## STBC/control image

Record 1 resets with:

```asm
0000  02 BA CE    ljmp 0xBACE
```

Aggressive 8051 autoanalysis is unreliable here because code, tables, and
indirect dispatch data overlap. Subsystem identification therefore uses reset
vectors, valid direct calls, register access, and diagnostic strings rather
than claiming exact function boundaries.

Confirmed or high-confidence responsibilities:

- power-saving and power-off mailbox commands;
- panel/Leon main and sub-core RUN/STOP control;
- AHB/PBus bridge control;
- ADC joystick/key detection and wake-up paths;
- USB-C CC state machine, sink startup, current advertisement, hard reset,
  and Attention handling;
- USB hub status and switching;
- DPTX HDCP and EDID mailbox operations;
- CEC power-up, power-down, active-source, and device-control commands;
- SPI flash read and quad-mode setup;
- watchdog/system-crash reset path;
- status LED and warm-reset handling.

Representative evidence includes:

```text
Leon2 (Main) RUN...
Leon2 (Main) STOP...
Leon2 (Sub) RUN...
Leon2 vs AHB clk is 3:1
PBus to AHB bridge Error!!
USBCC_SNK_Startup
PWR_DPMS ADC key
###SYSTEM CRASH, RESET###
```

This image explains why joystick/power behavior can exist below the main
SPARC OSD event layer.

## 8051 USB/update image

Record 2 resets with:

```asm
0000  02 B1 1F    ljmp 0xB11F
```

Its strings and reachable code establish a USB host/update role:

```text
TagInfo.ValidRegionNext
TagInfo.ValidRegionCurrent
CMD_LOADFILE2DRAM
STATUS_WAIT_FW_UPDATE
CheckSum Fail!
CMD_START_ISP_ROMCODE_MODE
CMD_START_ISP_ROMCODE_MODE_DUALFW
MSDOS5.0 ... NTFS
```

This controller participates in locating and staging update files. The main
SPARC application still performs the model/version UI and state-machine work,
so “USB updater” is a cross-processor pipeline rather than one function.

## SPARC trap/vector record

Record 3 begins with SPARC V8 big-endian vector-like code. At the probable
runtime mapping `0xA00E0000`:

```sparc
A00E0000  mov   %g0, %l0
A00E0004  sethi ..., %l4
A00E0008  jmp   %l4
```

The first `sethi` resolves to `0xA0029000`, so the initial jump is:

```sparc
A00E0000  A0 10 00 00  mov   %g0, %l0
A00E0004  29 28 00 A4  sethi %hi(0xA0029000), %l4
A00E0008  81 C5 20 00  jmp   %l4
A00E000C  01 00 00 00  nop
```

Later vector entries jump to `0xA0029460`, `0xA0029678`,
`0xA00296D0`, and related high-runtime handlers. Record 4 contains matching
`0xA002xxxx` handler pointers and exception-name/number tables. Operations
that radare2 marks invalid at vector boundaries correspond to SPARC
special-register forms involving `%wim`/`%tbr`.

The `0xA00E0000` runtime base is consistent with the flash-to-runtime mapping
and makes all vector targets coherent, but has not been observed in a loader
trace. The base remains **high-confidence/probable**, while the decoded jump
targets are exact.

## Main SPARC application

The main application is 32-bit, big-endian SPARC V8 using register windows,
delay slots, `save`/`restore`, and absolute `sethi` + `or` data references.
IDA discovered:

```text
functions:       3,074
call edges:      8,677
strings:         16,762
symbol anchors:  250 debug-string-backed mappings
```

See [MAIN_APPLICATION_MAP.md](MAIN_APPLICATION_MAP.md).

## Separate link/EQ SPARC image

Record 7 is not TCON firmware. It is another SPARC V8 image with:

```text
runtime VA:      0xA0060000..0xA008FB00
functions:       565
call edges:      1,358
strings:         351
symbol anchors:  22
```

Named anchors form a continuous HDMI PHY EQ state machine from InitialSettings
through PreAEQ, RunAEQ, error checks, PLL, and Done. See
[AUX_LINK_FIRMWARE.md](AUX_LINK_FIRMWARE.md).
