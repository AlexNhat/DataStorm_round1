import subprocess
from pathlib import Path

REPORT_DIR = Path('results/test_reports')
REPORT_DIR.mkdir(parents=True, exist_ok=True)
report_file = REPORT_DIR / 'ui_tests.txt'
visual_report = REPORT_DIR / 'ui_visual_diff.png'

with open(report_file, 'w', encoding='utf-8') as handle:
    process = subprocess.run(['pytest', 'tests/ui', '-q'], stdout=handle, stderr=subprocess.STDOUT)
    if process.returncode != 0:
        print('Một số UI tests FAILED - xem results/test_reports/ui_tests.txt')
    else:
        print('UI tests PASSED - log trong results/test_reports/ui_tests.txt')

# copy visual baseline làm báo cáo nhanh
baseline = Path('visual_regression/baseline/dashboard.png')
if baseline.exists():
    visual_report.write_bytes(baseline.read_bytes())
