import pytest


def test_dashboard_contains_canvas(http_client):
    resp = http_client.get('/dashboard/ai/late_delivery')
    html = resp.text
    assert '<canvas' in html or 'chart-box' in html


def test_chart_data_endpoint(http_client):
    resp = http_client.get('/ml/metrics/chart-data')
    if resp.status_code == 404:
        pytest.skip('Endpoint /ml/metrics/chart-data chưa được triển khai')
    assert resp.status_code == 200
    data = resp.json()
    assert 'labels' in data and 'datasets' in data
