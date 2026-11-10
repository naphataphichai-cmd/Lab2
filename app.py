from flask import Flask, render_template, request

from engineering import evaluate, format as fmt, validation

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "100",
    "r2": "22",
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
    "rc": RESISTOR_UNITS,
    "re": RESISTOR_UNITS,
    "vbe": VOLTAGE_UNITS,
}

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


def _to_base_units(form, units: dict[str, str]) -> dict[str, str]:
    """Convert the submitted values to ohms and volts for the engineering layer."""
    scaled: dict[str, str] = {}

    for field in validation.REQUIRED_FIELDS:
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

    vbb_number, vbb_unit = fmt.format_voltage(evaluation.analytical.vbb)
    rb_number, rb_unit = fmt.format_resistance(evaluation.analytical.rb)

    return {
        "region": evaluation.region,
        "comparison": evaluation.comparison,
        "rows": rows,
        "vbb": f"{vbb_number} {vbb_unit}",
        "rb": f"{rb_number} {rb_unit}",
        "max_error": fmt.format_error(evaluation.comparison.max_rel_error),
    }


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index_get():
        return render_template(
            "index.html",
            values=DEFAULT_FORM,
            units=dict(DEFAULT_UNITS),
            unit_choices=UNIT_CHOICES,
            errors={},
            form_error=None,
            result=None,
        )

    @app.post("/")
    def index_post():
        units = _selected_units(request.form)
        inputs, errors = validation.parse_inputs(
            _to_base_units(request.form, units)
        )

        if errors:
            return render_template(
                "index.html",
                values=request.form,
                units=units,
                unit_choices=UNIT_CHOICES,
                errors={error.field: error.message for error in errors},
                form_error=None,
                result=None,
            )

        try:
            evaluation = evaluate.evaluate(inputs)
            result = _build_view(evaluation)
        except (ValueError, ZeroDivisionError, OverflowError):
            return render_template(
                "index.html",
                values=request.form,
                units=units,
                unit_choices=UNIT_CHOICES,
                errors={},
                form_error="Inputs are outside the numerically stable range.",
                result=None,
            )

        return render_template(
            "index.html",
            values=request.form,
            units=units,
            unit_choices=UNIT_CHOICES,
            errors={},
            form_error=None,
            result=result,
        )

    return app


app = create_app()
