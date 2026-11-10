def test_get_page_shows_default_form(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "BJT Common-Emitter DC Bias" in body
    assert 'name="vcc"' in body
    assert 'value="47000"' in body
    assert "Calculate" in body
