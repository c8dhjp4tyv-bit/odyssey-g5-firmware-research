# Hardware and memory-access map

The exhaustive recovered absolute-access list is
[`hardware_absolute_accesses.csv`](generated/hardware_absolute_accesses.csv).
It contains 1,258 targets and preserves every load/store site, width, and
containing IDA function. Addresses in `0xA8xxxxxx` are classified as runtime
RAM; `0xCxxxxxxx`/`0xDxxxxxxx` are only **probable MMIO** until a Novatek
register manual or live bus trace assigns semantics.

The interface-level evidence and missing electrical facts are in
[`hardware_interfaces.csv`](generated/hardware_interfaces.csv).

## Confirmed software-facing interfaces

| Interface | Evidence | What is not yet known |
|---|---|---|
| UART | status service `0xA002C194`, transmit service `0xA002C1A0`, formatter `0x127854` | pins, UART instance, baud |
| PWM backlight | main paths `0x1A77B8`, `0x1A8194`; model selector returns PWM | final register/bit names and board net |
| I²C LED driver | compiled path `0x1A8480` | not selected for the tested model; bus/address unverified |
| Panel power GPIO | `0x117A64`, backlight `0x117D64/0x117DE4` | GPIO number and polarity |
| ADC joystick | STBC reachable key/wake paths | channel, thresholds, SFR addresses |
| SPI flash | boot/STBC JEDEC and quad-mode code | physical part and controller bit map |
| USB host/update | updater FAT/NTFS, load-file, ISP states | controller register map |
| CEC | STBC power/source/device-control paths | pin and SFR map |
| USB-C CC/PD | STBC sink/current/reset/Attention paths | whether components/connectors are populated |
| HDMI/DP PHY | link-image PreAEQ/RunAEQ state machine | vendor register names behind service calls |

## Panel/backlight boundary

Firmware proves global PWM is selected. Common LDC segment arithmetic is
compiled and a small gain helper is reused, but the full segment/panel setup
has no external direct caller and no zone transport was identified. Firmware
alone therefore cannot establish addressable backlight-zone hardware.

Board photographs, panel part number, continuity checks, I²C/SPI captures, or
a logic-analyzer trace are required before GPIO nets, bus addresses, and
register bit names can move from `UNRESOLVED` to confirmed.
