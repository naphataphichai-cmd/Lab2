import app as app_module


def test_get_page_shows_default_form(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Lab 03: BJT DC Bias Web App" in body
    assert 'name="vcc"' in body
    assert 'value="100"' in body
    assert "Calculate" in body


def test_valid_post_shows_operating_point(client, valid_form):
    response = client.post("/", data=valid_form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Active region approximation OK" in body
    assert "MATCH" in body
    assert "12.3 µA" in body
    assert "1.23 mA" in body
    assert "8.052 V" in body
    assert "Analytical" in body
    assert "Nodal" in body
    assert "VBB" in body
    assert "RB" in body


def test_invalid_number_preserves_value(client, valid_form):
    form = dict(valid_form, r1="abc")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Must be a number." in body
    assert 'value="abc"' in body


def test_empty_field_is_required(client, valid_form):
    form = dict(valid_form, vcc="")
    response = client.post("/", data=form)
    assert response.status_code == 200
    assert "Required." in response.get_data(as_text=True)


def test_zero_resistance_is_rejected(client, valid_form):
    form = dict(valid_form, r1="0")
    response = client.post("/", data=form)
    assert response.status_code == 200
    assert "Must be between 1 mΩ and 10 MΩ." in response.get_data(as_text=True)


def test_vbe_must_be_below_vcc(client, valid_form):
    form = dict(valid_form, vbe="12")
    response = client.post("/", data=form)
    assert response.status_code == 200
    assert "Must be less than VCC." in response.get_data(as_text=True)


def test_cutoff_is_reported(client, valid_form):
    form = dict(valid_form, r2="1")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Cutoff region" in body
    assert "cutoff" in body.lower()
    assert "0 µA" in body


def test_saturation_is_reported(client, valid_form):
    form = dict(valid_form, rc="10")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Saturation region" in body
    assert "not valid for amplifier use" in body


def test_mega_ohm_unit_selection_is_honoured(client, valid_form):
    form = dict(valid_form, r1="1", r1_unit="MΩ")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    # 1 MΩ upper divider pulls VBB below VBE, so the transistor must be off
    assert "Cutoff region" in body


def test_ohm_unit_selection_is_honoured(client, valid_form):
    form = dict(valid_form, r1="100", r1_unit="Ω")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    # a 100 Ω upper divider drives the transistor deep into saturation
    assert "Saturation region" in body


def test_non_finite_result_is_a_normal_error(client, valid_form, monkeypatch):
    def blow_up(evaluation):
        raise ValueError("non-finite")

    monkeypatch.setattr(app_module, "_build_view", blow_up)
    response = client.post("/", data=valid_form)
    assert response.status_code == 200
    assert "outside the numerically stable range" in response.get_data(as_text=True)


def test_extreme_valid_input_does_not_500(client, valid_form):
    form = dict(
        valid_form,
        vcc="100", r1="0.001", r2="0.001", rc="0.001", re="0.001",
        beta="2000", vbe="0",
        r1_unit="Ω", r2_unit="Ω", rc_unit="Ω", re_unit="Ω",
    )
    response = client.post("/", data=form)
    assert response.status_code == 200


def test_acceptance_table_lists_all_cases(client):
    body = client.get("/").get_data(as_text=True)

    for case_id in ("A1", "A2", "A3", "A4", "A5"):
        assert f"{case_id} ·" in body

    for header in (
        "Case",
        "Mode and inputs",
        "Expected before run",
        "Observed",
        "Method",
        "Status",
    ):
        assert f"<th>{header}</th>" in body

    assert body.count('class="status-pill pass"') == 5
    assert "PASS" in body


def test_acceptance_table_shows_observed_values(client):
    body = client.get("/").get_data(as_text=True)

    assert "IC = 1.23 mA" in body
    assert "IC = 1.13 mA" in body
    assert "IC = 1.026 mA" in body
    assert "IC = 940.1 µA" in body
    assert "Must be between 1 mΩ and 10 MΩ." in body
