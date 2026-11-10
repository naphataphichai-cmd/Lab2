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
    form = dict(DEFAULT_FORM)
    form.update(
        {
            "vcc_unit": "V",
            "r1_unit": "kΩ",
            "r2_unit": "kΩ",
            "rc_unit": "kΩ",
            "re_unit": "kΩ",
            "vbe_unit": "V",
        }
    )
    return form
