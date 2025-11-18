import difflib


def test_dashboard_snapshot(http_client, snapshot_baseline):
    resp = http_client.get('/dashboard/ai')
    html = resp.text
    if not snapshot_baseline:
        raise AssertionError('Baseline snapshot rỗng')
    if html.strip() != snapshot_baseline.strip():
        diff = '\n'.join(difflib.unified_diff(
            snapshot_baseline.splitlines(),
            html.splitlines(),
            fromfile='baseline',
            tofile='current'
        ))
        raise AssertionError('UI Snapshot mismatch:\n' + diff[:1000])
