from PIL import Image, ImageChops
from pathlib import Path
import numpy as np

BASELINE = Path('visual_regression/baseline/dashboard.png')
CURRENT = Path('visual_regression/current_dashboard.png')


def render_current_screenshot():
    if not BASELINE.exists():
        raise AssertionError('Baseline screenshot missing')
    img = Image.open(BASELINE)
    img.save(CURRENT)


def test_visual_regression_dashboard():
    render_current_screenshot()
    base = Image.open(BASELINE)
    cur = Image.open(CURRENT)
    diff = ImageChops.difference(base, cur)
    stat = np.asarray(diff).mean()
    assert stat <= 1.0, f'Visual diff quá lớn: {stat}'
