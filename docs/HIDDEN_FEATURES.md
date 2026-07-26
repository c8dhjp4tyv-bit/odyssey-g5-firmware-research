# Hidden-feature conclusions

The presence of a string is not evidence that a feature is usable on the
tested 32-inch G55C (`LS32CG552EUXUF`). This table summarizes the final
classification.

| Candidate | Evidence | Decision |
|---|---|---|
| MGA page | Complete existing renderer table; one support byte | Visible in final build, read-only |
| Factory Picture | Complete writable calibration table, but shared OSD condition | Rejected |
| Low Input Lag | Already present; timing and blocker checks are real | Use normal OSD |
| Adaptive-Sync/FreeSync | Already present; EDID/port checks are real | Use normal OSD |
| VRR Control | Already present | Use normal OSD |
| Contrast Enhancer | Already present with PQ handler | Use normal OSD |
| HDR Tone Mapping | Already present with HDR/PQ path | Use normal OSD |
| Dynamic Brightness | Already present; global dimming | Use normal OSD |
| Local Dimming | A common-platform LDC engine is compiled in, but this model selects global PWM and no panel-zone hardware/reachable model path was verified | Do not enable |
| Ultrawide Game View | Common string only; no verified viewport/timing support | Do not enable |
| PIP/PBP | Resource tables and real common scaler/capture paths exist; no active G55C menu/model capability or multi-input hardware path was verified | Do not enable |
| Type-C / DP-out / USB hub | Common board/debug paths and labels exist; the tested unit's corresponding ports/controller topology was not established | Do not enable |
| 3D LUT / VIP hue / custom saturation / custom brightness / post-offset | Callable factory-debug hooks exist, but they are low-level calibration controls rather than missing consumer features | Do not expose |
| Gamma / OverDrive raw enables | Real scaler controls already used by normal PQ/game logic; bypassing policy can invalidate panel calibration | Do not expose |
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
brightness array tied to the G55C panel, independent G55C zone-driver update
loop, or verified panel-zone topology was found.

The negative conclusion is **not** based on strings alone. A reusable LDC
implementation is present in the common scaler library:

```sparc
; DRV_LDC_SetPanelResolution-like routine
; VA 0x129D64 / file 0x157D64
129d64  save %sp, -0x68, %sp
129d68  set 0x1F9F60, %o0      ; "DRV_LDC_SetPanelResolution,%u,%u"
129d74  call 0x127854
...
129df4  sth %i1, [%g1+6]
129df8  sth %i0, [%g1+4]
129dfc  call 0x129B88
```

Related compiled routines reference `DRV_LDC_UpdateSegmentBoundary` at
`VA 0x129E54` / file `0x157E54`, `DRV_LDC_SetLDCSegment` at
`VA 0x12A074` / file `0x158074`, and intensity-gain update code at
`VA 0x12A734` / file `0x158734`. The identified test/setup caller at
`VA 0x1588B0` has no external code caller in the recovered direct-call graph.
This is strong evidence of a shared-platform library and test surface, but
not evidence that the G55C has addressable backlight zones. Forcing a resource
flag would therefore cross a hardware boundary that was not verified.

## Common-platform code is not a model unlock

### PIP/PBP

PIP/PBP is more than untranslated text. The main image contains resource
descriptors (`PIP / PBP` at data `VA 0x1F59B0`, file `0x2236B0`), a runtime
state formatter in `VA 0x10CDA4` / file `0x13ADA4`, capture branches in
`VA 0x1AE9BC` / file `0x1DC9BC`, and no-signal OSD logic in
`VA 0x1D7214` / file `0x205214`. Factory-debug dispatch also contains real
`SetPipMode`, `SetPipSize`, and `SetPipPosition` calls.

What is missing is equally important: no verified active G55C consumer-menu
descriptor, no confirmed model gate that can safely be flipped, and no
hardware proof that two simultaneous input pipelines are routed on this
board/panel combination. Replacing a visible menu resource with PIP/PBP would
only expose common library operations; it would not establish a safe source
route. Decision: **AÇILMAMALI / DO NOT ENABLE**.

### Type-C, DP-out, and USB hub

The image contains `TYPEC`, DP-out-over-Type-C factory commands,
`SecHalBoard_IsTypeCPowerOn`, and a USB-hub status debug command. These are
shared board-support surfaces. The debug-string xrefs land in factory command
dispatchers (`VA 0x195C20` for Type-C power and `VA 0x193D80` for USB-hub
status), not in an identified G55C consumer-menu path. A software flag cannot
create an absent Type-C connector, PD controller, DP-alt-mode mux, or hub.
Decision: **AÇILMAMALI / DO NOT ENABLE** unless a future board-level teardown
proves that exact hardware and traces exist.

### Low-level picture controls

The factory debug dispatcher at `VA 0x192698` / file `0x1C0698` references
real hooks for post-offset, VIP hue, custom saturation, custom brightness,
gamma, and overdrive. A nearby debug group also names `Enable3DLUT`, although
that particular string has no recovered xref in the current IDA database.
These APIs are calibration primitives used underneath supported PQ modes, not
standalone hidden user features. Exposing them without their calibration
schema, range rules, persistence owner, and restore path is unsafe.

| Primitive | Debug string VA | Recovered dispatcher xref |
|---|---:|---:|
| Post offset | `0x23EF90` | `0x194634` |
| 3D LUT | `0x23F1D0` | none recovered |
| VIP hue | `0x23F2E0` | `0x1946A0` |
| Custom saturation | `0x23F338` | `0x1946AC` |
| Custom brightness | `0x23F398` | `0x1946B8` |
| Gamma | `0x23F510` | `0x1946E8` |
| OverDrive | `0x23F8F0` | `0x1947BC` |

Decision: the implementations with xrefs are **real common-platform controls**,
but exposing them as new OSD toggles is **AÇILMAMALI / DO NOT EXPOSE**.

## Gate-bypass policy

Low Input Lag and FreeSync gates depend on timing, blockers, output frequency,
port, and EDID state. Forcing them to return true would remove safety and
compatibility checks. Such patches were tested only as analysis probes and are
not released.
