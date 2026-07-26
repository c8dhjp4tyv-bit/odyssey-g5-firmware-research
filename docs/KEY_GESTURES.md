# Joystick events and hidden-menu gestures

## Hardware-confirmed gesture

On the tested `LS32CG552EUXUF`, holding joystick **UP** opens the existing
factory screen headed `MGA`. This was observed before and after enabling the
MGA category support byte. The support patch changes `Not supported` into the
35-row MGA page; it does not change the joystick dispatcher.

The exact hold duration was not instrumented on hardware. The firmware's
long-press framework uses millisecond-like thresholds of 2,000, 5,000, and
approximately 8,191 ticks depending on runtime configuration. In practice,
five seconds is the normal first attempt, with eight to ten seconds covering
the longer variant.

## Key-event enum

| Value | Event |
|---:|---|
| `0x40` | PWR |
| `0x41` | MENU |
| `0x42` | AUTO |
| `0x43` | INPUT |
| `0x44` | FUNC |
| `0x45` | UP |
| `0x46` | DOWN |
| `0x47` | LEFT |
| `0x48` | RIGHT |
| `0x49` | USB_TEST |
| `0x4A..0x4C` | CUSTOM_1..3 |
| `0x4D` | FACT |
| `0x4E` | FACTRESET |
| `0x4F` | PWLOCK |
| `0x50` | OSDLOCK |
| `0x51` | TIMING_SWITCH |
| `0x52` | DEMO |
| `0x53` | USBUPDATE |
| `0x54` | MGA |
| `0x55` | TESTPAT |
| `0x56` | NONE |
| `0x57` | END |

The event-name table begins at `0x20755C / 0x23525C`.

## Physical/raw mapping

The raw-to-event table at `0x2076B8 / 0x2353B8` contains:

```text
raw 1 -> INPUT
raw 2 -> UP
raw 3 -> DOWN
raw 4 -> MENU or LEFT, context-dependent
raw 5 -> AUTO or RIGHT, context-dependent
```

FACT, FACTRESET, MGA, and TESTPAT have raw value zero and are synthetic
events, not separate physical switches.

## Long-UP synthetic MGA setup

At `0x17E34C`, runtime state is checked. When the relevant state equals 1 and
a runtime flag is set, the long-press mapper receives `UP -> MGA`:

```sparc
17E34C  cmp   %g1, 1
...
17E35C  cmp   %g1, 1
17E36C  mov   0x54, %o1       ; delay slot, MGA
```

The mapper at `0x17C2B8` stores the alternate event and enables the
long-press mask.

## Static/hardware discrepancy

In the exact base image, key-to-OSD table entry:

```text
table VA/file: 0x2077A8 / 0x2354A8
MGA index:      0x54 & 0x3F = 20
entry VA/file:  0x2077BC / 0x2354BC
base value:     0x10
```

The directly emulated dispatcher treats `0x10` as no action, while changing
it in memory to `0x05` reaches the factory renderer. The released MGA-only
image deliberately leaves the cell at `0x10`, yet hardware still opened the
MGA screen through long-UP.

Therefore the hardware gesture is confirmed, but this one static dispatcher
table is not its complete runtime explanation. A second product-state path,
runtime table replacement, or lower-controller mediation remains possible.
The repository does not claim the `0x10 -> 0x05` redirect is required or safe.

## Separate FACT candidate

Static code also installs `INPUT -> FACT` when OSD state equals `0x0C`:

```sparc
17E3E4  mov   0x43, %o0       ; INPUT
17E3E8  cmp   %g1, 0x0C
17E3F0  mov   0x4D, %o1       ; FACT
17E3F8  call  sub_17C2B8
```

FACT maps to OSD event 5 and reaches factory renderer `0x1DB94C`. Since raw 1
is INPUT, a center/ENTER long press is the strongest physical candidate.
However, the human meaning of state `0x0C` before entry was not proven, and
this gesture was not hardware-confirmed. It must remain **probable**, not a
published guaranteed combination.

## What is safe to tell users

- Confirmed: long-UP opened MGA on the tested unit.
- Confirmed: the released patch changes only category support, not gestures.
- Not confirmed: one universal gesture for every firmware or model suffix.
- Not released: dispatcher redirects or simplified RIGHT-long code patches.
