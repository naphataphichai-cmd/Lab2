# Lab 03 — Browser Acceptance Record (A1–A5)

Shared inputs for every case: `VCC = 12 V`, `RC = 2.2 kΩ`, `β = 100`,
`VBE = 0.70 V`. Expected values below were calculated by hand from the Lab 03
equations before running the app, not read from the code.

Tolerance used: `±0.01 mA` for `IC` and `±0.02 V` for `VCE`, compared with the
unrounded hand values. Values on the page are shown with 4 significant digits.

| Case | Mode and inputs | Expected | Observed on page | Method | Status |
|---|---|---|---|---|---|
| A1 · original mode | Divider · `R1 = 100 kΩ`, `R2 = 22 kΩ`, `RE = 1 kΩ` | `IC = 1.2298 mA`, `VCE = 8.0522 V` (same as Lab 02) | `IC = 1.23 mA`, `VCE = 8.052 V`, `✓ MATCH` | OpenCode Browser | PASS |
| A2 · Fixed | Fixed · `RB = 1 MΩ` | `IC = 1.1300 mA`, `VCE = 9.5140 V` | `IC = 1.13 mA`, `VCE = 9.514 V`, `✓ MATCH` | OpenCode Browser | PASS |
| A3 · Emitter | Emitter · `RB = 1 MΩ`, `RE = 1 kΩ` | `IC = 1.0263 mA`, `VCE = 8.7054 V` | `IC = 1.026 mA`, `VCE = 8.705 V`, `✓ MATCH` | OpenCode Browser | PASS |
| A4 · one value changed | Emitter · as A3 with `RE = 2 kΩ` | `IC = 0.9401 mA`, `VCE = 8.0328 V`; `IC` must fall versus A3 | `IC = 940.1 µA`, `VCE = 8.033 V`; lower than A3 | OpenCode Browser | PASS |
| A5 · bad input | Fixed · `RB = 0` | Range message for `RB`, no result from the previous run | `Must be between 1 mΩ and 10 MΩ.`; result table shows `--`, no `MATCH` badge | OpenCode Browser | PASS |

Method notes: all five cases were run in the in-app Chromium browser against
`http://127.0.0.1:5000/`, with the mode loaded from `/?mode=...`, values entered
in the page form, and the "Calculate DC Bias" button clicked. The A1–A4 values
above were read from the results panel after the page reloaded. A5 was read from
the field error and the empty result table after submitting.

Evidence: `docs/lab03-a3-emitter.jpeg` is the full-page capture of A3, showing
the selected mode, `IC = 1.026 mA`, `VCE = 8.705 V`, and the independent
(nodal) column agreeing to `2.2e-13` or better.

Expected values were compared with the page using `±0.01 mA` for `IC` and
`±0.02 V` for `VCE`; all observed values are inside those bands.

## Hand calculations

### A1 — Voltage Divider

```text
VBB = 12 · 22 / (100 + 22) = 2.163934 V
RB  = 100 · 22 / (100 + 22) = 18.032787 kΩ
IB  = (2.163934 − 0.70) / (18032.787 + 101 · 1000) = 12.298 µA
IC  = 100 · 12.298 µA = 1.2298 mA
VE  = 101 · 12.298 µA · 1 kΩ = 1.2421 V
VC  = 12 − 1.2298 mA · 2.2 kΩ = 9.2944 V
VCE = 9.2944 − 1.2421 = 8.0522 V
```

### A2 — Fixed Bias

```text
IB  = (12 − 0.70) / 1 MΩ = 11.30 µA
IC  = 100 · 11.30 µA = 1.130 mA
VC  = 12 − 1.130 mA · 2.2 kΩ = 9.514 V
VE  = 0 V  →  VCE = 9.514 V
```

### A3 — Emitter Bias

```text
IB  = (12 − 0.70) / (1 MΩ + 101 · 1 kΩ) = 11.3 / 1.101 MΩ = 10.263 µA
IC  = 100 · 10.263 µA = 1.0263 mA
IE  = 101 · 10.263 µA = 1.0366 mA
VE  = 1.0366 mA · 1 kΩ = 1.0366 V
VC  = 12 − 1.0263 mA · 2.2 kΩ = 9.7421 V
VCE = 9.7421 − 1.0366 = 8.7054 V
```

### A4 — Emitter with `RE = 2 kΩ`

```text
IB  = 11.3 / (1 MΩ + 101 · 2 kΩ) = 11.3 / 1.202 MΩ = 9.401 µA
IC  = 100 · 9.401 µA = 0.9401 mA
VE  = 101 · 9.401 µA · 2 kΩ = 1.8990 V
VC  = 12 − 0.9401 mA · 2.2 kΩ = 9.9318 V
VCE = 9.9318 − 1.8990 = 8.0328 V
```

Prediction before running A4: raising `RE` raises the emitter degeneration in
the base loop, so `IB` and `IC` fall while `VE` rises. `IC` must be lower than
A3's `1.0263 mA`.

### A5 — `RB = 0`

`0 Ω` is below the accepted `1 mΩ` minimum, so the app must show the resistor
range message next to `RB` and must not display A2's result as the result of
this run.
