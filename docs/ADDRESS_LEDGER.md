# Address ledger for `1010.0[D43B]`

All addresses in this file are revision-specific.

| Purpose | VA | File offset | Confidence |
|---|---:|---:|---|
| SPARC code start | `0x100000` | `0x12E000` | Confirmed |
| SPARC data start | `0x1F0000` | `0x21DD00` | Confirmed |
| Key-event string table | `0x20755C` | `0x23525C` | Confirmed |
| Physical raw-key table | `0x2076B8` | `0x2353B8` | Confirmed |
| MGA key-dispatch cell | `0x2077BC` | `0x2354BC` | Confirmed |
| Factory OSD renderer | `0x1DB94C` | `0x20994C` | Confirmed |
| Category renderer | `0x1D9B60` | `0x207B60` | Confirmed |
| Factory input handler | `0x1DA128` | `0x208128` | Confirmed |
| Factory item editor | `0x1DA96C` | `0x20896C` | Confirmed |
| MGA category descriptor | `0x2A4A60` | `0x2D2760` | Confirmed |
| MGA supported byte | `0x2A4A76` | `0x2D2776` | Confirmed |
| Factory Picture descriptor | `0x2A4A78` | `0x2D2778` | Confirmed |
| Shared Picture condition | `0x2A4A8D` | `0x2D278D` | Confirmed |
| MGA item table | `0x2A4E58` | `0x2D2B58` | Confirmed |
| `MGA On/Off` descriptor | `0x2A5430` | `0x2D3130` | Confirmed |
| Factory resource table | `0x2A7770` | `0x2D5470` | Confirmed |
| DP EQ resource pointer (ID 44) | `0x2A7820` | `0x2D5520` | Confirmed |
| HDMI EQ resource pointer (ID 45) | `0x2A7824` | `0x2D5524` | Confirmed |
| Canonical firmware string | `0x245658` | `0x273358` | Confirmed |
| TCON UART menu printer | `0x193E38` | `0x1C1E38` | Confirmed |
| TCON UART handler | `0x193F50` | `0x1C1F50` | Confirmed |
| PDIC “not implemented” stub | `0x1E45D4` | `0x2125D4` | Confirmed |
| LED-driver selector | `0x182130` | `0x1B0130` | Confirmed |
| Dimming controller | `0x1A87F8` | `0x1D67F8` | Confirmed |
| Global PWM path | `0x1A8194` | `0x1D6194` | Confirmed |
| Common I2C dimming path | `0x1A8480` | `0x1D6480` | Confirmed |
| Config Low Input Lag gate | `0x180A80` | `0x1AEA80` | Confirmed |
| Common Low Input Lag gate | `0x183BFC` | `0x1B1BFC` | Confirmed |
| FreeSync wrapper | `0x1B23A0` | `0x1E03A0` | Confirmed |
| EDID FreeSync check | `0x19EB70` | `0x1CCB70` | Confirmed |

## Separate HDMI/DP EQ partition

For this partition only:

```text
file 0x3196E0 -> runtime VA 0xA0060000
file = 0x3196E0 + (VA - 0xA0060000)
```

| Purpose | Runtime VA | File offset | Confidence |
|---|---:|---:|---|
| PreAEQ FSM | `0xA00778F4` | `0x330FD4` | Confirmed |
| PreAEQ runtime-index load | `0xA0077A14` | `0x3310F4` | Confirmed |
| PreAEQ candidate PHY write | `0xA0077AC4` | `0x3311A4` | Confirmed |
| RunAEQ FSM | `0xA0077D50` | `0x331430` | Confirmed |
| Runtime RCT/CFT loads | `0xA0077E78` | `0x331558` | Confirmed |
| RunAEQ PHY write | `0xA0077EB0` | `0x331590` | Confirmed |
| PreAEQ candidate table A | `0xA008C9A6` | `0x346086` | Confirmed |
| PreAEQ candidate table B | `0xA008C9DE` | `0x3460BE` | Confirmed |

## TCON factory-resource entries

| ID | Pointer VA/file | String VA/file | Text |
|---:|---|---|---|
| 46 | `0x2A7828 / 0x2D5528` | `0x2A7890 / 0x2D5590` | `PDIC Update` |
| 47 | `0x2A782C / 0x2D552C` | `0x2A7878 / 0x2D5578` | `TCON FW Update` |
| 48 | `0x2A7830 / 0x2D5530` | `0x2A7860 / 0x2D5560` | `TCON DATA Update` |
| 49 | `0x2A7834 / 0x2D5534` | `0x2A7848 / 0x2D5548` | `FPGA Update` |

The active factory renderer did not request IDs `46..49`.

## EQ factory-resource entries

| ID | Pointer VA/file | String VA/file | Text |
|---:|---|---|---|
| 44 | `0x2A7820 / 0x2D5520` | `0x2A78F0 / 0x2D55F0` | `DisplayPort EQ` |
| 45 | `0x2A7824 / 0x2D5524` | `0x2A78D8 / 0x2D55D8` | `HDMI EQ` |

The active factory renderer did not request IDs 44 or 45. These entries have
no associated value or action descriptor.

## Factory Picture selectors

| Field | Selector | Runtime effect |
|---|---:|---|
| Gamma Test OnOff | `0x21` | Selects factory gamma path |
| Fac Gamma | `0x22` | Factory gamma value |
| Sub Gamma | `0x23` | Factory sub-gamma value |
| ColorTone Test OnOff | `0x24` | Selects factory color-temperature gains |
| EyeSaver Test OnOff | `0x2D` | Selects factory Eye Saver calibration |

These selectors resolve to real writable state. They are not safe user
feature toggles.
