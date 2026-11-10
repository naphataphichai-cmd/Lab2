# BJT Common-Emitter DC Bias Web App — Design

**Course:** ENG29 2121 · **Date:** 2026-11-10 · **Status:** approved

## Intent and why

Students need a small, trustworthy tool that shows the DC operating point of a
voltage-divider-biased Common-Emitter stage. The point of the lab is not the
web page; it is seeing that a closed-form engineering calculation and an
independent network solution agree, and that the tool says "this transistor is
in saturation" instead of quietly printing numbers.

The deliverable is a real Flask application with separated engineering logic,
routes, templates, CSS and tests, runnable on localhost today.

## Goals

1. Compute the DC operating point from `VCC, R1, R2, RC, RE, β, VBE`.
2. Show every result with a unit: `IB, IC, IE, VCE, VB, VE, VC` (plus `VBB`,
   `RB` as supporting quantities).
3. Reject bad input with a specific, actionable message.
4. Classify the operating region (`cutoff`, `active`, `saturation`) and warn
   when the result leaves the active region.
5. Compute the same operating point a second, independent way and show both
   results plus a match/mismatch verdict.
6. Be understandable by a student reading the source in one sitting.

## Non-goals

- No AC analysis, gain, small-signal model, frequency response.
- No transient, no time-domain simulation.
- No schematic editor, no image upload, no netlist import.
- No FET/MOSFET support, no other bias topologies (fixed bias, collector
  feedback, emitter feedback).
- No database, no authentication, no JavaScript, no deployment work.
- No numerical device model (no Shockley diode equation, no temperature
  dependence). `VBE` is an input constant, not solved for.

## Anti-goals

Things that would make this a failure even if it runs:

- A "cross-check" that calls the same function or shares the same algebra.
- Numbers printed without units, or units missing on the comparison table.
- Silent clamping: a saturated result shown without a warning.
- A crash (500) on zero, negative, empty or non-numeric input.
- Tests that only cover the happy path.
- Inputs that produce division by zero anywhere in either solver.

## Constraints

- Python 3.12, Flask, pytest. No NumPy/SciPy — the linear solve is ~30 lines.
- Server-rendered HTML only, one page, one form, no build step.
- Workspace is empty; Python 3.12.7 and pip are present.
- `git` is installed at `C:\Users\B6618070\AppData\Local\Programs\Git\cmd` but
  is not on `PATH`; commands must use the absolute path.
- Floats throughout for the calculation; formatting happens at the edge.

## Approaches considered

**A. Analytical solver + independent nodal solver (chosen).**
`solver.py` solves the base loop analytically via the Thévenin equivalent of
`R1||R2`. `crosscheck.py` ignores Thévenin entirely: it writes the three node
equations (base, collector, emitter) with `VBE` as a fixed source and solves
the resulting 3×3 linear system with Gaussian elimination. Different equations,
different numerics. Costs ~70 extra lines and is exactly what the lab asks for.

**B. Analytical solver + hard-coded expected values in tests only.**
Smallest possible, but the comparison never appears in the app, so the
deliverable misses requirement 5.

**C. One module with two functions.**
Less code, but shared helpers and shared assumptions make the "independence"
claim hollow, and the lab rubric would not be met.

A is chosen because the independent calculation is a stated deliverable, and
the extra cost is bounded and testable.

## The model

Voltage-divider bias with emitter resistor. `VBE` is a fixed input.

Analytical path (`solver.py`):

```
VBB = VCC * R2 / (R1 + R2)          # Thévenin base voltage
RB  = R1 * R2 / (R1 + R2)           # Thévenin base resistance
IB  = (VBB - VBE) / (RB + (β+1)·RE)
IC  = β · IB
IE  = (β+1) · IB
VE  = IE · RE
VC  = VCC - IC · RC
VB  = VE + VBE
VCE = VC - VE
```

Independent path (`crosscheck.py`), unknowns `VB, VE, VC`:

```
(VCC - VB)/R1 - VB/R2 - IB = 0     with IB = IE/(β+1)
IE = VE/RE
(VCC - VC)/RC = IC                 with IC = β·IB
VB - VE = VBE
```

Assembled as `A·x = b` and solved by Gaussian elimination with partial
pivoting. Then `VCE = VC - VE`.

## Region classification

`model.py` owns this, because it is a physical interpretation, not a
calculation, and both paths must classify identically.

Both solvers run their own math first and report the signed `IB` they computed.
Neither may short-circuit to a cutoff answer, so a sign disagreement between
them surfaces as a mismatch instead of being hidden.

- **cutoff** — the solved `IB <= 0` (the base loop cannot supply forward
  current). `model.py`, not the solvers, then constructs the physical cutoff
  result: `IB = IC = IE = 0`, `VC = VCC`, `VE = 0`, `VCE = VCC`, and
  `VB = VCC·R2/(R1+R2)` — the unloaded divider voltage, because with no base
  current the base node floats to the divider tap and `VB − VE = VBE` no longer
  applies. Using the unloaded divider here is not Thévenin algebra; it is the
  statement "no current flows". A warning explains the transistor is off.
- **saturation** — otherwise, if `VCE <= VCE_SAT` with `VCE_SAT = 0.2 V`.
  Numbers are still reported uncorrected, including a negative `VCE` if the
  model produces one; a warning says the operating point is not valid for
  amplifier use. Nothing is clamped or hidden.
- **active** — otherwise. No warning.
- **near-cutoff hint** — `IB < 1 µA` in the active region gets a non-blocking
  note that the bias is very sensitive to `β`.

## Independent comparison

`compare.py` compares the two result objects field by field
(`IB, IC, IE, VCE, VB, VE, VC`) using
`abs(a - b) <= max(1e-12, 1e-6 * max(|a|, |b|))` and returns a verdict plus the
worst relative error. The page shows "Cross-check: MATCH (max rel. error
3.1e-16)" or a red "MISMATCH" banner listing the disagreeing fields.

The comparison table shows **both** solvers' values and their difference, in
units, so the cross-check is visible and not just a badge. The region is
displayed once, taken from the analytical path; if the two paths classify the
region differently that is itself reported as a mismatch, because one of them
is wrong.

Cutoff results are compared too, through the shared `model.py` construction, so
both sides must agree on `IB = IC = IE = 0`, `VB = VBB`, `VE = 0`, `VC = VCC`.

## Validation (`validation.py`)

Every field is required. Returns a list of `{field, message}` errors; the route
re-renders the form with the submitted values preserved and the messages shown
next to the fields.

| Rule | Message intent |
|---|---|
| numeric, finite | "must be a number" |
| `VCC > 0`, `VCC <= 100` | positive, sane lab range |
| `1 mΩ <= R1, R2, RC, RE <= 10 MΩ` | no zero/negative resistances, no overflow |
| `1 < β <= 2000` | realistic transistor range |
| `0 <= VBE < VCC` | base-emitter drop must be below the supply |

`RE > 0` is required so the nodal system stays non-singular. The 1 mΩ floor is
deliberately generous but still prevents `1/R` overflowing to `inf` for absurd
values such as `1e-320`. As a second line of defence, `format.py` refuses to
render a non-finite result: the route turns that into a normal validation error
("inputs are outside the numerically stable range") rather than a 500.

## The page

Single route pair, no JavaScript.

```
┌────────────────────────────────────────────────┐
│  BJT Common-Emitter DC Bias — ENG29 2121       │
├────────────────────────────────────────────────┤
│  VCC [12    ] V     R1 [47000 ] Ω              │
│  R2  [10000 ] Ω     RC [4700  ] Ω              │
│  RE  [1000  ] Ω     β  [150   ]                │
│  VBE [0.7   ] V                                 │
│              [ Calculate ]                      │
├────────────────────────────────────────────────┤
│  REGION: ACTIVE          Cross-check: MATCH     │
│                                                 │
│  Quantity   Analytical   Nodal      Unit        │
│  IB          8.825        8.825      µA          │
│  IC          1.324        1.324      mA          │
│  IE          1.333        1.333      mA          │
│  VCE         4.446        4.446      V           │
│  VB          2.033        2.033      V           │
│  VE          1.333        1.333      V           │
│  VC          5.779        5.779      V           │
│                                                 │
│  Supporting: VBB 2.105 V · RB 8.246 kΩ          │
│  Max relative difference: 4.4e-16               │
└────────────────────────────────────────────────┘
```

Warnings appear as a coloured band above the table. Errors replace the result
pane and keep the user's values in the form. The form pre-fills the example
above on first load so the page is never blank.

## Structure

```
.gitignore
app.py                      # create_app(), GET/POST "/", thin view building
engineering/
  __init__.py
  model.py                  # dataclasses, constants, region classification
  solver.py                 # analytical path
  crosscheck.py             # nodal path + Gaussian elimination
  evaluate.py               # runs both paths, builds the comparison
  validation.py             # input parsing and rules
  compare.py                # tolerance comparison
  format.py                 # value → (number, unit) for display
templates/
  base.html
  index.html                # form + result/warning/error panes
static/
  style.css
tests/
  conftest.py
  test_solver.py
  test_crosscheck.py
  test_region.py
  test_validation.py
  test_compare.py
  test_format.py
  test_routes.py
requirements.txt
README.md
docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md
```

## Testing strategy

- `test_solver.py` — worked example above with hand-computed expected values
  (`IB ≈ 8.824 µA`, `IC ≈ 1.324 mA`, `VCE ≈ 4.447 V`), tol 1e-6 relative; plus
  a cutoff case and a saturation case.
- `test_crosscheck.py` — agreement with the analytical path across a fixed
  table of 6 parameter sets spanning low/high β and small/large `RC`; plus a
  nodal KCL residual test (`< 1e-9`) and a cutoff case where the nodal solve
  must independently produce `IB <= 0`.
- `test_region.py` — boundary behaviour at `IB = 0` and at `VCE = 0.2 V`, the
  cutoff result shape (`VB = VBB`, `VE = 0`, `VC = VCC`), and a test that a
  deliberately corrupted solver result is reported as a region mismatch.
- `test_validation.py` — every rule, including `0`, `-1`, `"abc"`, empty,
  `NaN`, `inf`, `1e-320`, `β = 0`, `VBE = VCC`.
- `test_compare.py` — match, mismatch, zero-valued cutoff comparison, and
  region-mismatch combination.
- `test_format.py` — current/voltage/resistance scaling at unit boundaries,
  zero, negative values, 4-significant-digit rounding, and the non-finite guard.
- `test_routes.py` — `GET /` 200 with form fields; valid `POST` 200 containing
  the region, both solver columns and the match badge; invalid `POST` 200 with
  the error message and preserved values; non-finite guard; no 500s.

Run: `python -m pytest -q` from the project root.

## Delivery today

1. `git init` and commits along the way (small, working increments).
2. `README.md` with install/run/test instructions and the equations.
3. Create the GitHub repository and push. Needs the user's GitHub account:
   no `gh` CLI is installed and no remote exists. Fallback if credentials are
   unavailable: complete local commits and hand over the exact `git remote add`
   + `git push` commands.

## Left to the builder

- Exact CSS (a calm, readable lab-sheet look; system fonts, no framework).
- How many decimal places per unit (decided: 4 significant digits, unit
  auto-scaled to µA/mA and Ω/kΩ/MΩ).
- Whether `VBB`/`RB` are shown in the table or as a footnote (decided:
  footnote under the table, as in the sketch).
- Test fixture formatting.
