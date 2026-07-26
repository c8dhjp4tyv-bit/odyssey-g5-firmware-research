# MGA and Factory Picture

## What MGA is

MGA appears to be a multi-point panel RGB/gamma factory-calibration structure,
not a user picture-feature bundle.

The base table contains:

- `R/G/B-Gain1` through `R/G/B-Gain10`
- `Red Gain`, `Green Gain`, `Blue Gain`
- `MGA On/Off`
- navigation (`Back to upper`)

## Why it is visible but not editable

The renderer supports multiple descriptor kinds:

- kind `4`: resolves a selector to a byte pointer and can write with `stb`
- kind `5`: can read a 16-bit value through two selectors
- MGA points: kinds `2` and `3`, with no working edit path in this menu

The final `MGA On/Off` entry is also kind `2` and has selector `0`. Selector
`0` is used elsewhere by the VCP off-timer path:

```sparc
185C90  call sub_1B3FB0
185C94  mov  0, %o0
185C98  clrb [%o0]

185D00  call sub_1B3FB0
185D04  mov  0, %o0
185D08  stb  %i3, [%o0]
```

Converting the descriptor to kind `4` would therefore risk writing an
unrelated timer byte rather than enabling MGA.

This was subsequently confirmed in the emulator. A forced kind-4 `R-Gain1`
wrote and persisted selector 2; a forced `Red Gain` wrote selector 3; and a
forced `MGA On/Off` wrote selector 0. The kind-4 path uses `stb`, so a
Gain1..10 value with declared maximum `0x2FE` wrapped from `0xFF` to `0x00`.
Several rows also collide on selectors 3, 4, and 5.

The only identified call to
`SecLibFactory_GammaLoadTable(window_id, bWriteMGA)` supplies
`bWriteMGA = 0`. No call with `bWriteMGA = 1` was found.

**Conclusion:** a kind-only data patch is confirmed unsafe. Editable MGA
would require the missing MGA-specific storage mapping and apply/write path;
it cannot be safely enabled with a data permission flag. Full evidence:
[OPEN_QUESTIONS_RESOLVED.md](OPEN_QUESTIONS_RESOLVED.md).

## Factory Picture

The hidden Factory Picture category contains:

```text
Gamma Test OnOff
Fac Gamma
Sub Gamma
ColorTone Test OnOff
C RGain
C BGain
N RGain
N BGain
W1 RGain
W1 BGain
W2 RGain
W2 BGain
EyeSaver Test OnOff
ES L RGain
ES L BGain
ES L Sub Brightness
ES L Backlight
ES H RGain
ES H BGain
ES H Sub Brightness
ES H Backlight
```

These are real writable calibration values. That makes the page more
dangerous, not more useful. Enabling its shared condition byte removed the
normal OSD Game and Picture categories on hardware.

**Release decision:** keep Factory Picture hidden and preserve
`file 0x2D278D = 00`.
