# Technical map

## Exact target

```text
Exact model:  Samsung Odyssey G5 G55C 32-inch, LS32CG552EUXUF
Firmware:     M-C5500GGZA-1010.0[D43B].img
Size:         0x34A360 (3,449,760) bytes
SHA-256:      2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7
sum16:        0xD43B
CPU:          SPARC V8, 32-bit, big-endian
```

## SPARC address mapping

```text
Code:
  file 0x12E000 -> VA 0x100000
  length 0xEFCE0
  file = VA + 0x2E000

Data:
  file 0x21DD00 -> VA 0x1F0000
  length 0xFB9C0
  file = VA + 0x2DD00
```

Absolute data references commonly use:

```sparc
sethi %hi(address), %reg
or    %reg, %lo(address), %reg
```

## MGA category descriptor

```text
Descriptor VA:           0x2A4A60
Items VA:                0x2A4E58
Item count:              0x23 (35)
Item descriptor size:    0x2C
Category condition:      descriptor +0x15 = 1
Supported byte:          descriptor +0x16
Supported VA/file:       0x2A4A76 / 0x2D2776
Base/final:              00 / 01
```

The base category renderer:

```sparc
; sub_1D9B60
; VA 0x1D9B94 / file 0x207B94
1D9B94  DA 0B E0 16  ldub  [%o7+0x16], %o5
1D9BA4  80 A3 60 00  cmp   %o5, 0
1D9BAC  02 80 00 2E  be    0x1D9C64
1D9BB0  C2 0B E0 14  ldub  [%o7+0x14], %g1
```

`supported == 0` draws `Not supported`; `supported == 1` walks the existing
35 descriptors.

## Relevant key-event values

| Value | Event |
|---:|---|
| `0x40` | `PWR` |
| `0x41` | `MENU` |
| `0x43` | `INPUT` |
| `0x45` | `UP` |
| `0x46` | `DOWN` |
| `0x47` | `LEFT` |
| `0x48` | `RIGHT` |
| `0x4D` | `FACT` |
| `0x4E` | `FACTRESET` |
| `0x54` | `MGA` |
| `0x55` | `TESTPAT` |

The tested hardware observation was that holding joystick UP opened the MGA
screen. The firmware contains multiple state-dependent synthetic long-press
remaps; physical interpretation must therefore be confirmed on hardware and
must not be inferred only from enum names.

## Shared Factory Picture field

```text
Factory Picture descriptor VA:  0x2A4A78
Shared condition VA/file:        0x2A4A8D / 0x2D278D
Base:                            00
Rejected experiment:             01
```

Setting this field to `1` made Factory Picture visible, but hardware testing
also showed that the normal Game and Picture OSD categories disappeared. The
final build keeps it at `0`.

## Final patch

```text
file 0x273367: 30 -> 34  embedded version 1010.0 -> 1014.0
file 0x2D2776: 00 -> 01  MGA supported
```

No executable instruction is changed.
