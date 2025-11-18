import json

PAYLOAD = {
    "shipping_duration_scheduled": 5,
    "shipping_duration_real": 4,
    "temperature": 26.5,
    "weather_risk_level": 1
}


def test_ui_full_workflow(http_client):
    overview = http_client.get('/dashboard/ai')
    assert overview.status_code == 200
    detail = http_client.get('/dashboard/ai/late_delivery')
    assert detail.status_code == 200
    api_resp = http_client.post('/ml/logistics/delay', json=PAYLOAD)
    assert api_resp.status_code == 200
    data = api_resp.json()
    assert data['status'] == 'success'
    result = data['prediction']
    assert 'late_risk_prob' in result
    assert 0 <= result['late_risk_prob'] <= 1
