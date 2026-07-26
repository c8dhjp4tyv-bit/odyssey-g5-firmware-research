# Data, resources, EDID, and persistent storage

## Main data segment

Record 6 maps file `0x21DD00..0x3196C0` to
VA `0x1F0000..0x2EB9C0`. It contains:

- configuration and lookup tables;
- debug names and format strings;
- event-name tables;
- factory/menu descriptors;
- language resource-pointer tables and localized strings;
- EDID templates;
- embedded model/version text;
- user, picture, factory, MGA, and debug storage metadata.

This shared-platform data explains why unsupported feature names can exist
without a menu/action implementation.

## EDID templates and base-image provenance

The analyzed `1010.0[D43B]` base differs from the earlier `1008.3[C145]`
reference in 22 256-byte EDID templates. Each modified template has:

- display-name descriptor changed from `Odyssey G5` to `G5 umutcagand`;
- its EDID checksum byte adjusted.

The changed display-name offsets are:

```text
0x235D2F, 0x235E2F, ... , 0x23722F
```

The stride is `0x100`, and checksum changes occur at name offset `+0x20`.
This accounts for 308 of the 311 changed bytes between the two images.

The main application includes real EDID read/write, NVRAM, HDR-support, and
FreeSync-support paths. Editing a display name is therefore not equivalent to
changing a harmless UI label; the EDID checksum must remain valid and port
capability bits must not be altered casually.

## Embedded firmware identity

The canonical identity string is at:

```text
file 0x273358
VA   0x245658
text M-C5500GGZA-1010.0
```

It is consumed by the USB update parser as well as displayed in the UI. The
model field and fixed width must remain unchanged. The MGA-only build changes
only one version character, `1010.0 -> 1014.0`.

## NVRAM blocks

The NVRAM map reports separate addresses/sizes for:

- UD/user block;
- PQ/picture block;
- factory block;
- factory MGA block;
- debug block.

`SecHalUserData_SaveDiffToEEPROM` at `0x124A20` rejects zero/out-of-range
counts and performs differential persistence. Higher layers initialize and
save factory, game-picture, picture, and general user blocks independently.

This matters for MGA safety: a selector that resolves to valid persistent
memory is not automatically the correct MGA target. The forced kind-4 MGA
experiment wrote valid but unrelated general configuration bytes.

## Factory category descriptors

The MGA category descriptor is:

```text
descriptor VA/file: 0x2A4A60 / 0x2D2760
item table VA/file: 0x2A4E58 / 0x2D2B58
item count:          35
item size:           0x2C
supported byte:      descriptor + 0x16
supported VA/file:   0x2A4A76 / 0x2D2776
```

The adjacent Factory Picture descriptor has a condition at
`0x2A4A8D / 0x2D278D`. Hardware testing proved that field is shared with the
normal Game/Picture OSD state; enabling it is not an isolated visibility
toggle.

## Language resources are not menu tables

The English pointer table begins at `0x2A9F90`. It has 331 four-byte
big-endian pointers. Local Dimming, Ultrawide Game View, Dynamic Contrast,
FreeSync Premium, and many other common-platform strings are present.

The table has no per-string visibility or action flag. Active code chooses
resource IDs, then separate menu descriptors and handlers determine whether a
row exists and can be changed. Safe analysis must establish all three:

1. rendered resource ID;
2. descriptor/value source;
3. reachable action/persistence handler.

## Factory status resource table

The service table at `0x2A7770 / 0x2D5470` is an array of 53 string pointers.
IDs 44–49 are DP EQ, HDMI EQ, PDIC, TCON FW, TCON DATA, and FPGA labels. No
visibility flag, value pointer, or action pointer is adjacent to these
entries. Replacing a rendered ID could only draw a dead label.

## Record 4 USB-data objects

Record 4 names USB-downloadable object classes:

```text
edid_hdmi1, edid_hdmi2, edid_hdmi3
edid_dp, edid_dp1, edid_dp2
edid_typec, edid_typec1, edid_typec2
odtable
audio
M-USBDATA11-0000.0
```

These names align with the main app's USB data tag/type dispatcher and
download-to-NVRAM/audio/OD routines. They do not imply that TCON, FPGA, or
PDIC blobs are present.
