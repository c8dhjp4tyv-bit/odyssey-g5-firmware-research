# Resolved open questions: MGA writes and HDMI/DP EQ

This note closes two questions that were previously marked unresolved for
`M-C5500GGZA-1010.0[D43B]`. No firmware image was patched. All mutations used
below existed only in emulator memory.

## Final decisions

| Question | Decision | Confidence |
|---|---|---|
| Change MGA descriptors from kind 2/3 to kind 4 | **DO NOT ENABLE** | Confirmed unsafe |
| Obtain a persistent manual HDMI/DP EQ control through data-only edits | **NOT MEANINGFULLY POSSIBLE** | Confirmed for this build |
| Draw factory resource IDs 44/45 by changing a resource-table flag | **NOT POSSIBLE** | Confirmed; no such flag/table exists |

## 1. MGA descriptor layout

The MGA item table is at VA/file `0x2A4E58 / 0x2D2B58`. It contains 35
records of `0x2C` bytes:

| Offset | Size | Meaning |
|---:|---:|---|
| `+0x00` | `0x18` | Inline NUL-terminated row name |
| `+0x18` | 4 | Kind |
| `+0x1C` | 4 | Display format: `1` numeric, `2` Off/On |
| `+0x20` | 4 | Maximum; the editor reads its low half at `+0x22` |
| `+0x24` | 2 | Primary configuration selector |
| `+0x26` | 2 | Secondary selector, used by kind 5 |
| `+0x28` | 4 | Apply/action selector |

Representative raw records:

```text
R-Gain1, VA/file 0x2A4E84 / 0x2D2B84
52 2D 47 61 69 6E 31 00 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 02 00 00 00 01
00 00 02 FE 00 02 00 00 00 00 00 01

Red Gain, VA/file 0x2A53AC / 0x2D30AC
52 65 64 20 47 61 69 6E 00 00 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 03 00 00 00 01
00 00 00 FF 00 03 00 00 00 00 00 01

MGA On/Off, VA/file 0x2A5430 / 0x2D3130
4D 47 41 20 4F 6E 2F 4F 66 66 00 00 00 00 00 00
00 00 00 00 00 00 00 00 00 00 00 02 00 00 00 02
00 00 00 01 00 00 00 00 00 00 00 01
```

Rows 1–30 (`R/G/B-Gain1..10`) are kind 2, numeric, maximum `0x2FE`,
selectors `2..31`. Rows 31–33 (`Red/Green/Blue Gain`) are kind 3, numeric,
maximum `0xFF`, selectors `3..5`. `MGA On/Off` is kind 2, Off/On, maximum 1,
selector 0.

### What kinds 2, 3, 4, and 5 do

The item-value renderer is VA/file `0x1D99C0 / 0x2079C0`:

```sparc
1D9A08  C2 06 20 18  ld    [%i0+0x18], %g1
1D9A0C  80 A0 60 04  cmp   %g1, 4
1D9A10  D0 16 20 24  lduh  [%i0+0x24], %o0
1D9A14  02 80 00 38  be    0x1D9AF4
1D9A18  98 10 20 00  mov   0, %o4
1D9A1C  80 A0 60 05  cmp   %g1, 5
1D9A20  02 80 00 44  be    0x1D9B30

1D9AF4  A1 2A 20 10  sll   %o0, 16, %l0
1D9AF8  7F FF 69 2E  call  sub_1B3FB0
1D9AFC  91 34 20 10  srl   %l0, 16, %o0
1D9B04  D8 0A 00 00  ldub  [%o0], %o4

1D9B30  A1 33 60 10  srl   %o1, 16, %l0
1D9B34  7F FF 69 1F  call  sub_1B3FB0
1D9B3C  D8 0A 00 00  ldub  [%o0], %o4
1D9B44  7F FF 69 1B  call  sub_1B3FB0
1D9B48  90 04 20 01  add   %l0, 1, %o0
1D9B4C  C2 0A 00 00  ldub  [%o0], %g1
```

- Kind 4 resolves `+0x24` and reads one byte.
- Kind 5 resolves `+0x24` and the following selector and combines two bytes.
- Kinds 2 and 3 take neither read branch. Their displayed value remains the
  initialized zero.

No behavioral distinction between kinds 2 and 3 exists in this renderer or
the editor below. Their likely higher-level MGA meanings differ, but that
missing backend is not present in these paths. The exact intended semantic
distinction between 2 and 3 therefore remains unknown; the observed behavior
of both is confirmed and identical: display-only zero, no storage write.

## 2. Factory item editor

The editor is VA/file `0x1DA96C / 0x20896C`. It accepts only kind 4 for the
write/persist branch; kind 5 is read-only here. Kinds 2 and 3 begin with zero,
perform no storage write, and may still run the descriptor's apply action.

```sparc
1DA9B8  DA 06 E0 18  ld    [%i3+0x18], %o5
1DA9BC  80 A3 60 04  cmp   %o5, 4
1DA9C0  D0 16 E0 24  lduh  [%i3+0x24], %o0
1DA9C4  02 80 00 5B  be    0x1DAB30
1DA9C8  82 10 20 00  mov   0, %g1
1DA9CC  80 A3 60 05  cmp   %o5, 5
1DA9D0  02 80 00 5D  be    0x1DAB44

1DAA08  D4 06 E0 18  ld    [%i3+0x18], %o2
1DAA0C  80 A2 A0 04  cmp   %o2, 4
1DAA10  02 80 00 5B  be    0x1DAB7C
1DAA14  E0 16 E0 24  lduh  [%i3+0x24], %l0
1DAA18  C2 06 E0 28  ld    [%i3+0x28], %g1

1DAB7C  97 2C 20 10  sll   %l0, 16, %o3
1DAB80  A1 32 E0 10  srl   %o3, 16, %l0
1DAB84  7F FF 65 0B  call  sub_1B3FB0
1DAB88  90 10 00 10  mov   %l0, %o0
1DAB8C  E2 2A 00 00  stb   %l1, [%o0]
1DAB90  7F FF 65 BC  call  sub_1B4280
1DAB9C  7F FF 65 05  call  sub_1B3FB0
1DABAC  7F FE CE 29  call  sub_18E450
1DABB0  92 10 20 01  mov   1, %o1
```

`sub_1B3FB0` is a general configuration-selector resolver, not an MGA
calibration resolver. It accepts selectors through a 0..`0x35` switch and
returns bytes in the normal configuration block. `sub_1B4280` maps the same
selector to its persistent configuration offset; `sub_18E450` commits/applies
the byte. Selector 0 is independently used by the VCP off-timer path.

The MGA descriptors also contain impossible collisions if interpreted as
kind-4 configuration selectors:

- `G-Gain1` and `Red Gain` both select 3.
- `B-Gain1` and `Green Gain` both select 4.
- `R-Gain2` and `Blue Gain` both select 5.
- `MGA On/Off` selects 0, the known off-timer configuration byte.

These selectors are therefore not valid unique MGA write targets.

## 3. MGA mutation emulator result

The editor was run with a sentinel byte returned by `sub_1B3FB0`. The
descriptor change existed only in mapped emulator RAM:

```text
item=01 kind=2 base        target=10->10 resolver=[]      persist=False
item=01 kind=2 forced->4   target=10->11 resolver=[2,2,2] persist=True
item=01 kind=2 forced->4   target=FF->00 resolver=[2,2,2] persist=True
item=31 kind=3 base        target=10->10 resolver=[]      persist=False
item=31 kind=3 forced->4   target=10->11 resolver=[3,3,3] persist=True
item=34 kind=2 forced->4   target=00->01 resolver=[0,0,0] persist=True
MGA_KIND4_SAFETY=UNSAFE_CONFIRMED
```

The `0xFF -> 0x00` case is especially decisive. Gain1..10 declare maximum
`0x2FE`, but kind 4 stores with `stb`; `0xFF + 1` becomes `0x100` and is
truncated to zero. This path cannot represent those 10-bit values.

**MGA decision: DO NOT ENABLE.** A kind-only data patch would make the UI
write persistent, unrelated general-configuration bytes. It is not random
unmapped memory, but it is the wrong valid storage, which is more dangerous.

## 4. HDMI/DP EQ storage and automatic behavior

The EQ partition maps file `0x3196E0` to runtime VA `0xA0060000`.

### PreAEQ index and candidate tables

`Jay_EQ_PreAEQ_S`, VA/file `0xA00778F4 / 0x330FD4`, keeps each channel's
`preAEQIdx` in runtime RAM:

```sparc
A0077A14  C2 0D 20 03  ldub  [%l4+3], %g1       ! runtime preAEQIdx
A0077A80  C2 0D 20 03  ldub  [%l4+3], %g1
A0077A84  83 28 60 02  sll   %g1, 2, %g1
A0077A88  9A 05 80 01  add   %l6, %g1, %o5
A0077A8C  E0 13 60 02  lduh  [%o5+2], %l0       ! candidate CFT
A0077A98  E2 0D 80 01  ldub  [%l6+%g1], %l1     ! candidate RCT
A0077AC4  40 00 25 D7  call  sub_A0081220        ! write candidate to PHY

A0077BF8  C0 2C 20 03  clrb  [%l0+3]             ! reset preAEQIdx
```

The per-port/channel base is runtime RAM near `0xA807803C`, with a port stride
of `0x898`. Two candidate tables do exist in the EQ flash image:

| Runtime VA | File offset | Example entries |
|---:|---:|---|
| `0xA008C9A6` | `0x346086` | `01 00 00 FF`, `03 00 00 FF`, `05 00 00 FF` |
| `0xA008C9DE` | `0x3460BE` | `06 00 00 FF`, `08 00 00 FF`, `0A 00 00 FF` |

Each four-byte entry supplies RCT from the low nibble of byte 0 and CFT from
the big-endian halfword at `+2`. These are automatic scan candidates, not a
stored user-selected EQ setting.

### RunAEQ overwrites the candidate from runtime results

`DRV_HDMI_EQScan_FSM_PHY_RunAEQ`, VA/file
`0xA0077D50 / 0x331430`, reads the learned/current values from runtime state
and writes them to the PHY:

```sparc
A0077E78  D6 10 68 86  lduh  [%g1+0x886], %o3   ! runtime CFT
A0077E84  D8 08 68 84  ldub  [%g1+0x884], %o4   ! runtime RCT
A0077E88  97 2A E0 10  sll   %o3, 16, %o3
A0077E90  98 0B 20 0F  and   %o4, 0xF, %o4
A0077EA8  96 13 00 0B  or    %o4, %o3, %o3
A0077EB0  40 00 24 DC  call  sub_A0081220        ! later PHY write
```

Later in the same FSM, link/port runtime bytes and static calibration tables
are combined again before another `sub_A0081220` call at `0xA0078014`.
The FSM then advances its state. There is no stable manual EQ variable.

### EQ emulator result

With hardware calls stubbed, two candidate-table selections and two different
runtime results were executed:

```text
table A, idx 0/1/2 -> PHY RCT 1/3/5, CFT 00FF
table B, idx 0/1/2 -> PHY RCT 6/8/A, CFT 00FF

RunAEQ runtime RCT=2 CFT=1234 -> all three PHY writes use 1234/2
RunAEQ runtime RCT=9 CFT=5678 -> all three PHY writes use 5678/9

PREAEQ_INDEX_STORAGE=RUNTIME_RAM
PREAEQ_TABLE_SELECTION=FLASH_CANDIDATE_TABLE_CONFIRMED
RUNAEQ_RUNTIME_RESULT_OVERRIDES_PREAEQ=CONFIRMED
```

Changing the flash candidate table could bias or damage automatic link
training, but it would not create a persistent manual EQ control. The FSM
replaces the candidate with runtime results.

## 5. Factory resource IDs 44 and 45

The factory resource table is only an array of 53 big-endian string pointers:

| ID | Pointer entry VA/file | String VA/file | Text |
|---:|---|---|---|
| 44 | `0x2A7820 / 0x2D5520` | `0x2A78F0 / 0x2D55F0` | `DisplayPort EQ  :` |
| 45 | `0x2A7824 / 0x2D5524` | `0x2A78D8 / 0x2D55D8` | `HDMI  EQ        :` |

The raw pointer entries are:

```text
00 2A 78 F0  00 2A 78 D8
```

There is no adjacent visibility flag, action ID, value pointer, or handler.
The renderer at VA/file `0x1DB94C / 0x20994C` writes literal resource IDs into
runtime state and calls the string renderer:

```sparc
1DB9A4  96 10 20 08  mov   8, %o3
1DB9A8  D6 24 A3 EC  st    %o3, [%l2+0x3EC]
1DB9AC  90 10 20 00  mov   0, %o0
1DB9B0  92 10 20 08  mov   8, %o1
1DB9B4  94 10 20 00  mov   0, %o2
1DB9B8  40 00 14 51  call  0x1E0AFC
1DB9BC  96 10 20 03  mov   3, %o3
1DB9C0  94 10 20 0D  mov   13, %o2
1DB9C4  D4 24 A3 EC  st    %o2, [%l2+0x3EC]
```

An emulator run completed the renderer and observed these requested IDs:

```text
8,13,14,15,2,2,17,21,1,22,4,10,1,51,1,28,29,0,50,1,52,1,27,18,12,20
```

IDs 44 and 45 are never requested. Adding rows requires executable changes:
a new literal-ID store, layout coordinates, and a draw call. Replacing an
existing literal with 44 or 45 would also be a code patch and would merely
relabel an existing row; its original handler would remain unrelated.

No DP/HDMI EQ value or action descriptor is attached to either string.
Consequently, even making the labels appear would produce dead or misleading
UI, not control the EQ FSM.

**EQ decision: data-only manual control is not meaningfully possible. Do not
expose IDs 44/45 as working controls and do not alter the candidate tables.**
