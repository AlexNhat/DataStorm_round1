import pytest

PREDICT_PAYLOAD = {
    "shipping_duration_scheduled": 5,
    "shipping_duration_real": 4,
    "temperature": 27.5,
    "weather_risk_level": 2
}


def test_prediction_form_fields_exist(http_client):
    resp = http_client.get('/dashboard/ai/late_delivery')
    html = resp.text
    for field in ["shipping_duration_scheduled", "shipping_duration_real", "temperature", "weather_risk_level"]:
        assert f"name=\"{field}\"" in html


def test_prediction_form_submission(http_client):
    resp = http_client.post('/ml/logistics/delay', json=PREDICT_PAYLOAD)
    assert resp.status_code == 200
    body = resp.json()
    assert body['status'] == 'success'
    assert 'prediction' in body


def test_prediction_form_validation_numeric(http_client):
    bad_payload = {"shipping_duration_scheduled": "abc"}
    resp = http_client.post('/ml/logistics/delay', json=bad_payload)
    assert resp.status_code in (200, 422)
