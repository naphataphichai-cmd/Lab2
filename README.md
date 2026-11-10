# BJT Common-Emitter DC Bias Calculator

ENG29 2121 lab deliverable. A one-page Flask app that computes the DC operating
point of a voltage-divider-biased common-emitter stage, warns when the bias is
outside the active region, and checks the result against an independent nodal
solve.

## What it does

Enter `VCC, R1, R2, RC, RE, β, VBE`. The app returns:

- `IB, IC, IE` in µA/mA/A
- `VCE, VB, VE, VC` in volts
- `VBB` and `RB` as supporting quantities
- the operating region: `cutoff`, `active`, or `saturation`
- a field-level validation message for bad input
- a side-by-side comparison with the independent calculation

The default example is 12 V, 100 kΩ, 22 kΩ, 2.2 kΩ, 1 kΩ, β = 100, VBE = 0.70 V.
It gives approximately `IB = 12.3 µA`, `IC = 1.23 mA`, and `VCE = 8.052 V`.

## Analytical path

`solver.py` uses the Thévenin equivalent of the base divider:

```text
VBB = VCC · R2 / (R1 + R2)
RB  = R1 · R2 / (R1 + R2)
IB  = (VBB − VBE) / (RB + (β + 1)·RE)
IC  = β · IB
IE  = (β + 1)·IB
VE  = IE · RE
VC  = VCC − IC · RC
VB  = VE + VBE
VCE = VC − VE
```

## Independent cross-check

`crosscheck.py` does not use the Thévenin formulas. It writes the base,
collector, and base-emitter equations in `VB, VE, VC`:

```text
−(1/R1 + 1/R2)·VB − (1/((β+1)·RE))·VE = −VCC/R1
−(β/((β+1)·RE))·VE − (1/RC)·VC        = −VCC/RC
VB − VE                                = VBE
```

It solves the resulting 3×3 system with Gaussian elimination and partial
pivoting. The two paths are compared field by field with a relative tolerance
of `1e-6`; the page shows both columns and the maximum relative difference.

## Region rules

- **Cutoff** — the solved `IB <= 0`. The physical cutoff result is constructed
  by `model.py`: `IB = IC = IE = 0`, `VE = 0`, `VC = VCC`, `VCE = VCC`, and
  `VB` is the unloaded divider voltage. A warning explains that the transistor
  is off.
- **Saturation** — `VCE <= 0.2 V`. Raw values are shown, including a negative
  `VCE` if the model produces one. A warning says the point is not valid for
  amplifier use. Nothing is clamped.
- **Active** — otherwise. A low-base-current note appears when `IB < 1 µA`.

## Validation

Every field is required and must be finite. Accepted ranges:

| Field | Range |
|---|---|
| `VCC` | `0 < VCC <= 100 V` |
| `R1, R2, RC, RE` | `1 mΩ <= R <= 10 MΩ` |
| `β` | `1 < β <= 2000` |
| `VBE` | `0 <= VBE < VCC` |

Invalid input returns the form with the submitted values preserved and the
message next to the field. Non-finite intermediate results are reported as a
normal error instead of a 500.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python -m flask --app app run --port 5000
```

Open <http://127.0.0.1:5000/>.

## Test

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Project structure

```text
app.py                      Flask factory, routes, view building
engineering/
  model.py                  dataclasses, constants, region classification
  solver.py                 analytical Thévenin path
  crosscheck.py             independent nodal path + Gaussian elimination
  evaluate.py               runs both paths and builds the comparison
  validation.py             input parsing and field rules
  compare.py                tolerance comparison
  format.py                 value → (number, unit)
templates/                  base and index pages
static/style.css            lab-sheet styling
tests/                      unit and route tests
docs/superpowers/           approved design and implementation plan
```

## Limitations

No AC analysis, gain, small-signal model, transient simulation, schematic
editor, netlist import, FET support, database, authentication, JavaScript, or
deployment work. `VBE` is a fixed input, not solved from a device model, and
temperature dependence is out of scope.
