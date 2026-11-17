# BJT Common-Emitter DC Bias Calculator — Lab 03

ENG29 2121 lab deliverable. A one-page Flask app that computes the DC operating
point of a common-emitter stage for **three bias circuits**, warns when the bias
is outside the forward-active region, and checks every mode against an
independent nodal solve.

- **Voltage Divider Bias** — unchanged from Lab 02
- **Fixed Bias** — base resistor only
- **Emitter Bias (single supply)** — base and emitter resistors

## Repository

- GitHub: <https://github.com/naphataphichai-cmd/Lab2>
- Lab 03 commit: see the SHA recorded in `docs/validation.md` and in the submission
- How to run and open the app: see [Run](#run)

## What it does

Pick the circuit mode, then enter `VCC, RC, β, VBE` plus the resistors that mode
uses:

| Mode | Extra inputs | Resistor placement |
|---|---|---|
| Fixed Bias | `RB` | `RB` from VCC to base, emitter tied to ground |
| Emitter Bias | `RB, RE` | `RB` from VCC to base, `RE` from emitter to ground |
| Voltage Divider | `R1, R2, RE` | `R1` VCC→base, `R2` base→ground, `RE` emitter→ground |

Each field carries its own unit selector (`Ω` / `kΩ` / `MΩ` for resistors,
`V` / `mV` for voltages), so the circuit can be entered the way it is drawn on
the sheet. The app returns:

- `IB, IC, IE` in µA/mA/A
- `VCE, VB, VE, VC` in volts
- the operating region: `cutoff`, `active`, or `saturation`
- a field-level validation message for bad input
- a side-by-side comparison with the independent calculation

The page shows the input form on the left, a schematic of the selected circuit in
the middle with the entered component values, and the operating point on the
right. Selecting a mode reloads the page immediately with that circuit's fields;
without JavaScript a "Load circuit" button submits the same form. The divider
mode still shows `R1`, `R2`, and `RE` exactly as in Lab 02.

All three modes return the same `model.OperatingPoint` using the Lab 02 field
names (`vb, ve, vc, vce, ib, ic, ie`), so the comparison and formatting layers
stay shared; each function also returns the mode's `rb` value and, for the
divider, `vbb`. Units are fixed by the formatter (volts and A/µA/mA), so every
mode reports values in the same units.

The divider default example is 12 V, 100 kΩ, 22 kΩ, 2.2 kΩ, 1 kΩ, β = 100,
VBE = 0.70 V. It gives approximately `IB = 12.3 µA`, `IC = 1.23 mA`, and
`VCE = 8.052 V` — the same values as Lab 02.

## Analytical path

`engineering/solver.py` keeps the Lab 02 Thévenin divider path and adds one
function per new mode.

Divider (unchanged):

```text
VBB = VCC · R2 / (R1 + R2)
RB  = R1 · R2 / (R1 + R2)
IB  = (VBB − VBE) / (RB + (β + 1)·RE)
```

Fixed:

```text
IB = (VCC − VBE) / RB
VE = 0
```

Emitter (single supply):

```text
IB = (VCC − VBE) / [RB + (β + 1)·RE]
VE = IE · RE
```

Shared output stage:

```text
IC  = β · IB
IE  = (β + 1) · IB
VC  = VCC − IC · RC
VB  = VE + VBE
VCE = VC − VE
```

## Independent cross-check

`engineering/crosscheck.py` does not reuse the closed-form equations. For each
mode it writes the node equations and solves them with Gaussian elimination and
partial pivoting:

- **Divider** — unknowns `VB, VE, VC`:
  ```text
  −(1/R1 + 1/R2)·VB − (1/((β+1)·RE))·VE = −VCC/R1
  −(β/((β+1)·RE))·VE − (1/RC)·VC        = −VCC/RC
  VB − VE                                = VBE
  ```
- **Fixed** — unknowns `VB, VC, IB`:
  ```text
  (1/RB)·VB + IB          = VCC/RB
  (1/RC)·VC + β·IB        = VCC/RC
  VB                      = VBE
  ```
- **Emitter** — unknowns `VB, VE, VC`: the divider base equation with
  `1/R1 + 1/R2` replaced by `1/RB`.

The two paths are compared field by field with a relative tolerance of `1e-6`;
the page shows both columns and the maximum relative difference.

## Region rules

- **Cutoff** — the solved `IB <= 0`. The physical cutoff result is constructed
  by `model.py` for the divider; new modes keep the raw point and show the
  warning. With valid inputs `VBE < VCC`, so Fixed and Emitter cannot reach
  cutoff in this model.
- **Saturation** — `VCE <= 0.2 V`. Raw values are shown, including a negative
  `VCE` if the model produces one. A warning says the point is not valid for
  amplifier use. Nothing is clamped.
- **Active** — otherwise. A low-base-current note appears when `IB < 1 µA`.

## Validation

Only the fields the selected mode uses are required and converted. Every used
field must be finite. The chosen unit is converted to ohms and volts at the edge
of the app, so the engineering layer only ever sees base units. Accepted ranges:

| Field | Range |
|---|---|
| `VCC` | `0 < VCC <= 100 V` |
| `RB, R1, R2, RC, RE` | `1 mΩ <= R <= 10 MΩ` |
| `β` | `1 < β <= 2000` |
| `VBE` | `0 <= VBE < VCC` |

An unknown mode is rejected instead of being treated as divider. Invalid input
returns the form with the submitted values preserved, the message next to the
field, and no previous result. Non-finite intermediate results are reported as a
normal error instead of a 500.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m flask --app app run --port 5000
```

Open <http://127.0.0.1:5000/>. Use `http://127.0.0.1:5000/?mode=fixed` to open
the page directly in Fixed mode (or pick the mode in the page).

## Test

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Project structure

```text
app.py                      Flask factory, mode selection, unit conversion, view building
engineering/
  model.py                  mode names, input dataclasses, region rules, display point
  solver.py                 analytical paths: divider (Thévenin), fixed, emitter
  crosscheck.py             independent nodal paths + Gaussian elimination
  evaluate.py               dispatches by mode and builds the comparison
  validation.py             mode-aware parsing and field rules
  compare.py                tolerance comparison
  format.py                 value → (number, unit)
templates/                  base and index pages
static/style.css            lab-sheet styling
tests/                      unit and route tests
docs/validation.md          Lab 03 A1–A5 acceptance record
docs/superpowers/           approved design and implementation plan
```

## Lab 03 acceptance

`docs/validation.md` holds the A1–A5 table with independently calculated
expected values, the observed browser results, and the method used. All five
cases were run in the in-app browser and passed; `docs/lab03-a3-emitter.jpeg` is
the captured A3 page. The test suite covers the same numbers at the Python and
route level.

## AI assistance disclosure

This Lab 03 extension was built with **OpenCode (AI coding assistant)** working
under my direction. I supplied the Lab 03 handout, chose the three modes and the
constraints (keep the divider results identical to Lab 02, warn instead of
solving cutoff/saturation for the new modes, DC operating point only), and
reviewed every change before committing it. The paragraphs below state exactly
what the AI produced, what I checked, and where the code chooses a mode and
converts units.

### Equations and units used

The engineering layer only ever sees **ohms and volts**. Every mode solves the
same output stage, so `IC = β·IB`, `IE = (β + 1)·IB`, `VC = VCC − IC·RC`,
`VB = VE + VBE`, `VCE = VC − VE` (currents in A, voltages in V, resistances in Ω).

- **Voltage divider** (unchanged Lab 02 path):
  `VBB = VCC·R2/(R1 + R2)`, `RB = R1·R2/(R1 + R2)`,
  `IB = (VBB − VBE)/(RB + (β + 1)·RE)`.
- **Fixed bias:** `IB = (VCC − VBE)/RB`, `VE = 0`, `VCE = VC`.
- **Emitter bias (single supply):** `IB = (VCC − VBE)/(RB + (β + 1)·RE)`,
  `IE = (β + 1)·IB`, `VE = IE·RE`.

Display units are produced by `engineering/format.py`: currents in µA below
1 mA, mA below 1 A, otherwise A; voltages in V; resistances in Ω/kΩ/MΩ. The A1–A5
hand calculations in `docs/validation.md` use the same equations and units.

### What the AI generated

- `engineering/solver.py` — `solve_fixed()` and `solve_emitter()` (the divider
  `solve()` was kept byte-for-byte).
- `engineering/crosscheck.py` — the independent nodal systems for fixed
  (`VB, VC, IB`) and emitter (`VB, VE, VC`) bias, solved with the existing
  `gaussian_solve()`.
- `engineering/evaluate.py` — `_paths()` mode dispatch and the `mode` field on
  `Evaluation`; `engineering/model.py` — mode constants, `FixedBiasInputs`,
  `EmitterBiasInputs`, and the `mode` argument on `display_point()`.
- `engineering/validation.py` — `MODE_FIELDS`, `parse_mode()`,
  `parse_inputs_for_mode()` and the shared range rules.
- `app.py` — `rb` defaults/units, `MODE_CHOICES`, mode-aware conversion and
  routing, the result view, and the `ACCEPTANCE_CASES` data.
- `templates/index.html`, `templates/base.html`, `static/style.css` — mode
  selector, conditional input rows, the SVG schematic per mode, and the
  A1–A5 acceptance table.
- `tests/test_modes.py` and two tests in `tests/test_routes.py` — the new-mode
  solver, crosscheck, validation, route and acceptance-table tests.

### What I verified

I recomputed A1–A5 by hand from the equations above *before* running the app
(see `docs/validation.md`), then ran each case in the browser and compared:
`IC` within ±0.01 mA and `VCE` within ±0.02 V. I confirmed that A4 (`RE = 2 kΩ`)
gives a lower `IC` than A3, that A5 (`RB = 0`) shows the range message with an
empty result table and no `MATCH` badge, that the divider default still returns
the Lab 02 values (`IB = 12.3 µA`, `IC = 1.23 mA`, `VCE = 8.052 V`), that
selecting a mode immediately redraws the correct circuit, and that the printed
schematic matches the mode. I also re-derived the nodal cross-check equations
against the closed-form results and ran the full test suite (113 tests).

### Where mode selection and unit conversion live

- **Mode selection:** the page posts `mode`; `app.py` calls
  `validation.parse_mode()`, which rejects unknown values; `validation.MODE_FIELDS`
  decides which fields are parsed; then `evaluate._paths()` maps the mode to a
  `(solver, crosscheck)` pair with `if/elif` and raises `ValueError` otherwise.
  The template uses a `GET ?mode=` selector with `onchange="this.form.submit()"`,
  a hidden `mode` field on the POST form, and `<noscript>` fallback button.
- **Unit conversion:** `app.py` — `_selected_units()` reads each `*_unit` field,
  `_to_base_units()` multiplies by `UNIT_SCALE` (`Ω`/`kΩ`/`MΩ`,
  `V`/`mV`) using `UNIT_CHOICES`/`DEFAULT_UNITS`, and only the fields the mode
  uses are converted. Nothing is converted back in the engineering layer;
  presentation formatting is `engineering/format.py`.

สรุปภาษาไทย: งาน Lab 3 นี้ใช้ OpenCode เป็นผู้ช่วยเขียนโค้ด โดยนักศึกษาเป็นผู้กำหนด
โจทย์ เงื่อนไข และตรวจทานทุกส่วน ฟังก์ชันที่ AI ช่วยเขียนคือตัวแก้สมการ Fixed/Emitter,
 nodal cross-check, การเลือกโหมดใน `evaluate._paths()`, การตรวจอินพุตตามโหมด,
 ตัวเลือกโหมด/แผนภาพ/ตาราง A1–A5 ในเทมเพลต และชุดเทสต์ นักศึกษาเป็นผู้คำนวณค่า
 คาดหมาย A1–A5 ด้วยมือก่อนรัน ตรวจผลบนหน้าเว็บจริงตามเกณฑ์ ±0.01 mA และ ±0.02 V
 ตรวจว่าโหมด Divider ยังได้ค่าเดิมของ Lab 2 และตรวจสอบว่าการเลือกโหมดเกิดที่
 `validation.parse_mode()` + `evaluate._paths()` และการแปลงหน่วยเกิดที่
 `_selected_units()`/`_to_base_units()` ใน `app.py` ก่อนเข้าชั้นคำนวณ

## Limitations

No AC analysis, gain, small-signal model, transient simulation, schematic
editor, netlist import, FET support, database, authentication, JavaScript, or
deployment work. `VBE` is a fixed input, not solved from a device model, and
temperature dependence is out of scope.
