# Experiment timeline, incidents, and resolutions

This document records negative results as first-class evidence. They prevent
future researchers from repeating unsafe assumptions.

## Phase 1: MGA visibility

### Observation

Holding joystick UP displayed a factory page headed `MGA`, followed by
`Not supported`.

### Cause

The MGA category and all 35 item descriptors already existed. The category
`supported` byte at file `0x2D2776` was `0`.

### Resolution

Change only `0x2D2776: 00 -> 01`. Hardware testing confirmed that the existing
MGA rows appeared.

### Important limitation

The values displayed as zero and could not be edited. Further analysis showed
that this is expected: MGA entries use descriptor kinds `2` and `3`, while the
working byte-write handler is associated with kind `4`. Blindly changing the
kind would route selectors to unrelated state.

## Phase 2: Factory Picture experiment

### Observation

Changing file `0x2D278D: 00 -> 01` exposed a second Factory `Picture`
category with 21 writable calibration fields.

### Unexpected effect

The normal user OSD lost its Game and Picture categories.

### Root cause

`0x2D278D` is a shared product/category condition, not a private factory-menu
visibility flag.

### Resolution

Restore `0x2D278D` to base value `00`. Do not release the Factory Picture patch.

## Phase 3: update indicator stuck at 1%

### Observation

An intermediate recovery image remained at 1% for approximately 60 minutes.
After power removal, the monitor booted normally.

### Analysis

The updater was observed waiting in a USB/co-processor handshake path. The
intermediate filenames advertised higher versions while their embedded
canonical version string still remained `1010.0`. A filename/embedded-version
mismatch is the leading explanation, but the exact hardware-side failure code
was not captured and the root cause is therefore not claimed as certain.

### Resolution

The final build changes both:

- filename version: `1014.0`
- embedded canonical version: `1014.0`

It also keeps the checksum suffix consistent with the complete-file `sum16`.

### Lesson

The filename is not the only version identity. A release checklist must compare
the filename, embedded canonical string, checksum suffix, file length, model
identifier, and exact binary diff.

## Phase 4: normal OSD items appeared grey

### Initial hypotheses

- Eye Saver or HDR blocker
- Eco picture mode
- a Factory Picture test flag left in NVRAM
- an MGA side effect

### Confirmed cause

The computer/video source was not connected. After an active computer signal
was connected, the normal Game and Picture items became available.

### Resolution

No firmware change. Confirm an active source before diagnosing grey OSD items.

### Lesson

OSD availability is runtime-state dependent. A black/no-signal state can look
like a persistent firmware regression. Hardware validation must record:

- active input and cable
- resolution and refresh rate
- PC/AV mode
- HDR state
- Adaptive-Sync state
- Eye Saver state
- current picture mode

## Final known-good state

- Firmware reports `1014.0`.
- Normal Game and Picture OSD categories are present with an active source.
- Holding UP opens MGA.
- MGA displays its 35 existing rows.
- MGA remains read-only.
- `MGA On/Off` displays `Off`.
