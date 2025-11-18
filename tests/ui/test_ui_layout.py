import pytest

EXPECTED_KEYWORDS = [
    "AI Model Portfolio",
    "Total models",
    "filter-btn",
    "model-card"
]

SECTIONS = ["Metrics", "Thông tin", "Prediction"]


def test_dashboard_layout_contains_sections(http_client):
    resp = http_client.get('/dashboard/ai')
    assert resp.status_code == 200
    html = resp.text
    for text in EXPECTED_KEYWORDS:
        assert text in html, f"Không tìm thấy từ khóa '{text}' trong layout"
    assert 'models-grid' in html


def test_dashboard_has_key_elements(http_client):
    resp = http_client.get('/dashboard/ai/late_delivery')
    assert resp.status_code == 200
    html = resp.text
    assert '<form id="prediction-form"' in html
    assert '<nav class="text-sm text-gray-600">' in html
    assert 'tab-btn' in html
