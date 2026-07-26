# Separate HDMI/DisplayPort link and EQ firmware

## Identity

Package record 7 maps:

```text
file:       0x3196E0..0x3491E0
flash:      0x050000
runtime VA: 0xA0060000..0xA008FB00
ISA:        SPARC V8, 32-bit, big-endian
```

IDA discovered 565 functions, 1,358 direct call edges, and 351 strings.
Record 8 contains companion pointers/configuration for this image.

Generated catalogs:

- [aux_functions.csv](generated/aux_functions.csv)
- [aux_symbol_anchors.csv](generated/aux_symbol_anchors.csv)

## Named EQ state machine

Debug-string xrefs identify this sequence:

| VA | Function |
|---:|---|
| `0xA00753A4` | `DRV_HDMI_InitialSettings` |
| `0xA0075AAC` | clear EQ errors |
| `0xA0075F78` | BA Turning |
| `0xA0076CBC` | PreRVGA |
| `0xA00778F4` | PreAEQ |
| `0xA0077D50` | RunAEQ |
| `0xA00780A4` | R Turning |
| `0xA0078374` | Pre-check error |
| `0xA00788D0` | R-check error |
| `0xA00792D0` | search process |
| `0xA007978C` | search EQ table |
| `0xA007A4A8` | PHY EQ |
| `0xA007AEB4` | PICDR |
| `0xA007B7F8` | DPHY |
| `0xA007BACC` | MEQ done check |
| `0xA007BF38` | PHY error check |
| `0xA007D078` | FSM done |
| `0xA007D16C` | PLL |
| `0xA007D4BC` | PHY init |

The image also contains DP link/HPD behavior and static-HDR/PQ helpers. No
TCON, FPGA, or PDIC updater strings are present.

## PreAEQ candidate selection

`preAEQIdx` is a byte in runtime channel state, not a persistent flash user
setting:

```sparc
A0077A14  ldub  [%l4+3], %g1
A0077A84  sll   %g1, 2, %g1
A0077A88  add   %l6, %g1, %o5
A0077A8C  lduh  [%o5+2], %l0
A0077A98  ldub  [%l6+%g1], %l1
A0077AC4  call  sub_A0081220
A0077BF8  clrb  [%l0+3]
```

Candidate tables are at:

| Runtime VA | File |
|---:|---:|
| `0xA008C9A6` | `0x346086` |
| `0xA008C9DE` | `0x3460BE` |

Entries supply RCT/CFT candidates used during automatic scanning.

## RunAEQ overrides candidates

The later state reads learned/current runtime results:

```sparc
A0077E78  lduh  [%g1+0x886], %o3
A0077E84  ldub  [%g1+0x884], %o4
A0077E90  and   %o4, 0xF, %o4
A0077EA8  or    %o4, %o3, %o3
A0077EB0  call  sub_A0081220
```

Emulator runs with hardware calls stubbed confirmed:

```text
candidate table A, idx 0/1/2 -> RCT 1/3/5, CFT 00FF
candidate table B, idx 0/1/2 -> RCT 6/8/A, CFT 00FF

runtime RCT=2, CFT=1234 -> PHY writes 1234/2
runtime RCT=9, CFT=5678 -> PHY writes 5678/9
```

The automatic FSM replaces the initial candidate with runtime results.

## Data-only control decision

Changing the candidate table could bias or break link training, but it would
not create a stable manual EQ value. Factory resource IDs 44/45 have neither
descriptors nor handlers. Meaningful manual HDMI/DP EQ is therefore **not
available as a safe data-only patch** in this build.

This is a negative capability result; it does not deny that the hardware has
real EQ. The hardware EQ is active and automatic.
