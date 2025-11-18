import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services import ml_service  # pylint: disable=wrong-import-position


def run_inventory_rl():
    payload = {
        "weather_risk_index": 12.4,
        "temp_7d_avg": 29.1,
        "rain_7d_avg": 18.3,
        "storm_flag": 0,
        "region_congestion_index": 1.2,
        "warehouse_workload_score": 0.65,
        "Order Item Product Price": 35.0,
        "Sales": 5200.0,
        "Order Item Total": 7400.0,
        "region": "APAC",
    }
    ml_service.predict_inventory_rl(payload)


def run_demand_forecast():
    service = ml_service.get_revenue_service()
    request = {
        "region": "EU",
        "category": "Electronics",
        "forecast_date": "2025-11-20",
        "revenue_lag_7d": 420000.0,
        "revenue_lag_30d": 1280000.0,
        "revenue_7d_avg": 400000.0,
        "revenue_30d_avg": 1150000.0,
        "month": 11,
        "day_of_week": 2,
        "temperature": 12.0,
    }
    ml_service.predict_revenue(service, request)


def run_late_delivery():
    service = ml_service.get_logistics_service()
    request = {
        "order_id": "ORD-991",
        "shipping_duration_scheduled": 48,
        "shipping_duration_real": 62,
        "temperature": 27.5,
        "precipitation": 32.1,
        "wind_speed": 18.0,
        "weather_risk_level": 3,
        "is_weekend": 0,
        "month": 11,
        "category_name": "Furniture",
        "sales": 1890.0,
    }
    ml_service.predict_logistics_delay(service, request)


def run_pricing_elasticity():
    payload = {
        "price": 48.0,
        "sales": 1200.0,
        "weather_risk_index": 10.2,
        "weather_influence": 9.8,
        "region": "NA",
        "cat_Electronics": 1.0,
        "region_NA": 1.0,
    }
    ml_service.predict_pricing_elasticity(payload)


def main():
    run_inventory_rl()
    run_demand_forecast()
    run_late_delivery()
    run_pricing_elasticity()


if __name__ == "__main__":
    main()
