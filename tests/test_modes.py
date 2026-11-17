import pytest

from engineering import model, solver

# Shared Lab 03 case values: VCC = 12 V, RC = 2.2 kΩ, β = 100, VBE = 0.70 V.
VCC = 12.0
RC = 2200.0
BETA = 100.0
VBE = 0.7


def _fixed(rb=1e6, rc=RC, vcc=VCC, beta=BETA, vbe=VBE):
    return model.FixedBiasInputs(vcc=vcc, rb=rb, rc=rc, beta=beta, vbe=vbe)


def _emitter(rb=1e6, re=1000.0, rc=RC, vcc=VCC, beta=BETA, vbe=VBE):
    return model.EmitterBiasInputs(
        vcc=vcc, rb=rb, re=re, rc=rc, beta=beta, vbe=vbe
    )


def test_fixed_bias_a2_matches_hand_calculation():
    point = solver.solve_fixed(_fixed())

    assert point.ib == pytest.approx(11.3e-6, rel=1e-12)
    assert point.ic == pytest.approx(1.13e-3, rel=1e-12)
    assert point.ie == pytest.approx(1.13e-3 * 101 / 100, rel=1e-12)
    assert point.vb == pytest.approx(VBE, rel=1e-12)
    assert point.ve == 0.0
    assert point.vc == pytest.approx(9.514, rel=1e-12)
    assert point.vce == pytest.approx(9.514, rel=1e-12)


def test_emitter_bias_a3_matches_hand_calculation():
    point = solver.solve_emitter(_emitter())

    assert point.ib == pytest.approx(11.3 / 1.101e6, rel=1e-12)
    assert point.ic == pytest.approx(11.3 / 1.101e6 * BETA, rel=1e-12)
    assert point.ie == pytest.approx(11.3 / 1.101e6 * 101, rel=1e-12)
    assert point.ve == pytest.approx(1.036603088102, rel=1e-9)
    assert point.vb == pytest.approx(1.736603088102, rel=1e-9)
    assert point.vc == pytest.approx(9.742052679383, rel=1e-9)
    assert point.vce == pytest.approx(8.705449591281, rel=1e-9)


def test_emitter_bias_a4_raising_re_lowers_ic():
    one_k = solver.solve_emitter(_emitter(re=1000.0))
    two_k = solver.solve_emitter(_emitter(re=2000.0))

    assert two_k.ic < one_k.ic
    assert two_k.ic == pytest.approx(9.40099833610649e-4, rel=1e-9)
    assert two_k.vce == pytest.approx(8.03277870216306, rel=1e-9)


def test_fixed_bias_saturation_keeps_raw_negative_vce():
    point = solver.solve_fixed(_fixed(rc=15000.0))
    assert point.ib > 0.0
    assert point.vce < 0.2
