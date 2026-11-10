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
