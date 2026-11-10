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
