# Safety policy

This project uses a strict evidence hierarchy:

1. A string is only a lead.
2. A referenced descriptor proves that data is used.
3. A reachable handler proves that an action exists.
4. A hardware path and payload validation are required before calling an
   action usable.
5. A change is not considered releasable until the exact on-disk diff,
   checksum, parser constraints, and relevant execution path are tested.

## Non-negotiable rules

- Never flash an image built from a different model, suffix, size, SHA-256, or
  panel revision.
- Never rename an image without also understanding the embedded canonical
  version and filename checksum.
- Put exactly one candidate image in the root of a freshly formatted FAT32
  drive.
- Do not interrupt an update while progress is advancing.
- A frozen progress indicator is not permission to power-cycle. Exhaust the
  manufacturer's documented recovery path first.
- Do not edit factory calibration values without recording every original
  value.
- Do not force model gates that protect timing, EDID, VRR, or panel-dependent
  hardware.
- Do not expose an update string as a selectable action unless its handler,
  payload, flash target, validation, and recovery flow are all known.

## Recovery limitation

The tested monitor had no external SPI programmer or verified hardware
recovery path. That is why the released patch is data-only and why unsafe
feature candidates were rejected.

## No firmware redistribution

Do not commit Samsung `.img` files, extracted proprietary payloads, manuals, or
IDA databases. Publish hashes, offsets, original/target bytes, scripts, and
independently written analysis instead.
