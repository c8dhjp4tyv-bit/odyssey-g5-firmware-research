# Contributing

Contributions are welcome when they preserve model and firmware provenance.
For findings that could plausibly cause persistent device damage, bypass a
model/panel safety gate, expose a destructive update path, or enable unsafe
factory writes, read [SECURITY.md](SECURITY.md) before opening a public report.

## Required evidence

Every new address or patch claim must include:

- full monitor model code and panel revision, if known
- firmware filename, size, SHA-256, and complete-file `sum16`
- VA and file offset
- original bytes and interpreted instruction/data
- how the address was reached
- static, emulator, and hardware confidence separately

## Patch acceptance

A patch is not accepted for release merely because it renders a string.
Feature-enabling patches additionally require:

- a reachable handler
- a verified hardware path
- input/timing/model guards understood
- an exact minimal diff
- output checksum/version consistency
- a recovery analysis

## Prohibited contributions

- Samsung firmware or extracted proprietary payloads
- IDA databases containing redistributed firmware
- blind cross-model offsets
- forced timing/EDID/VRR gates presented as safe
- TCON/FPGA/PDIC actions without handler and payload evidence
- factory calibration defaults copied from a different panel

## Reporting hardware results

Prefer the repository's **Hardware validation report** issue form. If reporting
manually, record the complete state:

```text
model:
panel revision:
firmware shown in OSD:
base image SHA-256 (if modified):
input port:
source connected:
resolution/refresh:
HDR:
Adaptive-Sync:
Eye Saver:
PC/AV mode:
picture mode:
exact joystick action:
observed result:
```
