# BJT Common-Emitter DC Bias Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a one-page Flask app that computes the voltage-divider-biased common-emitter DC operating point, validates inputs, classifies the region, and shows agreement with an independent nodal solve.

**Architecture:** `solver.py` uses the Thévenin base loop. `crosscheck.py` writes three nodal equations and solves a 3×3 system with Gaussian elimination. `evaluate.py` runs both raw paths, lets `model.py` construct the physical cutoff result, and builds a tolerance comparison. Flask renders one server-side page; no JavaScript.

**Tech Stack:** Python 3.12, Flask 3.x, pytest 8.x. No NumPy/SciPy.

**Spec:** `docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md`

## Global Constraints

- Python 3.12; Flask and pytest only; no NumPy/SciPy.
- Server-rendered HTML, one page, one form, no JavaScript, no build step.
- `git` is at `C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe` and is not on `PATH`; use the absolute path.
- Floats throughout; formatting happens only at the display edge.
- Every displayed result carries a unit.
- Invalid input returns HTTP 200 with field errors and preserves submitted values; no 500s.
- Working directory: `C:\Users\B6618070\Documents\Default Project`.
- Run tests with `.venv\Scripts\python -m pytest -q` from the project root.

## Review Focus

1. Non-numeric, empty, `NaN`, and `inf` input must produce a specific field error, not a 500.
2. Zero, negative, and sub-milliohm resistance must be rejected; no division by zero or overflow in either solver.
3. Cutoff (`VBB < VBE`) must not short-circuit inside either solver: both report signed raw `IB`, and `model.py` builds the physical cutoff result.
4. Saturation, including negative raw `VCE`, must show raw values plus a warning; nothing is clamped.
5. A non-finite intermediate must be refused by the formatter and shown as a normal validation error, not a 500.

---

### Task 1: Scaffold, app factory, and GET page

**Files:**
- Create: `.gitignore`, `requirements.txt`, `engineering/__init__.py`, `app.py`, `templates/base.html`, `templates/index.html`, `static/style.css`, `tests/conftest.py`, `tests/test_routes.py`

**Interfaces:**
- Produces: `app.create_app() -> Flask`, `app.DEFAULT_FORM: dict[str, str]`, Flask endpoint `index_get` at `GET /`.
- `DEFAULT_FORM` keys: `vcc`, `r1`, `r2`, `rc`, `re`, `beta`, `vbe`.

- [ ] **Step 1: Create the virtual environment and install dependencies**

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install "Flask>=3.0,<4" "pytest>=8,<9"
```

- [ ] **Step 2: Write the failing GET test**

`tests/conftest.py`:

```python
import pytest

from app import DEFAULT_FORM, create_app


@pytest.fixture
def client():
    app = create_app()
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client


@pytest.fixture
def valid_form():
    return dict(DEFAULT_FORM)
```

`tests/test_routes.py`:

```python
def test_get_page_shows_default_form(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "BJT Common-Emitter DC Bias" in body
    assert 'name="vcc"' in body
    assert 'value="47000"' in body
    assert "Calculate" in body
```

- [ ] **Step 3: Run the test and confirm it fails**

Run: `.venv\Scripts\python -m pytest tests/test_routes.py::test_get_page_shows_default_form -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app'`.

- [ ] **Step 4: Create the scaffold**

`.gitignore`:

```gitignore
.venv/
__pycache__/
.pytest_cache/
*.pyc
```

`requirements.txt`:

```text
Flask>=3.0,<4
pytest>=8,<9
```

`engineering/__init__.py`: empty file.

`app.py`:

```python
from flask import Flask, render_template

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index_get():
        return render_template(
            "index.html",
            values=DEFAULT_FORM,
            errors={},
            form_error=None,
            result=None,
        )

    return app


app = create_app()
```

`templates/base.html`:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>BJT Common-Emitter DC Bias</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <main class="sheet">
    {% block content %}{% endblock %}
  </main>
</body>
</html>
```

`templates/index.html`:

```html
{% extends "base.html" %}

{% macro field(name, label, unit, values, errors) %}
<label class="field">
  <span class="field-label">{{ label }}</span>
  <span class="field-input">
    <input name="{{ name }}" value="{{ values.get(name, '') }}" inputmode="decimal" autocomplete="off">
    <span class="unit">{{ unit }}</span>
  </span>
  {% if errors.get(name) %}<span class="error">{{ errors.get(name) }}</span>{% endif %}
</label>
{% endmacro %}

{% block content %}
<header>
  <h1>BJT Common-Emitter DC Bias</h1>
  <p class="course">ENG29 2121 · voltage-divider bias</p>
</header>

<form method="post" action="/" novalidate>
  <div class="grid">
    {{ field("vcc", "VCC", "V", values, errors) }}
    {{ field("r1", "R1", "Ω", values, errors) }}
    {{ field("r2", "R2", "Ω", values, errors) }}
    {{ field("rc", "RC", "Ω", values, errors) }}
    {{ field("re", "RE", "Ω", values, errors) }}
    {{ field("beta", "β", "", values, errors) }}
    {{ field("vbe", "VBE", "V", values, errors) }}
  </div>
  {% if form_error %}<p class="form-error">{{ form_error }}</p>{% endif %}
  <button type="submit">Calculate</button>
</form>
{% endblock %}
```

`static/style.css`:

```css
:root {
  color-scheme: light;
  --ink: #17212b;
  --muted: #5d6b7a;
  --line: #d7dee6;
  --paper: #ffffff;
  --wash: #f3f6f9;
  --accent: #1f5f8b;
  --good: #1d6b45;
  --bad: #a32a2a;
  --warn: #8a5a00;
}

* { box-sizing: border-box; }

body {
  margin: 0;
  padding: 2rem 1rem;
  background: var(--wash);
  color: var(--ink);
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
}

.sheet {
  max-width: 760px;
  margin: 0 auto;
  padding: 2rem;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 10px;
}

h1 { margin: 0; font-size: 1.45rem; }
.course { margin: .2rem 0 1.6rem; color: var(--muted); }

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 1rem;
}

.field { display: flex; flex-direction: column; gap: .25rem; }
.field-label { font-weight: 600; }
.field-input { display: flex; align-items: center; gap: .4rem; }

input {
  width: 100%;
  padding: .5rem .6rem;
  border: 1px solid var(--line);
  border-radius: 6px;
  font: inherit;
  font-variant-numeric: tabular-nums;
}

input:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.unit { color: var(--muted); min-width: 1.5rem; }
.error { color: var(--bad); font-size: .85rem; }

button {
  margin-top: 1.4rem;
  padding: .6rem 1.2rem;
  border: 0;
  border-radius: 6px;
  background: var(--accent);
  color: #fff;
  font: inherit;
  font-weight: 600;
  cursor: pointer;
}

@media (max-width: 560px) {
  .sheet { padding: 1.2rem; }
  .grid { grid-template-columns: 1fr; }
}
```

- [ ] **Step 5: Run the test and confirm it passes**

Run: `.venv\Scripts\python -m pytest tests/test_routes.py::test_get_page_shows_default_form -v`
Expected: PASS.

- [ ] **Step 6: Initialise git and commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" init
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add .
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: scaffold Flask app with default bias form"
```

---

### Task 2: Model dataclasses and region classification

**Files:**
- Create: `engineering/model.py`, `tests/test_region.py`

**Interfaces:**
- Produces:
  - `model.VCE_SAT: float = 0.2`
  - `model.REGION_CUTOFF = "cutoff"`, `model.REGION_ACTIVE = "active"`, `model.REGION_SATURATION = "saturation"`
  - `model.BiasInputs(vcc, r1, r2, rc, re, beta, vbe)`
  - `model.OperatingPoint(ib, ic, ie, vce, vb, ve, vc, vbb, rb)`
  - `model.Region(name: str, warning: str | None)`
  - `model.base_voltage(inputs: BiasInputs) -> float`
  - `model.base_resistance(inputs: BiasInputs) -> float`
  - `model.classify(op: OperatingPoint) -> Region`
  - `model.cutoff_point(inputs: BiasInputs) -> OperatingPoint`
  - `model.display_point(inputs: BiasInputs, op: OperatingPoint, region: Region) -> OperatingPoint`
- Consumes: nothing.

- [ ] **Step 1: Write the failing region tests**

`tests/test_region.py`:

```python
import pytest

from engineering import model


def _op(ib=1e-3, vce=5.0):
    return model.OperatingPoint(
        ib=ib, ic=ib * 100, ie=ib * 101, vce=vce,
        vb=2.0, ve=1.0, vc=1.0 + vce, vbb=2.1, rb=8000.0,
    )


def _inputs():
    return model.BiasInputs(
        vcc=12.0, r1=47000.0, r2=10000.0, rc=4700.0, re=1000.0,
        beta=150.0, vbe=0.7,
    )


def test_cutoff_when_ib_zero():
    assert model.classify(_op(ib=0.0)).name == model.REGION_CUTOFF


def test_cutoff_when_ib_negative():
    assert model.classify(_op(ib=-1e-6)).name == model.REGION_CUTOFF


def test_active_above_saturation_and_above_hint():
    region = model.classify(_op(ib=1e-3, vce=5.0))
    assert region.name == model.REGION_ACTIVE
    assert region.warning is None


def test_saturation_at_boundary():
    region = model.classify(_op(ib=1e-3, vce=0.2))
    assert region.name == model.REGION_SATURATION
    assert "saturation" in region.warning.lower()


def test_active_just_above_saturation_boundary():
    assert model.classify(_op(ib=1e-3, vce=0.2001)).name == model.REGION_ACTIVE


def test_near_cutoff_hint():
    region = model.classify(_op(ib=5e-7, vce=5.0))
    assert region.name == model.REGION_ACTIVE
    assert region.warning is not None
    assert "β" in region.warning


def test_base_quantities_worked_example():
    inputs = _inputs()
    assert model.base_voltage(inputs) == pytest.approx(2.1052631578947367, rel=1e-12)
    assert model.base_resistance(inputs) == pytest.approx(8245.614035087719, rel=1e-12)


def test_cutoff_point_shape():
    inputs = _inputs()
    point = model.cutoff_point(inputs)
    assert point.ib == point.ic == point.ie == 0.0
    assert point.ve == 0.0
    assert point.vc == inputs.vcc
    assert point.vce == inputs.vcc
    assert point.vb == pytest.approx(model.base_voltage(inputs))


def test_display_point_replaces_only_cutoff():
    inputs = _inputs()
    raw = _op(ib=-1e-6, vce=5.0)
    region = model.classify(raw)
    displayed = model.display_point(inputs, raw, region)
    assert displayed.ib == 0.0
    assert displayed.vb == pytest.approx(model.base_voltage(inputs))

    active = _op(ib=1e-3, vce=5.0)
    assert model.display_point(inputs, active, model.classify(active)) is active
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_region.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engineering.model'`.

- [ ] **Step 3: Implement `engineering/model.py`**

Use frozen dataclasses. `classify` checks `op.ib <= 0` first, then `op.vce <= VCE_SAT`, then the near-cutoff hint `op.ib < 1e-6`. `cutoff_point` sets `ib=ic=ie=0`, `ve=0`, `vc=vcc`, `vce=vcc`, `vb=base_voltage(inputs)`, and carries `vbb`/`rb`. `display_point` returns `cutoff_point(inputs)` for cutoff and the raw point otherwise.

Exact warning strings:

```text
cutoff:       The transistor is in cutoff: the base loop cannot supply forward current.
saturation:   The transistor is in saturation (VCE ≤ 0.2 V); this operating point is not valid for amplifier use.
near-cutoff:  Very low base current (IB < 1 µA): the bias is very sensitive to β.
```

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_region.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add engineering/model.py tests/test_region.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add bias model and region classification"
```

---

### Task 3: Analytical solver

**Files:**
- Create: `engineering/solver.py`, `tests/test_solver.py`

**Interfaces:**
- Consumes: `model.BiasInputs`, `model.OperatingPoint`, `model.base_voltage`, `model.base_resistance`.
- Produces: `solver.solve(inputs: BiasInputs) -> OperatingPoint` (raw; no cutoff short-circuit).

- [ ] **Step 1: Write the failing solver tests**

`tests/test_solver.py`:

```python
import pytest

from engineering import model, solver


def _inputs(**overrides):
    values = dict(
        vcc=12.0, r1=47000.0, r2=10000.0, rc=4700.0, re=1000.0,
        beta=150.0, vbe=0.7,
    )
    values.update(overrides)
    return model.BiasInputs(**values)


def test_worked_example_matches_hand_calculation():
    point = solver.solve(_inputs())
    assert point.vbb == pytest.approx(2.1052631578947367, rel=1e-12)
    assert point.rb == pytest.approx(8245.614035087719, rel=1e-12)
    assert point.ib == pytest.approx(8.824501487275532e-06, rel=1e-12)
    assert point.ic == pytest.approx(0.0013236752230913297, rel=1e-12)
    assert point.ie == pytest.approx(0.0013324997245786052, rel=1e-12)
    assert point.ve == pytest.approx(1.3324997245786052, rel=1e-12)
    assert point.vc == pytest.approx(5.77872645147075, rel=1e-12)
    assert point.vb == pytest.approx(2.0324997245786052, rel=1e-12)
    assert point.vce == pytest.approx(4.446226726892145, rel=1e-12)


def test_cutoff_is_not_short_circuited():
    point = solver.solve(_inputs(r2=1000.0))
    assert point.ib < 0.0
    assert point.ic < 0.0
    assert point.ie < 0.0


def test_saturation_reports_raw_values():
    point = solver.solve(_inputs(rc=10000.0))
    assert point.ib > 0.0
    assert point.vce < 0.2
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_solver.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engineering.solver'`.

- [ ] **Step 3: Implement `engineering/solver.py`**

Implement the equations from the spec exactly. Do not branch on cutoff or saturation; always return the signed raw point.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_solver.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add engineering/solver.py tests/test_solver.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add analytical Thevenin solver"
```

---

### Task 4: Independent nodal solver

**Files:**
- Create: `engineering/crosscheck.py`, `tests/test_crosscheck.py`

**Interfaces:**
- Consumes: `model.BiasInputs`, `model.OperatingPoint`, `model.base_voltage`, `model.base_resistance`.
- Produces:
  - `crosscheck.gaussian_solve(matrix: list[list[float]], rhs: list[float]) -> list[float]`
  - `crosscheck.solve(inputs: BiasInputs) -> OperatingPoint` (raw; no cutoff short-circuit).

- [ ] **Step 1: Write the failing cross-check tests**

`tests/test_crosscheck.py`:

```python
import pytest

from engineering import crosscheck, model, solver

PARAMETER_SETS = [
    (12.0, 47000.0, 10000.0, 4700.0, 1000.0, 150.0, 0.7),
    (12.0, 100000.0, 22000.0, 3300.0, 470.0, 100.0, 0.7),
    (9.0, 33000.0, 6800.0, 2200.0, 680.0, 300.0, 0.65),
    (15.0, 68000.0, 15000.0, 5600.0, 1200.0, 50.0, 0.7),
    (5.0, 22000.0, 4700.0, 1000.0, 220.0, 800.0, 0.6),
    (20.0, 120000.0, 33000.0, 10000.0, 2200.0, 200.0, 0.7),
]


def _inputs(values):
    return model.BiasInputs(*values)


def _op(ib=-1e-6, vce=5.0):
    return model.OperatingPoint(
        ib=ib, ic=ib * 100, ie=ib * 101, vce=vce,
        vb=2.0, ve=1.0, vc=1.0 + vce, vbb=2.1, rb=8000.0,
    )


def test_gaussian_solve_known_system():
    matrix = [[2.0, 1.0, -1.0], [-3.0, -1.0, 2.0], [-2.0, 1.0, 2.0]]
    rhs = [8.0, -11.0, -3.0]
    assert crosscheck.gaussian_solve(matrix, rhs) == pytest.approx([2.0, 3.0, -1.0])


@pytest.mark.parametrize("values", PARAMETER_SETS)
def test_matches_analytical_across_parameter_sets(values):
    inputs = _inputs(values)
    analytical = solver.solve(inputs)
    independent = crosscheck.solve(inputs)
    for field in ("ib", "ic", "ie", "vce", "vb", "ve", "vc"):
        assert getattr(independent, field) == pytest.approx(getattr(analytical, field), rel=1e-9)


def test_nodal_kcl_residuals():
    inputs = _inputs(PARAMETER_SETS[0])
    point = crosscheck.solve(inputs)
    base = (inputs.vcc - point.vb) / inputs.r1 - point.vb / inputs.r2 - point.ib
    collector = (inputs.vcc - point.vc) / inputs.rc - point.ic
    vbe = point.vb - point.ve - inputs.vbe
    assert abs(base) < 1e-9
    assert abs(collector) < 1e-9
    assert abs(vbe) < 1e-9


def test_cutoff_signed_ib_is_not_short_circuited():
    inputs = _inputs((12.0, 47000.0, 1000.0, 4700.0, 1000.0, 150.0, 0.7))
    point = crosscheck.solve(inputs)
    assert point.ib < 0.0
    assert point.ic < 0.0
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_crosscheck.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engineering.crosscheck'`.

- [ ] **Step 3: Implement `engineering/crosscheck.py`**

Build the linear system in `VB, VE, VC`:

```text
-(1/R1 + 1/R2)·VB - (1/((β+1)·RE))·VE                         = -VCC/R1
-(β/((β+1)·RE))·VE - (1/RC)·VC                                = -VCC/RC
VB - VE                                                        = VBE
```

Solve with Gaussian elimination and partial pivoting. Reject a pivot with `abs < 1e-15` by raising `ValueError("singular system")`. Then compute `IB = VE/((β+1)·RE)`, `IC = β·IB`, `IE = VE/RE`, `VCE = VC - VE`, and carry `VBB`/`RB`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_crosscheck.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add engineering/crosscheck.py tests/test_crosscheck.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add independent nodal cross-check solver"
```

---

### Task 5: Tolerance comparison

**Files:**
- Create: `engineering/compare.py`, `tests/test_compare.py`

**Interfaces:**
- Consumes: `model.OperatingPoint`.
- Produces:
  - `compare.Comparison(match: bool, max_rel_error: float, mismatches: tuple[str, ...])`
  - `compare.compare(a: OperatingPoint, b: OperatingPoint) -> Comparison`
  - `compare.combine(*comparisons: Comparison, region_a: str, region_b: str) -> Comparison`

- [ ] **Step 1: Write the failing comparison tests**

`tests/test_compare.py`:

```python
from engineering import compare, model


def _op(**overrides):
    values = dict(
        ib=8.824501487275532e-06,
        ic=0.0013236752230913297,
        ie=0.0013324997245786052,
        vce=4.446226726892145,
        vb=2.0324997245786052,
        ve=1.3324997245786052,
        vc=5.77872645147075,
        vbb=2.1052631578947367,
        rb=8245.614035087719,
    )
    values.update(overrides)
    return model.OperatingPoint(**values)


def test_identical_points_match():
    result = compare.compare(_op(), _op())
    assert result.match is True
    assert result.max_rel_error == 0.0
    assert result.mismatches == ()


def test_tiny_relative_difference_matches():
    result = compare.compare(_op(), _op(ic=0.0013236752230913297 * (1.0 + 1e-7)))
    assert result.match is True


def test_large_difference_is_a_mismatch():
    result = compare.compare(_op(), _op(ic=0.002))
    assert result.match is False
    assert "ic" in result.mismatches
    assert result.max_rel_error > 1e-6


def test_zero_valued_cutoff_points_match():
    zero = _op(ib=0.0, ic=0.0, ie=0.0)
    assert compare.compare(zero, zero).match is True


def test_zero_versus_nonzero_is_a_mismatch():
    result = compare.compare(_op(ib=0.0), _op())
    assert result.match is False
    assert "ib" in result.mismatches


def test_combine_reports_region_mismatch():
    same = compare.compare(_op(), _op())
    result = compare.combine(same, same, region_a="active", region_b="cutoff")
    assert result.match is False
    assert "region" in result.mismatches


def test_combine_unions_numeric_mismatches():
    good = compare.compare(_op(), _op())
    bad = compare.compare(_op(), _op(ic=0.002))
    result = compare.combine(good, bad, region_a="active", region_b="active")
    assert result.match is False
    assert "ic" in result.mismatches
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_compare.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engineering.compare'`.

- [ ] **Step 3: Implement `engineering/compare.py`**

Compare fields `ib, ic, ie, vce, vb, ve, vc` with
`abs(a - b) <= max(1e-12, 1e-6 * max(abs(a), abs(b)))`.
Track the worst relative error (`0.0` when both are zero; `inf` for non-finite).
`combine` unions mismatches, takes the maximum error, and appends `"region"` when the two region names differ.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_compare.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add engineering/compare.py tests/test_compare.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: add tolerance comparison and region mismatch reporting"
```

---

### Task 6: Input validation

**Files:**
- Create: `engineering/validation.py`, `tests/test_validation.py`

**Interfaces:**
- Consumes: `model.BiasInputs`.
- Produces:
  - `validation.FieldError(field: str, message: str)`
  - `validation.REQUIRED_FIELDS: tuple[str, ...]`
  - `validation.parse_inputs(form: Mapping[str, str]) -> tuple[BiasInputs | None, list[FieldError]]`

- [ ] **Step 1: Write the failing validation tests**

`tests/test_validation.py`:

```python
import pytest

from engineering import model, validation

VALID = {
    "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
    "re": "1000", "beta": "150", "vbe": "0.7",
}


def _errors(form):
    _, errors = validation.parse_inputs(form)
    return {error.field: error.message for error in errors}


def test_valid_form_parses():
    inputs, errors = validation.parse_inputs(VALID)
    assert errors == []
    assert inputs == model.BiasInputs(12.0, 47000.0, 10000.0, 4700.0, 1000.0, 150.0, 0.7)


@pytest.mark.parametrize("field", validation.REQUIRED_FIELDS)
def test_every_field_is_required(field):
    form = dict(VALID)
    form[field] = ""
    assert _errors(form)[field] == "Required."


@pytest.mark.parametrize("value", ["abc", "1,2", "0x10"])
def test_non_numeric_is_rejected(value):
    form = dict(VALID)
    form["r1"] = value
    assert _errors(form)["r1"] == "Must be a number."


@pytest.mark.parametrize("value", ["NaN", "inf", "-inf"])
def test_non_finite_is_rejected(value):
    form = dict(VALID)
    form["beta"] = value
    assert _errors(form)["beta"] == "Must be a finite number."


@pytest.mark.parametrize("value", ["0", "-1", "100.1"])
def test_vcc_range(value):
    form = dict(VALID)
    form["vcc"] = value
    assert "vcc" in _errors(form)


@pytest.mark.parametrize("value", ["0", "-1", "0.0009", "10000001"])
def test_resistance_range(value):
    form = dict(VALID)
    form["r1"] = value
    assert _errors(form)["r1"] == "Must be between 1 mΩ and 10 MΩ."


@pytest.mark.parametrize("value", ["0", "1", "2001"])
def test_beta_range(value):
    form = dict(VALID)
    form["beta"] = value
    assert "beta" in _errors(form)


def test_vbe_negative_is_rejected():
    form = dict(VALID)
    form["vbe"] = "-1"
    assert _errors(form)["vbe"] == "Must be 0 V or more."


def test_vbe_must_be_below_vcc():
    form = dict(VALID)
    form["vbe"] = "12"
    assert _errors(form)["vbe"] == "Must be less than VCC."


def test_tiny_resistance_is_rejected_before_overflow():
    form = dict(VALID)
    form["r1"] = "1e-320"
    assert _errors(form)["r1"] == "Must be between 1 mΩ and 10 MΩ."


def test_boundary_values_are_accepted():
    form = dict(VALID, vcc="100", r1="0.001", r2="10000000", rc="0.001", re="0.001", beta="2000", vbe="0")
    inputs, errors = validation.parse_inputs(form)
    assert errors == []
    assert inputs is not None
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_validation.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engineering.validation'`.

- [ ] **Step 3: Implement `engineering/validation.py`**

Strip each value. Report `Required.` for empty, `Must be a number.` for a failed `float()`, and `Must be a finite number.` for non-finite values. Apply range rules only to fields that parsed:

| Field | Rule | Message |
|---|---|---|
| `vcc` | `0 < VCC <= 100` | `Must be greater than 0 and at most 100 V.` |
| `r1,r2,rc,re` | `1e-3 <= R <= 10e6` | `Must be between 1 mΩ and 10 MΩ.` |
| `beta` | `1 < β <= 2000` | `Must be greater than 1 and at most 2000.` |
| `vbe` | `0 <= VBE` | `Must be 0 V or more.` |
| `vbe` | `VBE < VCC` when `VCC` parsed | `Must be less than VCC.` |

Return `(None, errors)` if any error; otherwise `(BiasInputs(...), [])`.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_validation.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add engineering/validation.py tests/test_validation.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: validate bias inputs with field-level errors"
```

---

### Task 7: Display formatting

**Files:**
- Create: `engineering/format.py`, `tests/test_format.py`

**Interfaces:**
- Produces:
  - `format.format_current(amps: float) -> tuple[str, str]`
  - `format.format_voltage(volts: float) -> tuple[str, str]`
  - `format.format_resistance(ohms: float) -> tuple[str, str]`
  - `format.format_error(value: float) -> str`
- Non-finite input raises `ValueError`.

- [ ] **Step 1: Write the failing formatting tests**

`tests/test_format.py`:

```python
import pytest

from engineering import format as fmt


def test_current_scaling():
    assert fmt.format_current(8.824501487e-6) == ("8.825", "µA")
    assert fmt.format_current(1.323675223e-3) == ("1.324", "mA")
    assert fmt.format_current(1.5) == ("1.5", "A")
    assert fmt.format_current(0.0) == ("0", "µA")
    assert fmt.format_current(-1.323675223e-3) == ("-1.324", "mA")


def test_voltage_scaling():
    assert fmt.format_voltage(4.4462267) == ("4.446", "V")
    assert fmt.format_voltage(-0.5) == ("-0.5", "V")


def test_resistance_scaling():
    assert fmt.format_resistance(8245.614035) == ("8.246", "kΩ")
    assert fmt.format_resistance(47000.0) == ("47", "kΩ")
    assert fmt.format_resistance(1e6) == ("1", "MΩ")
    assert fmt.format_resistance(0.5) == ("0.5", "Ω")


def test_error_formatting():
    assert fmt.format_error(4.4e-16) == "4.4e-16"
    assert fmt.format_error(0.0) == "0.0e+00"
    assert fmt.format_error(float("inf")) == "inf"


@pytest.mark.parametrize("value", [float("inf"), float("-inf"), float("nan")])
def test_non_finite_is_refused(value):
    with pytest.raises(ValueError):
        fmt.format_current(value)
    with pytest.raises(ValueError):
        fmt.format_voltage(value)
    with pytest.raises(ValueError):
        fmt.format_resistance(value)
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_format.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engineering.format'`.

- [ ] **Step 3: Implement `engineering/format.py`**

Use 4 significant digits (`:.4g`). Current: `< 1 mA` → µA, `< 1 A` → mA, otherwise A. Resistance: `>= 1 MΩ` → MΩ, `>= 1 kΩ` → kΩ, otherwise Ω. Voltage always V. Reject non-finite values with `ValueError`. `format_error` returns `"inf"` for non-finite and `f"{value:.1e}"` otherwise.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_format.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add engineering/format.py tests/test_format.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: format engineering values with units"
```

---

### Task 8: Evaluation orchestration

**Files:**
- Create: `engineering/evaluate.py`
- Modify: `tests/test_region.py` (append the evaluation tests)

**Interfaces:**
- Consumes: `solver.solve`, `crosscheck.solve`, `model.classify`, `model.display_point`, `compare.compare`, `compare.combine`.
- Produces:
  - `evaluate.Evaluation(inputs, analytical_raw, independent_raw, analytical, independent, region, comparison)`
  - `evaluate.evaluate(inputs: BiasInputs) -> Evaluation`

- [ ] **Step 1: Write the failing evaluation tests**

Append to `tests/test_region.py`:

```python
from engineering import compare, evaluate, solver


def _worked_inputs():
    return model.BiasInputs(
        vcc=12.0, r1=47000.0, r2=10000.0, rc=4700.0, re=1000.0,
        beta=150.0, vbe=0.7,
    )


def test_evaluate_matches_for_worked_example():
    evaluation = evaluate.evaluate(_worked_inputs())
    assert evaluation.region.name == model.REGION_ACTIVE
    assert evaluation.comparison.match is True


def test_evaluate_builds_physical_cutoff_result():
    inputs = model.BiasInputs(
        vcc=12.0, r1=47000.0, r2=1000.0, rc=4700.0, re=1000.0,
        beta=150.0, vbe=0.7,
    )
    evaluation = evaluate.evaluate(inputs)
    assert evaluation.region.name == model.REGION_CUTOFF
    assert evaluation.analytical.ib == 0.0
    assert evaluation.independent.ib == 0.0
    assert evaluation.analytical.vb == pytest.approx(model.base_voltage(inputs))
    assert evaluation.analytical.vce == inputs.vcc


def test_evaluate_reports_region_mismatch(monkeypatch):
    fake = model.OperatingPoint(
        ib=-1e-3, ic=-1e-1, ie=-1.01e-1, vce=5.0,
        vb=2.0, ve=1.0, vc=6.0, vbb=2.1, rb=8000.0,
    )
    monkeypatch.setattr("engineering.evaluate.solver.solve", lambda inputs: fake)
    evaluation = evaluate.evaluate(_worked_inputs())
    assert evaluation.region.name == model.REGION_CUTOFF
    assert evaluation.comparison.match is False
    assert "region" in evaluation.comparison.mismatches
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_region.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'engineering.evaluate'`.

- [ ] **Step 3: Implement `engineering/evaluate.py`**

Run both solvers without branches. Classify each raw result. Build display points with `model.display_point`. Compare raw results and display results, then combine with both region names. Store `region` from the analytical path.

- [ ] **Step 4: Run the tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_region.py -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add engineering/evaluate.py tests/test_region.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: orchestrate both solvers and comparison"
```

---

### Task 9: POST route and result page

**Files:**
- Modify: `app.py`, `templates/index.html`, `static/style.css`
- Modify: `tests/test_routes.py` (append route tests)

**Interfaces:**
- Consumes: `validation.parse_inputs`, `evaluate.evaluate`, `format.format_current/format_voltage/format_resistance/format_error`.
- Produces: `POST /` endpoint `index_post`; `app._build_view(evaluation) -> dict`.

- [ ] **Step 1: Write the failing route tests**

Append to `tests/test_routes.py`:

```python
import app as app_module


def test_valid_post_shows_operating_point(client, valid_form):
    response = client.post("/", data=valid_form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "REGION: ACTIVE" in body
    assert "MATCH" in body
    assert "8.825 µA" in body
    assert "1.324 mA" in body
    assert "4.446 V" in body
    assert "Analytical" in body
    assert "Nodal" in body
    assert "VBB" in body
    assert "RB" in body


def test_invalid_number_preserves_value(client, valid_form):
    form = dict(valid_form, r1="abc")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Must be a number." in body
    assert 'value="abc"' in body


def test_empty_field_is_required(client, valid_form):
    form = dict(valid_form, vcc="")
    response = client.post("/", data=form)
    assert response.status_code == 200
    assert "Required." in response.get_data(as_text=True)


def test_zero_resistance_is_rejected(client, valid_form):
    form = dict(valid_form, r1="0")
    response = client.post("/", data=form)
    assert response.status_code == 200
    assert "Must be between 1 mΩ and 10 MΩ." in response.get_data(as_text=True)


def test_vbe_must_be_below_vcc(client, valid_form):
    form = dict(valid_form, vbe="12")
    response = client.post("/", data=form)
    assert response.status_code == 200
    assert "Must be less than VCC." in response.get_data(as_text=True)


def test_cutoff_is_reported(client, valid_form):
    form = dict(valid_form, r2="1000")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "REGION: CUTOFF" in body
    assert "cutoff" in body.lower()
    assert "0 µA" in body


def test_saturation_is_reported(client, valid_form):
    form = dict(valid_form, rc="10000")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "REGION: SATURATION" in body
    assert "not valid for amplifier use" in body


def test_non_finite_result_is_a_normal_error(client, valid_form, monkeypatch):
    def blow_up(evaluation):
        raise ValueError("non-finite")

    monkeypatch.setattr(app_module, "_build_view", blow_up)
    response = client.post("/", data=valid_form)
    assert response.status_code == 200
    assert "outside the numerically stable range" in response.get_data(as_text=True)


def test_extreme_valid_input_does_not_500(client, valid_form):
    form = dict(
        valid_form,
        vcc="100", r1="0.001", r2="0.001", rc="0.001", re="0.001",
        beta="2000", vbe="0",
    )
    response = client.post("/", data=form)
    assert response.status_code == 200
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `.venv\Scripts\python -m pytest tests/test_routes.py -v`
Expected: FAIL (POST returns 405, so the new tests fail).

- [ ] **Step 3: Implement the POST route and result view**

In `app.py`, import `evaluate`, `format`, and `validation`. Add `_build_view(evaluation)` and `@app.post("/")`.

`_build_view` builds rows for `IB, IC, IE` (current) and `VCE, VB, VE, VC` (voltage). Each row has `symbol`, `analytical`, `independent`, and `delta`, with units in every cell. Add `region`, `comparison`, `vbb`, `rb`, and `max_error`.

`index_post` parses the form; on errors it re-renders with `values=request.form` and `errors={e.field: e.message for e in errors}`. On success it calls `evaluate.evaluate(inputs)` and `_build_view(evaluation)`. Catch `(ValueError, ZeroDivisionError, OverflowError)` and re-render with `form_error="Inputs are outside the numerically stable range."`.

Update `templates/index.html` to render the result section when `result` is set:

- Region badge with class `region-{{ result.region.name }}` and text `REGION: {{ result.region.name|upper }}`.
- Cross-check badge `MATCH` or `MISMATCH`.
- Warning band for `result.region.warning`.
- Mismatch band listing `result.comparison.mismatches|join(', ')`.
- Table headers: `Quantity`, `Analytical (Thévenin)`, `Independent (nodal)`, `|Δ|`.
- Supporting line with `VBB` and `RB`.
- Maximum relative difference line.

Add CSS for `.result`, `.badges`, `.badge`, `.region-active`, `.region-cutoff`, `.region-saturation`, `.crosscheck-ok`, `.crosscheck-bad`, `.warning`, `table`, `th`, `td`, `.supporting`.

- [ ] **Step 4: Run the route tests and confirm they pass**

Run: `.venv\Scripts\python -m pytest tests/test_routes.py -v`
Expected: PASS.

- [ ] **Step 5: Run the whole suite**

Run: `.venv\Scripts\python -m pytest -q`
Expected: PASS, no failures.

- [ ] **Step 6: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add app.py templates/index.html static/style.css tests/test_routes.py
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "feat: render operating point, warnings and cross-check"
```

---

### Task 10: README, demo, and delivery

**Files:**
- Create: `README.md`
- Modify: `docs/superpowers/specs/2026-11-10-bjt-ce-dc-bias-design.md` only if the implementation revealed a needed correction.

- [ ] **Step 1: Write `README.md`**

Include: what the app does, the seven inputs, the equations, the independent nodal cross-check, region rules, install/run/test commands, project structure, and the limitations (no AC, transient, FET, or schematic editing).

- [ ] **Step 2: Run the full test suite**

Run: `.venv\Scripts\python -m pytest -q`
Expected: all tests pass.

- [ ] **Step 3: Start the app and verify the demo**

```powershell
.\.venv\Scripts\python -m flask --app app run --port 5000
```

In a second shell:

```powershell
(Invoke-WebRequest http://127.0.0.1:5000/).StatusCode
```

Expected: `200`. Submit the default form once and confirm the page shows `REGION: ACTIVE`, `MATCH`, and the operating-point table.

- [ ] **Step 4: Commit**

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" add README.md
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" commit -m "docs: add install, run and engineering notes"
```

- [ ] **Step 5: Push to GitHub**

If the user provides an empty repository URL and credentials:

```powershell
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" remote add origin <REPOSITORY_URL>
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" branch -M main
& "C:\Users\B6618070\AppData\Local\Programs\Git\cmd\git.exe" push -u origin main
```

If credentials are unavailable, report the local commit hash and hand over the exact `git remote add` and `git push` commands.
