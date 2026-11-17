from flask import Flask, render_template, request

from engineering import evaluate, format as fmt, model, validation

DEFAULT_FORM = {
    "mode": model.MODE_DIVIDER,
    "vcc": "12",
    "r1": "100",
    "r2": "22",
    "rb": "1",
    "rc": "2.2",
    "re": "1.0",
    "beta": "100",
    "vbe": "0.70",
}

RESISTOR_UNITS = ("Ω", "kΩ", "MΩ")
VOLTAGE_UNITS = ("V", "mV")

DEFAULT_UNITS = {
    "vcc": "V",
    "r1": "kΩ",
    "r2": "kΩ",
    "rb": "MΩ",
    "rc": "kΩ",
    "re": "kΩ",
    "vbe": "V",
}

UNIT_SCALE = {
    "Ω": 1.0,
    "kΩ": 1e3,
    "MΩ": 1e6,
    "V": 1.0,
    "mV": 1e-3,
}

UNIT_CHOICES = {
    "vcc": VOLTAGE_UNITS,
    "r1": RESISTOR_UNITS,
    "r2": RESISTOR_UNITS,
    "rb": RESISTOR_UNITS,
    "rc": RESISTOR_UNITS,
    "re": RESISTOR_UNITS,
    "vbe": VOLTAGE_UNITS,
}

MODE_CHOICES = [(mode, model.MODE_LABELS[mode]) for mode in model.MODES]

# Lab 03 acceptance record shown on the page. Expected values were calculated
# by hand from the bias equations before the app was run; observed values are
# what the in-app browser showed for each case.
ACCEPTANCE_CASES = (
    {
        "id": "A1",
        "title": "Original mode",
        "inputs": "Divider · R1 = 100 kΩ, R2 = 22 kΩ, RE = 1 kΩ",
        "expected": "IC = 1.2298 mA · VCE = 8.0522 V (same as Lab 02)",
        "observed": "IC = 1.23 mA · VCE = 8.052 V",
        "method": "OpenCode Browser",
        "status": "PASS",
    },
    {
        "id": "A2",
        "title": "Fixed",
        "inputs": "Fixed · RB = 1 MΩ",
        "expected": "IC = 1.1300 mA · VCE = 9.5140 V; no RE input needed",
        "observed": "IC = 1.13 mA · VCE = 9.514 V",
        "method": "OpenCode Browser",
        "status": "PASS",
    },
    {
        "id": "A3",
        "title": "Emitter",
        "inputs": "Emitter · RB = 1 MΩ, RE = 1 kΩ",
        "expected": "IC = 1.0263 mA · VCE = 8.7054 V; RE field used",
        "observed": "IC = 1.026 mA · VCE = 8.705 V",
        "method": "OpenCode Browser",
        "status": "PASS",
    },
    {
        "id": "A4",
        "title": "One value changed",
        "inputs": "Emitter · as A3 with RE = 2 kΩ",
        "expected": "IC must fall from A3: IC = 0.9401 mA · VCE = 8.0328 V",
        "observed": "IC = 940.1 µA · VCE = 8.033 V (lower than A3)",
        "method": "OpenCode Browser",
        "status": "PASS",
    },
    {
        "id": "A5",
        "title": "Bad input",
        "inputs": "Fixed · RB = 0",
        "expected": "Message for RB, page stays up, no previous result reused",
        "observed": "“Must be between 1 mΩ and 10 MΩ.”; result table shows --",
        "method": "OpenCode Browser",
        "status": "PASS",
    },
)


RESULT_ROWS = (
    ("VB", "vb", "voltage"),
    ("VE", "ve", "voltage"),
    ("VC", "vc", "voltage"),
    ("VCE", "vce", "voltage"),
    ("IB", "ib", "current"),
    ("IC", "ic", "current"),
    ("IE", "ie", "current"),
)

FORMATTERS = {
    "current": fmt.format_current,
    "voltage": fmt.format_voltage,
}


def _with_unit(kind: str, value: float) -> str:
    number, unit = FORMATTERS[kind](value)
    return f"{number} {unit}"


def _selected_units(form) -> dict[str, str]:
    units = {}
    for field, fallback in DEFAULT_UNITS.items():
        chosen = form.get(f"{field}_unit", fallback)
        units[field] = chosen if chosen in UNIT_SCALE else fallback
    return units


def _to_base_units(form, units: dict[str, str], fields) -> dict[str, str]:
    """Convert the submitted values to ohms and volts for the engineering layer."""
    scaled: dict[str, str] = {}

    for field in fields:
        raw = form.get(field, "")
        text = raw.strip() if isinstance(raw, str) else str(raw).strip()

        if not text or field not in UNIT_CHOICES:
            scaled[field] = text
            continue

        try:
            value = float(text) * UNIT_SCALE[units[field]]
        except (ValueError, OverflowError):
            scaled[field] = text
            continue

        scaled[field] = f"{value:.12g}"

    return scaled


def _build_view(evaluation: evaluate.Evaluation) -> dict:
    rows = []
    for symbol, field, kind in RESULT_ROWS:
        analytical = getattr(evaluation.analytical, field)
        independent = getattr(evaluation.independent, field)
        rows.append(
            {
                "symbol": symbol,
                "analytical": _with_unit(kind, analytical),
                "independent": _with_unit(kind, independent),
                "delta": _with_unit(kind, abs(analytical - independent)),
            }
        )

    mode = evaluation.mode
    view = {
        "region": evaluation.region,
        "comparison": evaluation.comparison,
        "rows": rows,
        "mode": mode,
        "mode_label": model.MODE_LABELS[mode],
        "show_supporting": mode == model.MODE_DIVIDER,
        "max_error": fmt.format_error(evaluation.comparison.max_rel_error),
    }

    if view["show_supporting"]:
        vbb_number, vbb_unit = fmt.format_voltage(evaluation.analytical.vbb)
        rb_number, rb_unit = fmt.format_resistance(evaluation.analytical.rb)
        view["vbb"] = f"{vbb_number} {vbb_unit}"
        view["rb"] = f"{rb_number} {rb_unit}"

    return view


def create_app() -> Flask:
    app = Flask(__name__)

    def render(
        mode: str,
        values,
        units,
        errors=None,
        form_error=None,
        result=None,
    ):
        return render_template(
            "index.html",
            mode=mode,
            mode_label=model.MODE_LABELS[mode],
            mode_choices=MODE_CHOICES,
            values=values,
            units=units,
            unit_choices=UNIT_CHOICES,
            errors=errors or {},
            form_error=form_error,
            result=result,
            acceptance=ACCEPTANCE_CASES,
        )

    @app.get("/")
    def index_get():
        mode, error = validation.parse_mode(request.args.get("mode"))
        if error is not None:
            mode = model.MODE_DIVIDER
        values = dict(DEFAULT_FORM, mode=mode)
        return render(
            mode,
            values,
            dict(DEFAULT_UNITS),
            form_error=error.message if error else None,
        )

    @app.post("/")
    def index_post():
        mode, mode_error = validation.parse_mode(request.form.get("mode"))
        units = _selected_units(request.form)
        render_mode = mode or model.MODE_DIVIDER

        if mode_error is not None:
            return render(
                render_mode,
                request.form,
                units,
                form_error=mode_error.message,
            )

        fields = validation.MODE_FIELDS[mode]
        inputs, errors = validation.parse_inputs_for_mode(
            _to_base_units(request.form, units, fields),
            mode,
        )

        if errors:
            return render(
                render_mode,
                request.form,
                units,
                errors={error.field: error.message for error in errors},
            )

        try:
            evaluation = evaluate.evaluate(inputs, mode)
            result = _build_view(evaluation)
        except (ValueError, ZeroDivisionError, OverflowError):
            return render(
                render_mode,
                request.form,
                units,
                form_error="Inputs are outside the numerically stable range.",
            )

        return render(render_mode, request.form, units, result=result)

    return app


app = create_app()
