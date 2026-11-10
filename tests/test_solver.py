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
