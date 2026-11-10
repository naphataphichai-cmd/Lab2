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
