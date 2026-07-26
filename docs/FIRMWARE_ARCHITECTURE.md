# Firmware architecture and complete package map

## Provenance boundary

The exact analyzed base image is:

```text
filename: M-C5500GGZA-1010.0[D43B].img
size:     0x34A3A0 (3,449,760 bytes)
SHA-256:  2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7
sum16:    0xD43B
```

This is an owner-supplied base image, not an independently authenticated
Samsung release. Comparing it with the earlier owner-supplied
`M-C5500GGZA-1008.3[C145]` reference shows:

- records 0–5 and 7–9 are byte-identical;
- only record 6, the main data/resource partition, differs;
- there are 311 changed bytes;
- 308 changes are 22 EDID display-name fields changed from `Odyssey G5` to
  `G5 umutcagand`, plus the corresponding 22 EDID checksum bytes;
- the remaining three changes are the embedded version `1008.3 -> 1010.0`.

Therefore `1010.0[D43B]` is best described as a personalized derivative of
the `1008.3` reference, not as a newly compiled application. All executable
partitions are identical between those two files.

## Container format

The package starts with:

```text
7F 4E 56 54 53 43 5F 49 4D 47 0A
   "\x7fNVTSC_IMG\n"
```

The global header occupies `0x20` bytes. Ten records follow with no gaps.
Each record has a `0x20`-byte big-endian header:

```text
+0x00  u32 target flash address
+0x04  u32 payload length
+0x08  u32 byte-sum checksum, or 0xFFFFFFFF sentinel
+0x0C  u32 constant 0x04000000
+0x10  16 reserved zero bytes
+0x20  payload
```

The public read-only parser is
[`tools/inventory_firmware.py`](../tools/inventory_firmware.py).

## Record inventory

| # | Header | Payload | Flash target | Length | Checksum | Interpretation |
|---:|---:|---:|---:|---:|---:|---|
| 0 | `0x20` | `0x40` | `0x000000` | `0x8000` | `132B` | 8051 bootloader |
| 1 | `0x8040` | `0x8060` | `0x010000` | `0xFAC0` | `B12C` | 8051 STBC/control image |
| 2 | `0x17B20` | `0x17B40` | `0x020000` | `0xC180` | `8DF0` | 8051 USB/update image |
| 3 | `0x23CC0` | `0x23CE0` | `0x0D0000` | `0x7760` | `0291` | SPARC trap/boot-vector block |
| 4 | `0x2B440` | `0x2B460` | `0x0FC000` | `0x2860` | Main SPARC companion trap/runtime/config data |
| 5 | `0x2DCC0` | `0x2DCE0` | `0x108000` | `0x1F0000` | sentinel | Main SPARC application container |
| 6 | `0x21DCE0` | `0x21DD00` | `0x2F8000` | `0xFB9C0` | sentinel | Main data, resources, strings |
| 7 | `0x3196C0` | `0x3196E0` | `0x050000` | `0x2FB00` | `F687` | Separate HDMI/DP link/EQ SPARC image |
| 8 | `0x3491E0` | `0x349200` | `0x0A6000` | `0x1120` | `AC00` | Link SPARC companion trap/runtime/config data |
| 9 | `0x34A320` | `0x34A340` | `0x006000` | `0x60` | `250F` | Footer partition table |

All non-sentinel record checksums match the payload byte-sum modulo 65536.
The two `0xFFFFFFFF` fields cannot be literal 16-bit sums and act as
sentinels in these large records.

## Footer table

Record 9 is a sequence of big-endian `(target, meaningful_length)` pairs:

```text
00010000 0000FAA7
00020000 0000C16B
000D0000 0000775C
000FC000 00002858
00108000 002EB9AC
00050000 0002FAF0
000A6000 00001108
00030000 0000F9F0
000B0000 0001CDCC
FFFFFFFF FFFFFFFF ...
```

Targets `0x30000` and `0xB0000` are described but have no payload record in
this package. The listed lengths are slightly shorter than several physical
record lengths, consistent with padding/alignment. No safe conclusion can be
drawn about the absent regions without reading the monitor's flash directly.

## Main SPARC mappings

The application container's prefix is fully accounted for:

```text
file 0x02DCE0..0x03DCE0  0x10000 bytes  FF padding
file 0x03DCE0..0x12DCE0  0xF0000 bytes  00 padding
file 0x12DCE0..0x12E000  0x320-byte marker/padding header
file 0x12E000..0x21DCE0  relocated code/tables
```

The small header begins:

```text
AA 55 77 88 43 48 4B FF ... 45 C1
             "CHK"
```

`45 C1` is little-endian `0xC145`, matching the earlier reference image's
whole-file sum, and it remains unchanged in the personalized `D43B` base and
the hardware-tested MGA build. It is therefore a stale build/check marker,
not an enforced current whole-file checksum in the observed update path.

The verified analysis mappings are relocation mappings, not simple
flash-target mappings:

```text
Code: file 0x12E000 -> VA 0x00100000, length 0xEFCE0
      file = VA + 0x2E000

Data: file 0x21DD00 -> VA 0x001F0000, length 0xFB9C0
      file = VA + 0x2DD00
```

The code slice ends exactly at file `0x21DCE0`, where record 6 begins. IDA
found no function at `0x100000`; the first defined function is `0x10018C`
because the beginning contains tables/padding.

The separate link image maps:

```text
file 0x3196E0 -> VA 0xA0060000, length 0x2FB00
file = VA - 0xA0060000 + 0x3196E0
```

## Record 4 and record 8

These records share a clear companion-data layout. Each contains a pointer/ID
table for SPARC exception names such as Power-on reset, instruction-fetch
error, UNIMP, invalid SAVE/RESTORE, alignment fault, FPU/co-processor fault,
hardware breakpoint, divide-by-zero, and write-buffer error.

Record 4 points to exception strings at main VA `0x1F9A98..0x1F9CC0`, then
contains handler pointers, hardware register/value tables, the platform tag
`NT68500_TK_USB_IMG`, and named USB-data objects including `edid_hdmi1`,
`edid_dp`, `odtable`, and `audio`.

Record 8 begins with the equivalent exception table pointing to
`0xA0065B48..0xA0065D70`, followed by `0xA006xxxx/0xA007xxxx` handler pointers
and hardware configuration values. Those addresses land inside record 7.

Record 4 is therefore main-SPARC companion runtime/trap/config data; record 8
is the equivalent companion for the link image. Their precise loader ABI
remains undocumented, but their role and pairing are high confidence.

## Reproducible inventory command

```bash
python3 tools/inventory_firmware.py \
  /path/to/M-C5500GGZA-1010.0[D43B].img
```

The tool refuses malformed magic, record tags, nonzero reserved bytes,
truncated payloads, and trailing partial records. A checksum mismatch is
reported rather than silently accepted.
