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
