"""
Central model registry storing metadata for AI models exposed in dashboards and APIs.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class ModelType(str, Enum):
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    RL = "reinforcement_learning"
    SIMULATION = "simulation"
    COGNITIVE = "cognitive"
    ONLINE_LEARNING = "online_learning"


class ModelStatus(str, Enum):
    DEPLOYED = "deployed"
    ANALYTICS = "analytics"
    DEVELOPMENT = "development"
    NOT_TRAINED = "not_trained"


@dataclass
class ModelMetric:
    name: str
    value: Optional[float] = None
    target: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ModelFormField:
    name: str
    label: str
    type: str
    required: bool = False
    default: Any = None
    options: Optional[List[str]] = None
    description: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    placeholder: Optional[str] = None
    unit: Optional[str] = None


@dataclass
class AIModel:
    id: str
    name: str
    display_name: str
    type: ModelType
    description: str
    status: ModelStatus
    version: str = "1.0.0"
    metrics: Optional[List[ModelMetric]] = None
    api_endpoint: Optional[str] = None
    api_method: str = "POST"
    docs_path: Optional[str] = None
    form_fields: Optional[List[ModelFormField]] = None
    dataset_info: Optional[str] = None
    last_trained: Optional[str] = None
    model_path: Optional[str] = None
    chart_types: Optional[List[str]] = None
    sample_payload: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metrics is None:
            self.metrics = []
        if self.form_fields is None:
            self.form_fields = []
        if self.chart_types is None:
            self.chart_types = []


MODEL_REGISTRY: Dict[str, AIModel] = {
    "late_delivery": AIModel(
        id="late_delivery",
        name="late_delivery",
        display_name="Late Delivery Classifier",
        type=ModelType.CLASSIFICATION,
        description="Gradient boosting model with weather context to flag shipments likely to arrive late.",
        status=ModelStatus.DEPLOYED,
        version="5.4.0",
        metrics=[
            ModelMetric(name="AUC-ROC", value=0.81, target=0.75, description="Binary classification quality"),
            ModelMetric(name="F1 Score", value=0.68, target=0.65),
        ],
        api_endpoint="/ml/logistics/delay",
        docs_path="docs/AI_MODELS_DETAIL.md#late-delivery-classifier",
        form_fields=[
            ModelFormField(
                name="shipping_duration_scheduled",
                label="Planned Transit Time (days)",
                type="number",
                required=True,
                default=5,
                min_value=1,
                max_value=120,
                step=1,
                description="Lead time promised to customers."
            ),
            ModelFormField(
                name="temperature",
                label="Temperature (degC)",
                type="number",
                default=27.5,
                min_value=-30,
                max_value=55,
                step=0.1,
                description="Average ambient temperature for the lane."
            ),
            ModelFormField(
                name="precipitation",
                label="Precipitation (mm)",
                type="number",
                default=3.2,
                min_value=0,
                max_value=500,
                step=0.1,
                description="Total rainfall during the shipping window."
            ),
            ModelFormField(
                name="wind_speed",
                label="Wind Speed (m/s)",
                type="number",
                default=8.1,
                min_value=0,
                max_value=60,
                step=0.1,
                description="Maximum sustained wind speed."
            ),
            ModelFormField(
                name="weather_risk_level",
                label="Weather Risk Index (1-5)",
                type="number",
                default=2,
                min_value=1,
                max_value=5,
                step=1,
                description="Composite score computed by the data pipeline."
            ),
            ModelFormField(
                name="is_weekend",
                label="Weekend Delivery",
                type="select",
                default=0,
                options=["0", "1"],
                description="Set 1 if the delivery date is Saturday/Sunday."
            ),
            ModelFormField(
                name="month",
                label="Month (1-12)",
                type="number",
                default=6,
                min_value=1,
                max_value=12,
                step=1,
                description="Calendar month of shipment."
            ),
            ModelFormField(
                name="category_name",
                label="Product Category",
                type="text",
                default="Electronics",
                description="Free text product segment."
            ),
        ],
        dataset_info="Global supply chain shipments with weather enrichment (data/merged/supplychain_weather_merged_global.csv)",
        model_path="models/logistics_delay_model.pkl",
        chart_types=["confusion_matrix", "roc_curve", "feature_importance"],
        sample_payload={
            "shipping_duration_scheduled": 5,
            "temperature": 27.5,
            "precipitation": 3.2,
            "wind_speed": 8.1,
            "weather_risk_level": 2,
            "is_weekend": 0,
            "month": 6,
            "category_name": "Electronics"
        },
    ),
    "revenue_forecast": AIModel(
        id="revenue_forecast",
        name="revenue_forecast",
        display_name="Demand Forecast Ensemble",
        type=ModelType.REGRESSION,
        description="XGBoost + Prophet + LSTM ensemble that predicts demand across global regions.",
        status=ModelStatus.DEPLOYED,
        version="7.6.0",
        metrics=[
            ModelMetric(name="MAPE", value=18.4, target=22.0, unit="%"),
            ModelMetric(name="RMSE", value=41000.0, unit="USD"),
        ],
        api_endpoint="/ml/forecast/demand",
        docs_path="docs/AI_MODELS_DETAIL.md#demand-forecast-ensemble",
        form_fields=[
            ModelFormField(
                name="region",
                label="Region",
                type="select",
                default="GLOBAL",
                options=["GLOBAL", "EU", "APAC", "NA", "LATAM", "AFRICA", "MENA", "OTHER"],
                description="Geography for the forecast."
            ),
            ModelFormField(
                name="category",
                label="Product Category",
                type="text",
                default="Electronics",
                description="Business category or portfolio."
            ),
            ModelFormField(
                name="forecast_date",
                label="Forecast Date",
                type="date",
                required=True,
                default="2025-05-01",
                description="Anchor date for the prediction window."
            ),
            ModelFormField(
                name="revenue_lag_7d",
                label="Revenue Lag 7d",
                type="number",
                default=52000.0,
                min_value=0,
                step=100.0,
                unit="USD",
                description="Actual revenue seven days prior."
            ),
            ModelFormField(
                name="revenue_lag_30d",
                label="Revenue Lag 30d",
                type="number",
                default=208000.0,
                min_value=0,
                step=100.0,
                unit="USD",
                description="Actual revenue thirty days prior."
            ),
            ModelFormField(
                name="revenue_7d_avg",
                label="7-day Moving Avg",
                type="number",
                default=54000.0,
                min_value=0,
                step=100.0,
                description="Rolling seven-day average."
            ),
            ModelFormField(
                name="revenue_30d_avg",
                label="30-day Moving Avg",
                type="number",
                default=215000.0,
                min_value=0,
                step=100.0,
                description="Rolling thirty-day average."
            ),
            ModelFormField(
                name="month",
                label="Month (1-12)",
                type="number",
                default=7,
                min_value=1,
                max_value=12,
                step=1,
                description="Calendar month of forecast."
            ),
            ModelFormField(
                name="day_of_week",
                label="Day of Week (0=Mon)",
                type="number",
                default=1,
                min_value=0,
                max_value=6,
                step=1,
                description="Weekday index."
            ),
            ModelFormField(
                name="temperature",
                label="Temperature (degC)",
                type="number",
                default=30.0,
                min_value=-30,
                max_value=55,
                step=0.1,
                description="Regional average temperature."
            ),
        ],
        dataset_info="Merged supply chain + weather dataset với rolling features (scripts/train_forecast.py)",
        model_path="models/revenue_forecast_model.pkl",
        chart_types=["forecast_plot", "mape_timeline", "region_performance"],
        sample_payload={
            "region": "GLOBAL",
            "category": "Electronics",
            "forecast_date": "2025-05-01",
            "revenue_lag_7d": 52000.0,
            "revenue_lag_30d": 208000.0,
            "revenue_7d_avg": 54000.0,
            "revenue_30d_avg": 215000.0,
            "month": 5,
            "day_of_week": 2,
            "temperature": 30.0
        },
    ),
    "inventory_rl": AIModel(
        id="inventory_rl",
        name="inventory_rl",
        display_name="Inventory Optimizer RL",
        type=ModelType.RL,
        description="Policy network recommending buffer adjustments per region using weather and congestion.",
        status=ModelStatus.DEPLOYED,
        version="5.3.0",
        metrics=[
            ModelMetric(name="Average Reward", value=1.18),
            ModelMetric(name="Stockout Reduction", value=0.27, unit="ratio"),
        ],
        api_endpoint="/ml/rl/inventory",
        docs_path="docs/AI_MODELS_DETAIL.md#inventory-optimizer-rl",
        form_fields=[
            ModelFormField(
                name="weather_risk_index",
                label="Weather Risk Index (0-1)",
                type="number",
                required=True,
                default=0.18,
                min_value=0,
                max_value=1,
                step=0.01,
                description="Composite weather severity."
            ),
            ModelFormField(
                name="temp_7d_avg",
                label="Temperature 7d Avg (degC)",
                type="number",
                default=29.5,
                min_value=-20,
                max_value=50,
                step=0.1,
                description="Rolling temperature average."
            ),
            ModelFormField(
                name="rain_7d_avg",
                label="Rainfall 7d Avg (mm)",
                type="number",
                default=8.0,
                min_value=0,
                max_value=400,
                step=0.1,
                description="Rolling rainfall average."
            ),
            ModelFormField(
                name="storm_flag",
                label="Storm Flag",
                type="select",
                default=0,
                options=["0", "1"],
                description="1 if storm conditions expected."
            ),
            ModelFormField(
                name="region_congestion_index",
                label="Region Congestion (0-5)",
                type="number",
                default=2.3,
                min_value=0,
                max_value=5,
                step=0.1,
                description="Congestion index from monitoring pipeline."
            ),
            ModelFormField(
                name="warehouse_workload_score",
                label="Warehouse Workload (0-1)",
                type="number",
                default=0.55,
                min_value=0,
                max_value=1,
                step=0.01,
                description="Utilization ratio for the warehouse."
            ),
            ModelFormField(
                name="order_item_price",
                label="Order Item Price",
                type="number",
                default=45.0,
                min_value=0,
                step=0.01,
                unit="USD",
                description="Unit price for the SKU."
            ),
            ModelFormField(
                name="sales",
                label="Daily Sales Units",
                type="number",
                default=125.0,
                min_value=0,
                step=1,
                description="Observed units sold."
            ),
            ModelFormField(
                name="order_item_total",
                label="Order Value",
                type="number",
                default=5600.0,
                min_value=0,
                step=1,
                unit="USD",
                description="Total order amount (price * quantity)."
            ),
            ModelFormField(
                name="region",
                label="Region",
                type="select",
                default="GLOBAL",
                options=["GLOBAL", "EU", "APAC", "NA", "LATAM", "AFRICA", "MENA"],
                description="Region to apply the recommendation."
            ),
        ],
        dataset_info="Global merged supply chain + weather dataset with RL state augmentation.",
        model_path="models/inventory_rl/global/inventory_rl_global.pkl",
        chart_types=["reward_curve", "policy_actions"],
        sample_payload={
            "weather_risk_index": 0.18,
            "temp_7d_avg": 29.5,
            "rain_7d_avg": 8.0,
            "storm_flag": 0,
            "region_congestion_index": 2.3,
            "warehouse_workload_score": 0.55,
            "order_item_price": 45.0,
            "sales": 125.0,
            "order_item_total": 5600.0,
            "region": "GLOBAL"
        },
    ),
    "pricing_elasticity": AIModel(
        id="pricing_elasticity",
        name="pricing_elasticity",
        display_name="Pricing Elasticity Model",
        type=ModelType.REGRESSION,
        description="Elastic net regressor estimating demand sensitivity to price and weather influences.",
        status=ModelStatus.DEPLOYED,
        version="3.2.0",
        metrics=[
            ModelMetric(name="MAPE", value=9.8, unit="%"),
            ModelMetric(name="R2", value=0.72),
        ],
        api_endpoint="/ml/pricing/elasticity",
        docs_path="docs/AI_MODELS_DETAIL.md#pricing-elasticity-model",
        form_fields=[
            ModelFormField(
                name="price",
                label="Current Price",
                type="number",
                required=True,
                default=49.0,
                min_value=0,
                step=0.01,
                unit="USD",
                description="Proposed selling price."
            ),
            ModelFormField(
                name="sales",
                label="Baseline Sales Units",
                type="number",
                required=True,
                default=120.0,
                min_value=0,
                step=1,
                description="Expected daily units without price change."
            ),
            ModelFormField(
                name="weather_risk_index",
                label="Weather Risk Index (0-1)",
                type="number",
                default=0.2,
                min_value=0,
                max_value=1,
                step=0.01,
                description="Weather sensitivity driver."
            ),
            ModelFormField(
                name="weather_influence",
                label="Weather Influence Modifier",
                type="number",
                default=0.1,
                min_value=-1,
                max_value=1,
                step=0.01,
                description="Optional override for weather effect."
            ),
            ModelFormField(
                name="region",
                label="Region",
                type="select",
                default="GLOBAL",
                options=["GLOBAL", "EU", "APAC", "NA", "LATAM", "AFRICA", "MENA"],
                description="Market where the price change applies."
            ),
        ],
        dataset_info="Merged sales + weather dataset with price elasticity features.",
        model_path="models/pricing/global/model.pkl",
        chart_types=["elasticity_curve", "region_heatmap"],
        sample_payload={
            "price": 49.0,
            "sales": 120.0,
            "weather_risk_index": 0.2,
            "weather_influence": 0.1,
            "region": "GLOBAL"
        },
    ),
    "customer_churn": AIModel(
        id="customer_churn",
        name="customer_churn",
        display_name="Customer Churn Classifier",
        type=ModelType.CLASSIFICATION,
        description="RFM-based classification model for retention prioritization.",
        status=ModelStatus.ANALYTICS,
        version="2.1.0",
        metrics=[
            ModelMetric(name="Recall", value=0.71),
            ModelMetric(name="Precision", value=0.63),
        ],
        api_endpoint="/ml/customer/churn",
        docs_path="docs/AI_MODELS_DETAIL.md#customer-churn-classifier",
        form_fields=[
            ModelFormField(
                name="customer_id",
                label="Customer ID",
                type="text",
                required=True,
                placeholder="C123456",
                description="Unique identifier used in CRM."
            ),
            ModelFormField(
                name="rfm_recency",
                label="Recency (days)",
                type="number",
                default=30,
                min_value=0,
                description="Days since last purchase."
            ),
            ModelFormField(
                name="rfm_frequency",
                label="Frequency",
                type="number",
                default=8,
                min_value=0,
                description="Orders placed in the past year."
            ),
            ModelFormField(
                name="rfm_monetary",
                label="Monetary Value",
                type="number",
                default=1200.0,
                min_value=0,
                step=0.01,
                unit="USD",
                description="Total spend in the past year."
            ),
            ModelFormField(
                name="total_orders",
                label="Total Orders",
                type="number",
                default=15,
                min_value=0,
                description="Lifetime orders."
            ),
            ModelFormField(
                name="avg_order_value",
                label="Average Order Value",
                type="number",
                default=85.0,
                min_value=0,
                step=0.01,
                unit="USD",
                description="Average check size."
            ),
        ],
        dataset_info="CRM derived features (RFM + lifecycle).",
        model_path="models/churn_model.pkl",
        chart_types=["confusion_matrix", "feature_importance"],
        sample_payload={
            "customer_id": "C123456",
            "rfm_recency": 30,
            "rfm_frequency": 8,
            "rfm_monetary": 1200.0,
            "total_orders": 15,
            "avg_order_value": 85.0
        },
    ),
    "drift_detection": AIModel(
        id="drift_detection",
        name="drift_detection",
        display_name="Data Drift Monitor",
        type=ModelType.ONLINE_LEARNING,
        description="Theo dõi độ lệch dữ liệu giữa baseline và dữ liệu mới để quyết định retrain.",
        status=ModelStatus.ANALYTICS,
        metrics=[ModelMetric(name="Drift Score", value=0.07, target=0.2)],
        api_endpoint="/monitoring/drift/check",
        docs_path="docs/MONITORING_AUTOMATION_GLOBAL.md",
        form_fields=[
            ModelFormField(
                name="late_delivery_risk",
                label="Late_delivery_risk",
                type="number",
                required=True,
                default=0.18,
                min_value=0,
                max_value=1,
                step=0.01,
                description="Rủi ro giao trễ tổng hợp (0-1)."
            ),
            ModelFormField(
                name="weather_risk_index",
                label="weather_risk_index",
                type="number",
                required=True,
                default=0.2,
                min_value=0,
                max_value=1,
                step=0.01,
                description="Chỉ số rủi ro thời tiết toàn cục (0-1)."
            ),
            ModelFormField(
                name="temp_mean_7d",
                label="temp_mean_7d (°C)",
                type="number",
                required=True,
                default=29.5,
                min_value=-30,
                max_value=55,
                step=0.1,
                description="Nhiệt độ trung bình 7 ngày gần nhất."
            ),
        ],
        dataset_info="Streaming inference statistics",
        chart_types=["drift_timeline", "distribution_comparison"],
        sample_payload={
            "late_delivery_risk": 0.18,
            "weather_risk_index": 0.2,
            "temp_mean_7d": 29.5
        },
    ),
    "digital_twin": AIModel(
        id="digital_twin",
        name="digital_twin",
        display_name="Digital Twin Simulation",
        type=ModelType.SIMULATION,
        description="Simulates end-to-end supply chain scenarios for what-if analysis.",
        status=ModelStatus.ANALYTICS,
        api_endpoint="/api/digital-twin/run",
        docs_path="docs/V6_V7_IMPLEMENTATION_SUMMARY.md",
        form_fields=[
            ModelFormField(
                name="duration_days",
                label="Simulation Duration (days)",
                type="number",
                required=True,
                default=30,
                min_value=1,
                max_value=180,
                description="Length of the what-if simulation."
            ),
            ModelFormField(
                name="scenario",
                label="Scenario",
                type="select",
                default="normal",
                options=["normal", "demand_surge", "weather_storm", "port_congestion", "supplier_disruption"],
                description="Scenario template."
            ),
            ModelFormField(
                name="region",
                label="Khu vực",
                type="select",
                default="GLOBAL",
                options=["GLOBAL", "EU", "APAC", "NA", "LATAM", "AFRICA", "MENA"],
                description="Vùng mô phỏng chính."
            ),
        ],
        dataset_info="Digital twin state stored trong engines/digital_twin.",
        sample_payload={"duration_days": 30, "scenario": "normal", "region": "GLOBAL"},
    ),
    "strategy_engine": AIModel(
        id="strategy_engine",
        name="strategy_engine",
        display_name="Strategic Reasoning Engine",
        type=ModelType.COGNITIVE,
        description="Aggregates model insights and produces executive-ready strategies.",
        status=ModelStatus.ANALYTICS,
        api_endpoint="/api/strategy/recommend",
        docs_path="docs/STRATEGIC_AI_GUIDE.md",
        form_fields=[
            ModelFormField(
                name="region",
                label="Khu vực ưu tiên",
                type="select",
                default="GLOBAL",
                options=["GLOBAL", "EU", "APAC", "NA", "LATAM", "AFRICA", "MENA"],
            ),
            ModelFormField(
                name="season",
                label="Mùa vụ",
                type="select",
                default="all",
                options=["all", "spring", "summer", "autumn", "winter"],
            ),
            ModelFormField(
                name="inventory",
                label="Tồn kho hiện tại",
                type="number",
                default=10000,
                min_value=0,
            ),
            ModelFormField(
                name="demand_outlook",
                label="Xu hướng nhu cầu",
                type="select",
                default="neutral",
                options=["neutral", "surge", "slow"],
            ),
            ModelFormField(
                name="risk_focus",
                label="Ưu tiên chiến lược",
                type="select",
                default="balanced",
                options=["balanced", "growth", "cost"],
            ),
        ],
        sample_payload={
            "region": "GLOBAL",
            "season": "summer",
            "inventory": 12000,
            "demand_outlook": "surge",
            "risk_focus": "balanced",
        },
    ),
}


def get_all_models() -> List[AIModel]:
    return list(MODEL_REGISTRY.values())


def get_model(model_id: str) -> Optional[AIModel]:
    return MODEL_REGISTRY.get(model_id)


def get_models_by_type(model_type: ModelType) -> List[AIModel]:
    return [model for model in MODEL_REGISTRY.values() if model.type == model_type]


def get_models_by_status(status: ModelStatus) -> List[AIModel]:
    return [model for model in MODEL_REGISTRY.values() if model.status == status]


def check_model_exists(model_id: str) -> bool:
    return model_id in MODEL_REGISTRY


def get_model_metrics_summary(model_id: str) -> Dict[str, Any]:
    model = get_model(model_id)
    if not model:
        return {}
    return {
        "model_id": model_id,
        "metrics": [
            {
                "name": metric.name,
                "value": metric.value,
                "target": metric.target,
                "unit": metric.unit,
                "description": metric.description,
            }
            for metric in model.metrics
        ],
    }


def check_model_files() -> Dict[str, bool]:
    results: Dict[str, bool] = {}
    for model_id, model in MODEL_REGISTRY.items():
        if model.model_path:
            results[model_id] = (BASE_DIR / model.model_path).exists()
        else:
            results[model_id] = True
    return results
