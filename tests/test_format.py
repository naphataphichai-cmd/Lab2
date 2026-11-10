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
