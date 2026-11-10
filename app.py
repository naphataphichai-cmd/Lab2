from flask import Flask, render_template, request

from engineering import evaluate, format as fmt, validation

DEFAULT_FORM = {
    "vcc": "12",
    "r1": "47000",
    "r2": "10000",
    "rc": "4700",
    "re": "1000",
    "beta": "150",
    "vbe": "0.7",
}

RESULT_ROWS = (
    ("IB", "ib", "current"),
    ("IC", "ic", "current"),
    ("IE", "ie", "current"),
    ("VCE", "vce", "voltage"),
    ("VB", "vb", "voltage"),
    ("VE", "ve", "voltage"),
    ("VC", "vc", "voltage"),
)

FORMATTERS = {
    "current": fmt.format_current,
    "voltage": fmt.format_voltage,
}


def _with_unit(kind: str, value: float) -> str:
    number, unit = FORMATTERS[kind](value)
    return f"{number} {unit}"


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
            errors={},
            form_error=None,
            result=None,
        )

    @app.post("/")
    def index_post():
        inputs, errors = validation.parse_inputs(request.form)

        if errors:
            return render_template(
                "index.html",
                values=request.form,
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
                errors={},
                form_error="Inputs are outside the numerically stable range.",
                result=None,
            )

        return render_template(
            "index.html",
            values=request.form,
            errors={},
            form_error=None,
            result=result,
        )

    return app


app = create_app()
