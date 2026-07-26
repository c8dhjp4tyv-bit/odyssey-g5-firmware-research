# Hidden-feature conclusions

The presence of a string is not evidence that a feature is usable on the
tested 32-inch G55C (`LS32CG552EUXUF`). This table summarizes the final
classification.

| Candidate | Evidence | Decision |
|---|---|---|
| MGA page | Complete existing renderer table; one support byte | Visible in final build, read-only |
| Factory Picture | Complete writable calibration table, but shared OSD condition | Rejected |
| Low Input Lag | Already present; timing and blocker checks are real | Use stock OSD |
| Adaptive-Sync/FreeSync | Already present; EDID/port checks are real | Use stock OSD |
| VRR Control | Already present | Use stock OSD |
| Contrast Enhancer | Already present with PQ handler | Use stock OSD |
| HDR Tone Mapping | Already present with HDR/PQ path | Use stock OSD |
| Dynamic Brightness | Already present; global dimming | Use stock OSD |
| Local Dimming | Common string, but model selects global PWM and no zone engine was found | Do not enable |
| Ultrawide Game View | Common string only; no verified viewport/timing support | Do not enable |
| TCON FW Update | UART/factory string without working command handler/payload | Do not enable |
| TCON DATA Update | Same | Do not enable |
| FPGA Update | String only; no payload or reachable action | Do not enable |
| PDIC Update | Stub explicitly reports “not implemented yet” | Do not enable |
| Panel Timing Update | No update menu/handler in this build | Do not enable |
| DisplayPort/HDMI EQ factory rows | Labels 44/45 only; no value/action descriptor; EQ is an automatic runtime FSM | Do not enable |

## TCON evidence

The UART menu printer lists TCON-related labels, but its command handler only
has real branches for:

- command `17`: Remote Key
- command `99`: Exit

Commands `1..16` do not call update/flash routines. Factory resource IDs
`46..49` contain PDIC/TCON/FPGA labels, but the active factory renderer never
uses those IDs.

The strings:

```text
TCON init Start
TCON init Done
TCON FW Update Start
TCON FW Update Done
```

have no code/data references in the analyzed build.

The separate SPARC payload at runtime `0xA0060000` is dominated by HDMI/DP PHY
and link logic, not a TCON updater.

## HDMI/DP EQ evidence

The separate payload does contain real EQ logic, but not a manual factory
control. `preAEQIdx` is a runtime byte near `0xA807803C`; it indexes flash
candidate tables at `0xA008C9A6` or `0xA008C9DE`. The later RunAEQ state reads
learned RCT/CFT values from runtime offsets `+0x884/+0x886` and writes those
values to the PHY, replacing the initial candidate.

Factory resource IDs 44 and 45 are only string pointers for
`DisplayPort EQ` and `HDMI EQ`. The renderer never requests them and there is
no adjacent value pointer or handler. See
[OPEN_QUESTIONS_RESOLVED.md](OPEN_QUESTIONS_RESOLVED.md).

## Local Dimming evidence

The model LED-driver selector is:

```sparc
; VA 0x182130 / file 0x1B0130
retl
mov 0, %o0
```

The dimming controller interprets:

```text
0 = PWM
1 = I2C
2 = OLED
```

This build therefore selects global PWM. No spatial-zone histogram, zone
brightness array, independent channel update loop, or verified panel-zone
topology was found.

## Gate-bypass policy

Low Input Lag and FreeSync gates depend on timing, blockers, output frequency,
port, and EDID state. Forcing them to return true would remove safety and
compatibility checks. Such patches were tested only as analysis probes and are
not released.
