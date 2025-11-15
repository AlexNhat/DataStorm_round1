import pytest

API_PAYLOAD = {
    "shipping_duration_scheduled": 6,
    "shipping_duration_real": 5,
    "temperature": 28.0,
    "weather_risk_level": 3
}


def test_ui_api_integration_flow(http_client):
    resp = http_client.get('/dashboard/ai')
    assert resp.status_code == 200
    api_resp = http_client.post('/ml/logistics/delay', json=API_PAYLOAD)
    assert api_resp.status_code == 200
    data = api_resp.json()['prediction']
    assert 'late_risk_prob' in data or 'risk_score' in data
