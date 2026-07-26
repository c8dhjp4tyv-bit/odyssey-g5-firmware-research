# Main SPARC application map

## Analysis scope

IDA analyzed two relocated segments:

```text
LOAD code  0x00100000..0x001EFCE0  RX  0xEFCE0 bytes
LOAD data  0x001F0000..0x002EB9C0  RW  0xFB9C0 bytes
```

The database contains 3,074 functions, 8,677 direct call-graph edges, and
16,762 strings. Because the image is stripped and makes indirect calls,
function boundaries and direct edge counts are an analysis lower bound.

The complete generated navigation tables are:

- [main_functions.csv](generated/main_functions.csv)
- [main_symbol_anchors.csv](generated/main_symbol_anchors.csv)

## Application architecture

The main firmware uses an event/action architecture rather than exposing a
conventional RTOS task list. Separate event families exist for:

- application/signal state;
- key events;
- OSD events;
- DDC/CI events;
- system-state/power events.

String tables enumerate power-on/off/saving, cable/no-signal/unstable,
before/after-display, mute, out-of-range, OSD refresh, USB update, factory,
MGA, and test-pattern events.

High-value dispatch functions:

| VA | File | Inferred symbol/role |
|---:|---:|---|
| `0x1791E0` | `0x1A71E0` | `__APPTasksAfterDisplay` |
| `0x1798C8` | `0x1A78C8` | `SecApp_APPActionDispatcher` and display/mute task group |
| `0x17AA7C` | `0x1A8A7C` | Event publisher/debug formatter |
| `0x17B778` | `0x1A9778` | `__DpmsHandler` |
| `0x17C4A4` | `0x1AA4A4` | `SecApp_KeyActionDemander` |
| `0x17EC80` | `0x1ACC80` | `__processKeyEvent` |
| `0x17F078` | `0x1AD078` | `__processOsdEvent` |
| `0x17F130` | `0x1AD130` | `__processAppEvent` |
| `0x1D6FE8` | `0x204FE8` | `SecAppOsd_MenuHandler` |

The event strings are debug-name evidence, while the actual enum numbers are
derived from their indexed tables. Relevant key values are documented in
[TECHNICAL.md](TECHNICAL.md).

## Boot and common initialization

| VA | File | Role |
|---:|---:|---|
| `0x18B9F4` | `0x1B99F4` | ROM checksum helper |
| `0x18BA48` | `0x1B9A48` | HDCP 2.2 application-data overwrite check |
| `0x18BFC0` | `0x1B9FC0` | common driver reset |
| `0x18C2B0` | `0x1BA2B0` | boot-flow state/check initialization |
| `0x18CF9C` | `0x1BAF9C` | update-state handler |

The main app initializes board/scaler services, restores persistent blocks,
drives source detection, and transitions into the event dispatch system. The
8051 controller remains responsible for lower-level power/key/flash services.

## Board and scaler layer

Representative debug-string-backed anchors:

| VA | Symbol |
|---:|---|
| `0x117A64` | `SecHalBoard_SetPanelPower` |
| `0x117D64` | `SecHalBoard_SetBackLightOn` |
| `0x117DE4` | `SecHalBoard_SetBackLightOff` |
| `0x1180E8` | `SecHalBoard_TurnOnOffUsbPortPwr` |
| `0x11EBCC` | `SecHalScaler_ToggleHPD` |
| `0x11F1A4` | `SecHalScaler_ReadEdidData` |
| `0x11F43C` | `SecHalScaler_WriteEdidData` |
| `0x120BC0` | `SecHalScaler_SetSaturation` |
| `0x121328` | `SecHalScaler_SetSharpness` |
| `0x1218A8` | `SecHalScaler_SetPreRevGamma` |
| `0x1229F8` | `SecHalScaler_SetInputSource` |
| `0x123620` | `SecHalScaler_UpdateSyncState_CallBack` |
| `0x124804` | `SecHalScaler_SetUsbSwitch` |

Callbacks update input width/height/H/V frequency, interlace, VRR, output
timing, DCLK, and sync-lock state.

## Picture/PQ pipeline

| VA | File | Symbol |
|---:|---:|---|
| `0x1A727C` | `0x1D527C` | energy-saving solution |
| `0x1A7334` | `0x1D5334` | response-time/overdrive drive |
| `0x1A77B8` | `0x1D57B8` | dynamic PWM |
| `0x1A8194` | `0x1D6194` | LED-driver PWM dimming |
| `0x1A8480` | `0x1D6480` | LED-driver I2C dimming |
| `0x1A87F8` | `0x1D67F8` | dimming controller |
| `0x1A974C` | `0x1D774C` | HDR on/off handler |
| `0x1A9A00` | `0x1D7A00` | color-space mode |
| `0x1AB790` | `0x1D9790` | eye-protection adjustment |
| `0x1ABB10` | `0x1D9B10` | color-parameter update |
| `0x1AC1F8` | `0x1DA1F8` | picture-mode/MagicBright drive |
| `0x1AD510` | `0x1DB510` | gamma drive |
| `0x1AD880` | `0x1DB880` | Black Equalizer |
| `0x1ADA00` | `0x1DBA00` | Contrast Enhancer |

The LED-driver selector returns `0`, selecting one global PWM path on this
model. Common-platform I2C and dimming strings do not establish spatial local
dimming hardware.

## Source, link capability, and EDID

| VA | Symbol |
|---:|---|
| `0x19E490` | NVRAM EDID table read |
| `0x19E500` | NVRAM EDID block write |
| `0x19E83C` | EDID write |
| `0x19EAD4` | EDID HDR support test |
| `0x19EB70` | EDID FreeSync support test |
| `0x19EF5C` | EDID drive |
| `0x1B0338` | input-source drive |
| `0x1B0F18` | cable-connection event |
| `0x1B1934` | auto-source switch handler |
| `0x1B24E4` | FreeSync on/off drive |
| `0x1B312C` | refresh-rate adjustment |

Low-input-lag and FreeSync “workable” functions are dynamic capability gates,
not fixed SKU booleans. They combine current timing, output frequency,
blockers, port state, and EDID. Forcing their return values bypasses real
compatibility checks and is not released.

## OSD and factory UI

| VA | Symbol/role |
|---:|---|
| `0x1B7E04` | OSD background-window renderer |
| `0x1CCA1C` | UP-key direct OSD |
| `0x1D0C60` | left/right direct menu |
| `0x1D2018` | USB update version OSD |
| `0x1D3420` | virtual aim point |
| `0x1D58C8` | OSD arena-button fill |
| `0x1D6FE8` | menu handler |
| `0x1D99C0` | factory item-value renderer |
| `0x1D9B60` | factory category renderer |
| `0x1DA96C` | factory item editor |
| `0x1DB94C` | factory service/status renderer |

OSD language resources are shared-platform assets. A string pointer alone is
not a menu item: active renderers request numeric resource IDs and may have
separate descriptor/action tables.

## Persistent storage

The NVRAM map exposes blocks for:

- user data;
- picture/PQ data;
- factory data;
- factory MGA data;
- debug data.

Representative functions:

| VA | Symbol |
|---:|---|
| `0x124A20` | `SecHalUserData_SaveDiffToEEPROM` |
| `0x124BC8` | NVRAM map initialization/reporting |
| `0x124F34` | picture block save |
| `0x18D45C` | download to NVRAM |
| `0x18E4E4` | common user-parameter save |
| `0x1B42D0` / `0x1B440C` | factory-data initialization paths |
| `0x1B55E4` | user-data initialization |
| `0x1B5D88` | differential user-data save |

MGA descriptors do not point to a valid MGA write backend. Forcing their kind
to the generic byte editor redirects them into unrelated persistent
configuration selectors; see [OPEN_QUESTIONS_RESOLVED.md](OPEN_QUESTIONS_RESOLVED.md).

## Sound and power

Sound anchors cover mute on/off, audio source/channel, volume, PEQ, amplifier
control, and downloadable audio/overdrive data. Power anchors cover
on/off/saving/wakeup, DPMS, off timers, ECO timer, panel power, backlight, and
USB-A/Type-C power.

The hardware incident in which normal Picture/Game items appeared grey while
no source was connected is consistent with runtime source-state gating. After
HDMI was connected, the items returned; it was not persistent damage caused
by the MGA-only byte.
