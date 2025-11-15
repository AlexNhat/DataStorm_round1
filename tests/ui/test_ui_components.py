import re

def test_model_cards_render_names(http_client):
    resp = http_client.get('/dashboard/ai')
    html = resp.text
    cards = re.findall(r"class=\"model-card ([^\"]+)\"", html)
    assert cards, "Không tìm thấy card mô hình"
    assert any('classification' in c for c in cards)


def test_model_detail_metrics_table(http_client):
    resp = http_client.get('/dashboard/ai/late_delivery')
    html = resp.text
    assert '<table class="min-w-full text-sm">' in html
    assert 'Tổng quan' in html
    assert 'Metrics & Charts' in html


def test_chart_placeholder_present(http_client):
    resp = http_client.get('/dashboard/ai/late_delivery')
    html = resp.text
    assert 'chart-box' in html or '<canvas' in html
