def test_get_page_shows_default_form(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "BJT Common-Emitter DC Bias" in body
    assert 'name="vcc"' in body
    assert 'value="47000"' in body
    assert "Calculate" in body


import app as app_module


def test_valid_post_shows_operating_point(client, valid_form):
    response = client.post("/", data=valid_form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "REGION: ACTIVE" in body
    assert "MATCH" in body
    assert "8.825 µA" in body
    assert "1.324 mA" in body
    assert "4.446 V" in body
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
    form = dict(valid_form, r2="1000")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "REGION: CUTOFF" in body
    assert "cutoff" in body.lower()
    assert "0 µA" in body


def test_saturation_is_reported(client, valid_form):
    form = dict(valid_form, rc="10000")
    response = client.post("/", data=form)
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "REGION: SATURATION" in body
    assert "not valid for amplifier use" in body


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
    )
    response = client.post("/", data=form)
    assert response.status_code == 200
