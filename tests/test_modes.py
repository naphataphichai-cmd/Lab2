import pytest

from engineering import crosscheck, evaluate, model, solver, validation

# Shared Lab 03 case values: VCC = 12 V, RC = 2.2 kฮฉ, ฮฒ = 100, VBE = 0.70 V.
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

FIELDS = ("ib", "ic", "ie", "vce", "vb", "ve", "vc")


@pytest.mark.parametrize(
    "values",
    [
        (12.0, 1e6, 2200.0, 100.0, 0.7),
        (9.0, 470e3, 3300.0, 150.0, 0.65),
        (15.0, 2.2e6, 4700.0, 300.0, 0.7),
    ],
)
def test_fixed_crosscheck_matches_analytical(values):
    inputs = model.FixedBiasInputs(*values)
    analytical = solver.solve_fixed(inputs)
    independent = crosscheck.solve_fixed(inputs)
    for field in FIELDS:
        assert getattr(independent, field) == pytest.approx(
            getattr(analytical, field), rel=1e-9
        )


@pytest.mark.parametrize(
    "values",
    [
        (12.0, 1e6, 1000.0, 2200.0, 100.0, 0.7),
        (9.0, 470e3, 680.0, 2200.0, 150.0, 0.65),
        (15.0, 2.2e6, 1200.0, 5600.0, 50.0, 0.7),
    ],
)
def test_emitter_crosscheck_matches_analytical(values):
    inputs = model.EmitterBiasInputs(*values)
    analytical = solver.solve_emitter(inputs)
    independent = crosscheck.solve_emitter(inputs)
    for field in FIELDS:
        assert getattr(independent, field) == pytest.approx(
            getattr(analytical, field), rel=1e-9
        )


def test_fixed_nodal_kcl_residuals():
    inputs = _fixed()
    point = crosscheck.solve_fixed(inputs)
    base = (inputs.vcc - point.vb) / inputs.rb - point.ib
    collector = (inputs.vcc - point.vc) / inputs.rc - point.ic
    vbe = point.vb - inputs.vbe
    assert abs(base) < 1e-9
    assert abs(collector) < 1e-9
    assert abs(vbe) < 1e-9


def test_emitter_nodal_kcl_residuals():
    inputs = _emitter()
    point = crosscheck.solve_emitter(inputs)
    base = (inputs.vcc - point.vb) / inputs.rb - point.ib
    collector = (inputs.vcc - point.vc) / inputs.rc - point.ic
    vbe = point.vb - point.ve - inputs.vbe
    assert abs(base) < 1e-9
    assert abs(collector) < 1e-9
    assert abs(vbe) < 1e-9

def test_evaluate_dispatches_fixed_mode():
    evaluation = evaluate.evaluate(_fixed(), model.MODE_FIXED)
    assert evaluation.comparison.match
    assert evaluation.region.name == model.REGION_ACTIVE
    assert evaluation.analytical.ic == pytest.approx(1.13e-3, rel=1e-12)


def test_evaluate_dispatches_emitter_mode():
    evaluation = evaluate.evaluate(_emitter(), model.MODE_EMITTER)
    assert evaluation.comparison.match
    assert evaluation.analytical.vce == pytest.approx(8.705449591281, rel=1e-9)


def test_evaluate_fixed_saturation_keeps_raw_point():
    evaluation = evaluate.evaluate(_fixed(rc=15000.0), model.MODE_FIXED)
    assert evaluation.region.name == model.REGION_SATURATION
    assert evaluation.region.warning is not None
    assert evaluation.analytical.vce < 0.2


def test_evaluate_rejects_unknown_mode():
    with pytest.raises(ValueError):
        evaluate.evaluate(_fixed(), "bogus")


def test_display_point_only_rewrites_divider_cutoff():
    inputs = _fixed()
    raw = solver.solve_fixed(inputs)
    region = model.Region(model.REGION_CUTOFF, model.CUTOFF_WARNING)

    assert model.display_point(inputs, raw, region, model.MODE_FIXED) is raw


FIXED_FORM = {"vcc": "12", "rb": "1000000", "rc": "2200", "beta": "100", "vbe": "0.7"}
EMITTER_FORM = dict(FIXED_FORM, re="1000")


def test_parse_mode_defaults_to_divider():
    for raw in (None, "", "divider"):
        mode, error = validation.parse_mode(raw)
        assert mode == model.MODE_DIVIDER
        assert error is None


def test_parse_mode_rejects_unknown():
    mode, error = validation.parse_mode("bogus")
    assert mode is None
    assert error is not None
    assert error.field == "mode"


def test_fixed_form_requires_rb():
    form = dict(FIXED_FORM, rb="")
    inputs, errors = validation.parse_inputs_for_mode(form, model.MODE_FIXED)
    assert inputs is None
    assert {error.field: error.message for error in errors}["rb"] == "Required."


def test_fixed_form_ignores_divider_fields():
    form = dict(FIXED_FORM, r1="abc", r2="0", re="")
    inputs, errors = validation.parse_inputs_for_mode(form, model.MODE_FIXED)
    assert errors == []
    assert inputs == model.FixedBiasInputs(12.0, 1e6, 2200.0, 100.0, 0.7)


def test_emitter_form_requires_rb_and_re():
    for field in ("rb", "re"):
        form = dict(EMITTER_FORM, **{field: ""})
        _, errors = validation.parse_inputs_for_mode(form, model.MODE_EMITTER)
        assert {error.field: error.message for error in errors}[field] == "Required."


def test_emitter_form_parses_and_ignores_divider_fields():
    form = dict(EMITTER_FORM, r1="abc", r2="-5")
    inputs, errors = validation.parse_inputs_for_mode(form, model.MODE_EMITTER)
    assert errors == []
    assert inputs == model.EmitterBiasInputs(12.0, 1e6, 1000.0, 2200.0, 100.0, 0.7)


@pytest.mark.parametrize("field", ["rb", "re"])
def test_mode_resistor_range_is_enforced(field):
    form = dict(EMITTER_FORM, **{field: "0"})
    _, errors = validation.parse_inputs_for_mode(form, model.MODE_EMITTER)
    assert {error.field: error.message for error in errors}[field] == (
        "Must be between 1 mΩ and 10 MΩ."
    )


def test_parse_inputs_for_divider_matches_parse_inputs():
    form = {
        "vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
        "re": "1000", "beta": "150", "vbe": "0.7",
    }
    assert validation.parse_inputs_for_mode(form, model.MODE_DIVIDER) == (
        validation.parse_inputs(form)
    )


FIXED_POST = {
    "mode": "fixed", "vcc": "12", "vcc_unit": "V", "rb": "1", "rb_unit": "MΩ",
    "rc": "2.2", "rc_unit": "kΩ", "beta": "100", "vbe": "0.70", "vbe_unit": "V",
}
EMITTER_POST = dict(FIXED_POST, mode="emitter", re="1", re_unit="kΩ")


def test_get_fixed_mode_shows_rb_only(client):
    body = client.get("/?mode=fixed").get_data(as_text=True)
    assert 'name="rb"' in body
    assert 'name="r1"' not in body
    assert 'name="re"' not in body
    assert "Fixed Bias" in body


def test_get_divider_mode_still_shows_voltage_divider(client):
    body = client.get("/").get_data(as_text=True)
    assert 'name="r1"' in body
    assert 'name="r2"' in body
    assert 'name="re"' in body


def test_fixed_mode_a2(client):
    body = client.post("/", data=FIXED_POST).get_data(as_text=True)
    assert "Fixed Bias" in body
    assert "1.13 mA" in body
    assert "9.514 V" in body
    assert "MATCH" in body


def test_emitter_mode_a3(client):
    body = client.post("/", data=EMITTER_POST).get_data(as_text=True)
    assert "Emitter Bias" in body
    assert "1.026 mA" in body
    assert "8.705 V" in body


def test_emitter_mode_a4_uses_new_re(client):
    body = client.post("/", data=dict(EMITTER_POST, re="2")).get_data(as_text=True)
    assert "940.1 µA" in body
    assert "8.033 V" in body


def test_fixed_mode_a5_rejects_zero_rb(client):
    body = client.post("/", data=dict(FIXED_POST, rb="0")).get_data(as_text=True)
    assert "Must be between 1 mΩ and 10 MΩ." in body
    assert '<td class="val">9.514 V</td>' not in body
    assert "✓ MATCH" not in body


def test_unknown_mode_is_rejected(client):
    body = client.post("/", data=dict(FIXED_POST, mode="bogus")).get_data(as_text=True)
    assert "Choose a supported circuit mode." in body
    assert '<td class="val">1.13 mA</td>' not in body
    assert "✓ MATCH" not in body

