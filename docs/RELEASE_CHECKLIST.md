# Release checklist

```text
Validated on:             2026-07-26
Validation reference:     current release commit/tag
Tested hardware:          LS32CG552EUXUF
```

Checked items below are the recorded `v1.0.0`-candidate validation. The USB
preparation section intentionally remains unchecked because it is a per-flash
operator checklist and must be completed again for every physical update.

## Repository

- [x] No `.img`, `.bin`, `.rom`, dump, IDA database, manual, or extracted
      proprietary payload is tracked.
- [x] README states the exact target model and base-image SHA-256.
- [x] Safety and no-recovery limitations are prominent.
- [x] The final image is generated locally, not distributed.
- [x] Builder and verifier use runtime guards, not Python `assert`.
- [x] Malformed images are rejected under `python3 -O`.
- [x] Read-only inventory parser covers every package record.
- [x] Generated catalogs contain metadata, not proprietary payload bytes.
- [x] All local Markdown links resolve.

## Build

- [x] Base-image size is `3,449,760`.
- [x] Base-image SHA-256 is
      `2e901cf2677b688d740dc62b279faedbee991c726ab5c3dcf75d156115cc96e7`.
- [x] Base-image `sum16` is `D43B`.
- [x] Embedded base version is `1010.0`.
- [x] Provenance is described as owner-supplied, not authenticated official stock.
- [x] Final embedded version and filename both say `1014.0`.
- [x] Final checksum suffix and `sum16` are both `D440`.
- [x] Final SHA-256 is
      `815f28e8e1eaba498c07cd500d581c63b16a887ea0da274152d1297b8d237350`.
- [x] Exact diff is only `0x273367` and `0x2D2776`.
- [x] Shared Picture byte `0x2D278D` remains `00`.
- [x] Positive private build reproduces the documented output SHA-256.

## USB preparation

- [ ] Fresh FAT32 drive.
- [ ] Exactly one IMG in the root.
- [ ] Filename unchanged.
- [ ] Monitor model and installed version rechecked.
- [ ] Stable power available.
- [ ] User understands there is no verified SPI recovery.

## Hardware validation

- [x] Firmware Information page shows `1014.0`.
- [x] Normal Game and Picture categories are present with an active source.
- [x] Long-UP opens MGA.
- [x] MGA lists 35 rows.
- [x] MGA rows remain read-only.
- [x] `MGA On/Off` remains `Off`.
