# Static-to-dynamic validation matrix

The complete claim-by-claim matrix is
[`dynamic_validation_matrix.csv`](generated/dynamic_validation_matrix.csv).

Dynamic validation is intentionally not represented as universal. Selected
renderer, descriptor editor, gate, and EQ paths were exercised in the SPARC
emulator. A smaller set was observed on the owner's monitor. No UART capture,
runtime RAM dump, or logic-analyzer trace was available.

Consequently:

- a static callback store does not prove the slot's value at runtime;
- a probable MMIO address does not receive a register/bit name;
- a common driver path does not prove populated hardware;
- a Ghidra/IDA function boundary does not prove its ABI;
- the observed 1% update state has no invented root cause.

## Required next captures

1. UART from cold boot through one complete USB update.
2. Runtime RAM `0xA8030000..0xA8040000` after OSD initialization.
3. Logic-analyzer capture of panel-power, backlight PWM, and suspected I²C.
4. Non-destructive SPI read of footer-described absent regions.
5. Board/panel identifiers and controller markings.

Without those physical inputs, the repository can be exhaustive about
**known and unresolved evidence**, but cannot truthfully claim dynamic
validation of every function or hardware register.
