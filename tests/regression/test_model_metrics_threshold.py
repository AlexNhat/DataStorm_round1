import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
BASELINE = json.loads((ROOT_DIR / "tests" / "metrics_baseline.json").read_text(encoding="utf-8-sig"))


def load_latest_metrics():
    results_dir = ROOT_DIR / "results"
    run_dirs = sorted(
        [d for d in results_dir.iterdir() if d.is_dir() and d.name.startswith("run_")],
        reverse=True,
    )
    for run in run_dirs:
        candidate = run / "model_performance" / "all_models_metrics.json"
        if candidate.exists():
            return json.loads(candidate.read_text())
    raise AssertionError("Không tìm thấy metrics cho regression test")


RUN_METRICS = load_latest_metrics()


def test_late_delivery_regression_threshold():
    base = BASELINE["late_delivery"]
    cur = RUN_METRICS["late_delivery_v2"]
    assert cur["auc"] + BASELINE["thresholds"]["auc_drop"] >= base["auc"]
    assert cur["f1"] + BASELINE["thresholds"]["f1_drop"] >= base["f1"]


def test_forecast_regression_threshold():
    base = BASELINE["revenue_forecast"]
    cur = RUN_METRICS["revenue_forecast_v2"]
    assert cur["mape"] <= base["mape"] + BASELINE["thresholds"]["mape_increase"]
    assert cur["rmse"] <= base["rmse"] + BASELINE["thresholds"]["rmse_increase"]
