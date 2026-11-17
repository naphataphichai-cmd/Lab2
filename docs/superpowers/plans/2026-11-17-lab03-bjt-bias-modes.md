# Lab 03 — Three BJT Bias Modes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Lab 2 Flask app so one page computes the DC operating point for Voltage Divider, Fixed, and single-supply Emitter bias without changing the existing divider results.

**Architecture:** Keep the divider path untouched. Add per-mode input dataclasses and solver/crosscheck functions, dispatch by mode inside `evaluate`, validate only the fields a mode uses, and render a mode-aware form/schematic. Every mode returns the same `OperatingPoint` so the comparison and formatting layers stay shared.

**Tech Stack:** Python 3.12, Flask, Jinja2, pytest.

**Spec:** `C:\Users\B6618070\Downloads\ENG29_2121_Lab03_BJT_Bias_Web_App (1).html` (Lab 03 handout)

## Global Constraints

- Divider mode must return exactly the Lab 2 numbers for the Lab 2 inputs.
- Only DC operating point: no AC, SPICE, load line, bypass capacitors.
- No JavaScript; mode switching re-renders the page with a GET.
- Engineering layer receives ohms and volts only; unit conversion stays in `app.py`.
- Unknown mode is an error, never treated as divider.
- Warn when `IB <= 0` or `VCE <= 0.2 V`; do not solve cutoff/saturation values for the new modes.
- Keep the existing tests passing; new tests cover the new modes.

## Review Focus

- Missing `rb` in Fixed/Emitter must be a field error, not a 500 or `TypeError`.
- `RE = 0` in Fixed must never reach a division by `RE`.
- An unknown `mode` value posted by hand must show an error and no stale result.
- Divider results must not drift when new code paths are added.
- A mode switch must show only that mode's inputs.

---

### Task 1: Mode constants and analytical solvers

**Files:**
- Modify: `engineering/model.py` (add mode constants, `FixedBiasInputs`, `EmitterBiasInputs`)
- Modify: `engineering/solver.py` (add `solve_fixed`, `solve_emitter`)
- Test: `tests/test_modes.py`

**Interfaces:**
- Produces: `model.MODE_FIXED = "fixed"`, `model.MODE_EMITTER = "emitter"`, `model.MODE_DIVIDER = "divider"`, `model.MODE_LABELS: dict[str, str]`
- Produces: `model.FixedBiasInputs(vcc, rb, rc, beta, vbe)`, `model.EmitterBiasInputs(vcc, rb, re, rc, beta, vbe)`
- Produces: `solver.solve_fixed(FixedBiasInputs) -> OperatingPoint`, `solver.solve_emitter(EmitterBiasInputs) -> OperatingPoint`

- [ ] **Step 1: Write failing solver tests (A2, A3, A4 values)**

```python
def test_fixed_bias_a2():
    point = solver.solve_fixed(model.FixedBiasInputs(12.0, 1e6, 2200.0, 100.0, 0.7))
    assert point.ib == pytest.approx(11.3e-6, rel=1e-12)
    assert point.ic == pytest.approx(1.13e-3, rel=1e-12)
    assert point.ve == 0.0
    assert point.vce == pytest.approx(9.514, rel=1e-12)

def test_emitter_bias_a3():
    point = solver.solve_emitter(model.EmitterBiasInputs(12.0, 1e6, 1000.0, 2200.0, 100.0, 0.7))
    assert point.ib == pytest.approx(11.3 / 1.101e6, rel=1e-12)
    assert point.vce == pytest.approx(8.705449591375, rel=1e-9)
```

- [ ] **Step 2: Run and confirm failure**

Run: `.\.venv\Scripts\python -m pytest tests/test_modes.py -q`
Expected: FAIL — missing attributes/functions.

- [ ] **Step 3: Implement**

`FixedBiasInputs`: `ib = (vcc - vbe) / rb`, `ic = beta*ib`, `ie = (beta+1)*ib`, `ve=0`, `vc = vcc - ic*rc`, `vb = vbe`, `vce = vc`, `vbb=0.0`, `rb=rb`.
`EmitterBiasInputs`: `ib = (vcc - vbe) / (rb + (beta+1)*re)`, `ie = (beta+1)*ib`, `ve = ie*re`, `vc = vcc - ic*rc`, `vb = ve + vbe`, `vce = vc - ve`, `vbb=0.0`, `rb=rb`.

- [ ] **Step 4: Run tests** — Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add engineering/model.py engineering/solver.py tests/test_modes.py
git commit -m "feat: add fixed and emitter bias solvers"
```

---

### Task 2: Independent crosscheck for the new modes

**Files:**
- Modify: `engineering/crosscheck.py`
- Test: `tests/test_modes.py`

**Interfaces:**
- Consumes: `crosscheck.gaussian_solve`, model dataclasses from Task 1
- Produces: `crosscheck.solve_fixed(FixedBiasInputs) -> OperatingPoint`, `crosscheck.solve_emitter(EmitterBiasInputs) -> OperatingPoint`

- [ ] **Step 1: Write failing tests** asserting each independent result matches the analytical result field by field (`rel=1e-9`) and that KCL residuals are ~0.

- [ ] **Step 2: Run and confirm failure.**

- [ ] **Step 3: Implement nodal systems**

Fixed, unknowns `VB, VC, IB`:
```text
gb·VB + IB          = gb·VCC
gc·VC + β·IB        = gc·VCC
VB                  = VBE
```
Emitter, unknowns `VB, VE, VC`:
```text
-gb·VB - (ge/(β+1))·VE   = -gb·VCC
-β·ge/(β+1)·VE - gc·VC   = -VCC/RC
VB - VE                   = VBE
```
Then derive `IB`, `IC`, `IE`, `VE`, `VCE` from the node voltages.

- [ ] **Step 4: Run tests** — Expected: PASS.
- [ ] **Step 5: Commit** — `feat: add independent crosscheck for new bias modes`

---

### Task 3: Mode-aware evaluation and display

**Files:**
- Modify: `engineering/evaluate.py`, `engineering/model.py`
- Test: `tests/test_modes.py`

**Interfaces:**
- Produces: `evaluate.evaluate(inputs, mode=model.MODE_DIVIDER) -> Evaluation` accepting any of the three input types.
- `model.display_point(inputs, op, region, mode=model.MODE_DIVIDER)` keeps the divider cutoff construction; other modes return the raw point.

- [ ] **Step 1: Write failing test** that `evaluate.evaluate(fixed, MODE_FIXED)` returns a matched comparison and that a saturated fixed point keeps raw negative/under-0.2 V `VCE` with the saturation warning.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement dispatch** with `if/elif` on mode; raise `ValueError("unknown mode")` for anything else.
- [ ] **Step 4: Run tests** — Expected: PASS, plus the whole existing suite.
- [ ] **Step 5: Commit** — `feat: dispatch evaluation by bias mode`

---

### Task 4: Mode-aware validation

**Files:**
- Modify: `engineering/validation.py`
- Test: `tests/test_modes.py`

**Interfaces:**
- Produces: `validation.parse_mode(raw: str | None) -> tuple[str | None, FieldError | None]`
- Produces: `validation.parse_inputs_for_mode(form, mode) -> tuple[inputs | None, list[FieldError]]`
- `validation.parse_inputs(form)` remains the divider entry point.

- [ ] **Step 1: Write failing tests**: fixed requires `rb` and ignores `r1/r2/re`; emitter requires `rb` and `re`; `rb=0` is a range error; `mode="bogus"` returns an error.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** per-mode field tuples and shared range rules for every resistor field.
- [ ] **Step 4: Run tests** — Expected: PASS.
- [ ] **Step 5: Commit** — `feat: validate inputs per bias mode`

---

### Task 5: Flask route and result view

**Files:**
- Modify: `app.py`
- Test: `tests/test_modes.py`

**Interfaces:**
- `DEFAULT_FORM` gains `"mode": "divider"` and `"rb": "1"`; `DEFAULT_UNITS` gains `"rb": "MΩ"`.
- GET accepts `?mode=<mode>`; POST reads `mode` from the form.
- `_build_view(evaluation, mode)` adds `mode`, `mode_label`, and `show_supporting`.

- [ ] **Step 1: Write failing route tests** for A2 (`Fixed · RB = 1 MΩ` → `1.13 mA`, `9.514 V`), A3 (`Emitter · RB = 1 MΩ, RE = 1 kΩ` → `1.026 mA`, `8.705 V`), A4 (RE 2 kΩ → `0.9401 mA`), A5 (`RB = 0` → range message, no stale result), unknown mode → error message.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** conversion for only the mode's fields, dispatch to `validation.parse_inputs_for_mode` and `evaluate.evaluate`, keep the existing numerical-error guard.
- [ ] **Step 4: Run tests** — Expected: PASS.
- [ ] **Step 5: Commit** — `feat: add circuit mode selection to the Flask route`

---

### Task 6: Mode-aware form and schematic

**Files:**
- Modify: `templates/index.html`, `templates/base.html`, `static/style.css`
- Test: `tests/test_modes.py`

- [ ] **Step 1: Write failing template tests**: GET `/?mode=fixed` shows `RB` and hides `R1`; GET `/?mode=divider` still shows `R1` and `R2`; the result panel names the selected mode.
- [ ] **Step 2: Run and confirm failure.**
- [ ] **Step 3: Implement** a GET mode form, a hidden `mode` field on the POST form, conditional input rows, a schematic that swaps R1→RB and hides R2/RE where the circuit has none, and a supporting block only for divider.
- [ ] **Step 4: Run tests** — Expected: PASS.
- [ ] **Step 5: Commit** — `feat: render mode-specific form and schematic`

---

### Task 7: Documentation and browser acceptance record

**Files:**
- Modify: `README.md`
- Create: `docs/validation.md`

- [ ] **Step 1: Update the README** with the three modes, equations, per-mode validation, run/test commands, and the new file map.
- [ ] **Step 2: Create `docs/validation.md`** with the A1–A5 table, independently calculated expected values, and columns for observed values, method, and status.
- [ ] **Step 3: Run the full suite** — `.\.venv\Scripts\python -m pytest -q` — Expected: all pass.
- [ ] **Step 4: Run the app and execute A1–A5 in a browser,** recording observed values and at least one saved result text.
- [ ] **Step 5: Commit** — `docs: record Lab 03 modes and acceptance results`

## Self-Review Notes

- Divider regression is covered by the existing `tests/test_solver.py`, `tests/test_crosscheck.py`, and `tests/test_routes.py`.
- `combined` cutoff display stays divider-only because Fixed/Emitter cannot reach `IB <= 0` with valid inputs (`VBE < VCC`), matching the handout's allowance to warn instead of solving cutoff.
- No new dependency is added.
