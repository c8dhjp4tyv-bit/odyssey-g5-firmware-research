# USB update pipeline and external-firmware stubs

## Safety boundary

The monitor has USB update access but no verified recovery mode or external
SPI backup in this project. The analysis distinguishes:

1. file discovery/staging;
2. model, version, extension, and checksum validation;
3. update-state UI/control;
4. flash programming;
5. optional external-component update hooks.

Finding a label at step 5 does not prove a programmer exists behind it.

## Filename and version validation

`USBCop_CheckVersion` begins at VA/file
`0x14CC9C / 0x17AC9C`. It compares:

- fixed model characters in the update filename against the embedded model;
- fixed-position version digits;
- the expected punctuation/extension layout;
- `bin` or `img` extension case-insensitively.

Malformed model/version strings return an error before the programming path.
The earlier attempt to replace `M-C5500GGZA-...` with a longer custom product
name was therefore rejected: it shifted fixed fields and broke future update
parsing.

The canonical 18-character embedded form must remain:

```text
M-C5500GGZA-NNNN.N
```

## Whole-file checksum

The updater computes a byte-sum over the whole file and compares it with the
four hexadecimal digits in brackets in the filename. For the analyzed base:

```text
sum16(contents) = D43B
filename        = M-C5500GGZA-1010.0[D43B].img
```

This is separate from record-level checksums. Records 5 and 6 carry
`0xFFFFFFFF` sentinels, while the complete-file sum still changes when either
record changes.

## Cross-processor update path

Evidence supports this division:

| Layer | Component | Evidence |
|---|---|---|
| USB filesystem/staging | 8051 record 2 | FAT/NTFS, load-file, wait-update, ISP commands |
| Model/version check | main SPARC `0x14CC9C` | fixed-format parser |
| UI/state machine | main SPARC `0x18CF9C`, `0x1D2018`, `0x1E07F0` | update state and OSD |
| USB data-tag dispatch | main SPARC `0x18DFFC`, `0x18E274` | tag/type parsing |
| External FW wrapper | main SPARC `0x1E4550` | accepts `fwType`, buffer length |
| Flash/ISP mechanics | 8051 controllers and platform services | SPI/ISP commands |

Key functions:

| VA | File | Role |
|---:|---:|---|
| `0x14CC9C` | `0x17AC9C` | version/model/extension gate |
| `0x18CF9C` | `0x1BAF9C` | common update-state handler |
| `0x18DFFC` | `0x1BBFFC` | USB data tag check |
| `0x18E274` | `0x1BC274` | USB data download/type dispatch |
| `0x1D2018` | `0x200018` | version/update confirmation OSD |
| `0x1E03DC` | `0x20E3DC` | USB-check failure reporting |
| `0x1E07F0` | `0x20E7F0` | update-now OSD/start |
| `0x1E4550` | `0x212550` | external-firmware wrapper |

At `0x1E4550`, only `fwType == 7` is forwarded into the USB-data download
path. The wrapper is not evidence that every resource label has a matching
external programmer.

## Why the update once appeared stuck at 1%

Hardware testing showed an update could remain at 1% for roughly an hour and
then reboot normally. The image was not left in a failed boot state. The
firmware exposes multiple asynchronous update states across the SPARC UI and
8051 USB/ISP controller; the displayed percentage is therefore not a direct
flash-address progress meter.

The exact stall cause was not captured with UART/USB traces, so it cannot be
assigned to one function. Confirmed operational guidance remains:

- do not remove power while an update screen is active;
- after a normal reboot, verify the displayed version and OSD state;
- do not infer a brick solely from a static 1% UI;
- without a recovery programmer, do not retry speculative code or external
  component patches.

## TCON UART debug menu

The serial debug printer at `0x193E38` lists DeInit/Init, OD table, frequency,
flash dump, TCON FW/DATA, version, FPGA, remote key, and exit entries.

The handler at `0x193F50` has explicit command branches only for:

```sparc
193F64  cmp  %i0, 0x11    ; 17, Remote Key
193F68  be   0x194018
193F6C  cmp  %i0, 0x63    ; 99, Exit
193F74  be   0x193FA8
```

Commands 1–16 do not dispatch TCON/FPGA update functions. The normal path
redraws the current debug-menu callback through a runtime table at probable
RAM address `0xA8034F30`.

The strings `TCON init Start/Done` and `TCON FW Update Start/Done` have zero
code/data xrefs in this build.

## Factory OSD labels

The service resource-pointer table contains:

| ID | Text |
|---:|---|
| 44 | `DisplayPort EQ  :` |
| 45 | `HDMI EQ         :` |
| 46 | `PDIC Update     :` |
| 47 | `TCON FW Update  :` |
| 48 | `TCON DATA Update:` |
| 49 | `FPGA Update     :` |

These entries are string pointers only. The active renderer at `0x1DB94C`
does not request IDs 44–49, and no adjacent action/value descriptor exists.

## PDIC

`sub_1E45D4` at VA/file `0x1E45D4 / 0x2125D4` has no callers and logs:

```text
update PDIC f/w is not implemented yet.
```

It performs no update and returns zero. Decision: **not implemented; do not
expose**.

## TCON, FPGA, and Panel Timing decisions

- **TCON FW/DATA:** labels and UART printer exist, but no reachable action or
  packaged updater payload was found.
- **FPGA:** label/UART text exists, but no reachable programmer or FPGA
  payload was found.
- **Panel Timing Update:** no corresponding service action exists in this
  build; normal panel timing calculations are not an updater.
- **Record 7:** verified HDMI/DP link/EQ code, not a TCON/FPGA image.

All four remain **do not enable**. This is a verified negative result, not an
assumption that the broader NT68500 platform can never support them.
