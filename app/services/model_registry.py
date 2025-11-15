"""
Model Registry: Quản lý metadata của tất cả AI models trong hệ thống.

Registry này định nghĩa:
- Tên model
- Loại model (classification, regression, RL, simulation)
- Mô tả
- Metrics
- API endpoints
- Documentation paths
- Form fields cho prediction
"""

from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass
from pathlib import Path
import os

BASE_DIR = Path(__file__).parent.parent.parent


class ModelType(str, Enum):
    """Loại model."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    RL = "reinforcement_learning"
    SIMULATION = "simulation"
    COGNITIVE = "cognitive"
    ONLINE_LEARNING = "online_learning"


class ModelStatus(str, Enum):
    """Trạng thái model."""
    DEPLOYED = "deployed"
    ANALYTICS = "analytics"
    DEVELOPMENT = "development"
    NOT_TRAINED = "not_trained"


@dataclass
class ModelMetric:
    """Metric của model."""
    name: str
    value: Optional[float] = None
    target: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ModelFormField:
    """Form field cho prediction."""
    name: str
    label: str
    type: str  # text, number, select, date, etc.
    required: bool = False
    default: Any = None
    options: Optional[List[str]] = None
    description: Optional[str] = None


@dataclass
class AIModel:
    """Metadata của một AI model."""
    id: str
    name: str
    display_name: str
    type: ModelType
    description: str
    status: ModelStatus
    version: str = "1.0.0"
    
    # Metrics
    metrics: List[ModelMetric] = None
    
    # API
    api_endpoint: Optional[str] = None
    api_method: str = "POST"
    
    # Documentation
    docs_path: Optional[str] = None
    
    # Form fields cho prediction
    form_fields: List[ModelFormField] = None
    
    # Additional info
    dataset_info: Optional[str] = None
    last_trained: Optional[str] = None
    model_path: Optional[str] = None
    
    # Charts
    chart_types: List[str] = None  # confusion_matrix, roc_curve, forecast_plot, etc.
    
    def __post_init__(self):
        if self.metrics is None:
            self.metrics = []
        if self.form_fields is None:
            self.form_fields = []
        if self.chart_types is None:
            self.chart_types = []


# ============================================================================
# MODEL REGISTRY
# ============================================================================

MODEL_REGISTRY: Dict[str, AIModel] = {
    "late_delivery": AIModel(
        id="late_delivery",
        name="late_delivery",
        display_name="Dự đoán Giao hàng Trễ",
        type=ModelType.CLASSIFICATION,
        description="Dự đoán nguy cơ giao hàng trễ dựa trên thông tin đơn hàng, shipping, và thời tiết để cảnh báo sớm và tối ưu hóa logistics.",
        status=ModelStatus.DEPLOYED,
        version="1.0.0",
        metrics=[
            ModelMetric(name="AUC-ROC", value=None, target=0.70, unit="", description="Area Under ROC Curve"),
            ModelMetric(name="F1 Score", value=None, target=0.60, unit="", description="F1 Score"),
            ModelMetric(name="Precision", value=None, target=0.65, unit="", description="Precision"),
            ModelMetric(name="Recall", value=None, target=0.60, unit="", description="Recall"),
        ],
        api_endpoint="/ml/logistics/delay",
        api_method="POST",
        docs_path="docs/model_late_delivery.md",
        form_fields=[
            ModelFormField(name="shipping_duration_scheduled", label="Thời gian giao hàng dự kiến (ngày)", type="number", required=True, default=5),
            ModelFormField(name="temperature", label="Nhiệt độ (°C)", type="number", required=False, default=25.0),
            ModelFormField(name="precipitation", label="Lượng mưa (mm)", type="number", required=False, default=0.0),
            ModelFormField(name="wind_speed", label="Tốc độ gió (m/s)", type="number", required=False, default=10.0),
            ModelFormField(name="weather_risk_level", label="Mức độ rủi ro thời tiết (1-5)", type="number", required=False, default=2),
            ModelFormField(name="is_weekend", label="Cuối tuần", type="select", required=False, default=0, options=["0", "1"]),
            ModelFormField(name="month", label="Tháng", type="number", required=False, default=6),
            ModelFormField(name="category_name", label="Danh mục sản phẩm", type="text", required=False, default="Electronics"),
        ],
        dataset_info="Supply Chain Dataset + Weather Data (~180,000 records)",
        last_trained=None,
        model_path="models/logistics_delay_model.pkl",
        chart_types=["confusion_matrix", "roc_curve", "feature_importance"]
    ),
    
    "revenue_forecast": AIModel(
        id="revenue_forecast",
        name="revenue_forecast",
        display_name="Dự báo Doanh thu",
        type=ModelType.REGRESSION,
        description="Dự báo doanh thu tương lai theo thời gian để phục vụ kế hoạch doanh số, tối ưu hóa inventory và phân bổ resources.",
        status=ModelStatus.DEPLOYED,
        version="1.0.0",
        metrics=[
            ModelMetric(name="MAPE", value=None, target=30.0, unit="%", description="Mean Absolute Percentage Error"),
            ModelMetric(name="RMSE", value=None, target=None, unit="$", description="Root Mean Squared Error"),
            ModelMetric(name="MAE", value=None, target=None, unit="$", description="Mean Absolute Error"),
            ModelMetric(name="R²", value=None, target=0.70, unit="", description="R-squared"),
        ],
        api_endpoint="/ml/revenue/forecast",
        api_method="POST",
        docs_path="docs/model_revenue_forecast.md",
        form_fields=[
            ModelFormField(name="region", label="Khu vực", type="text", required=False, default="United States"),
            ModelFormField(name="category", label="Danh mục", type="text", required=False, default="Electronics"),
            ModelFormField(name="revenue_lag_7d", label="Doanh thu 7 ngày trước", type="number", required=False, default=50000.0),
            ModelFormField(name="revenue_lag_30d", label="Doanh thu 30 ngày trước", type="number", required=False, default=200000.0),
            ModelFormField(name="month", label="Tháng", type="number", required=False, default=7),
            ModelFormField(name="day_of_week", label="Ngày trong tuần (0-6)", type="number", required=False, default=1),
            ModelFormField(name="temperature", label="Nhiệt độ (°C)", type="number", required=False, default=28.0),
        ],
        dataset_info="Supply Chain Dataset aggregated by month + region (~X records)",
        last_trained=None,
        model_path="models/revenue_forecast_model.pkl",
        chart_types=["forecast_plot", "error_distribution", "actual_vs_predicted"]
    ),
    
    "customer_churn": AIModel(
        id="customer_churn",
        name="customer_churn",
        display_name="Dự đoán Churn Khách hàng",
        type=ModelType.CLASSIFICATION,
        description="Dự đoán khách hàng có khả năng churn (không quay lại mua) dựa trên RFM và lịch sử mua hàng để phục vụ chiến dịch giữ chân khách hàng.",
        status=ModelStatus.DEPLOYED,
        version="1.0.0",
        metrics=[
            ModelMetric(name="AUC-ROC", value=None, target=0.75, unit="", description="Area Under ROC Curve"),
            ModelMetric(name="Precision@Top100", value=None, target=0.50, unit="", description="Precision at Top 100"),
            ModelMetric(name="F1 Score", value=None, target=0.65, unit="", description="F1 Score"),
        ],
        api_endpoint="/ml/customer/churn",
        api_method="POST",
        docs_path="docs/model_customer_churn.md",
        form_fields=[
            ModelFormField(name="customer_id", label="Customer ID", type="text", required=True, default=""),
            ModelFormField(name="rfm_recency", label="RFM Recency (ngày)", type="number", required=False, default=120),
            ModelFormField(name="rfm_frequency", label="RFM Frequency", type="number", required=False, default=5),
            ModelFormField(name="rfm_monetary", label="RFM Monetary ($)", type="number", required=False, default=5000.0),
            ModelFormField(name="total_orders", label="Tổng số đơn hàng", type="number", required=False, default=10),
            ModelFormField(name="total_sales", label="Tổng doanh thu ($)", type="number", required=False, default=5000.0),
            ModelFormField(name="avg_order_value", label="Giá trị đơn hàng trung bình ($)", type="number", required=False, default=500.0),
            ModelFormField(name="days_since_first_order", label="Số ngày từ lần mua đầu tiên", type="number", required=False, default=365),
        ],
        dataset_info="Supply Chain Dataset aggregated by customer (~X customers)",
        last_trained=None,
        model_path="models/churn_model.pkl",
        chart_types=["precision_recall_curve", "feature_importance", "churn_distribution"]
    ),
    
    "drift_detection": AIModel(
        id="drift_detection",
        name="drift_detection",
        display_name="Phát hiện Drift",
        type=ModelType.ONLINE_LEARNING,
        description="Phát hiện data drift và concept drift để trigger auto-retrain và maintain model quality.",
        status=ModelStatus.ANALYTICS,
        version="1.0.0",
        metrics=[
            ModelMetric(name="Drift Score", value=None, target=0.05, unit="", description="Drift detection score"),
        ],
        api_endpoint="/v6/observe",
        api_method="POST",
        docs_path="docs/ML_IMPROVEMENTS_V6_V7.md",
        form_fields=[],
        dataset_info="Real-time streaming data",
        last_trained=None,
        model_path=None,
        chart_types=["drift_timeline", "distribution_comparison"]
    ),
    
    "digital_twin": AIModel(
        id="digital_twin",
        name="digital_twin",
        display_name="Digital Twin Simulation",
        type=ModelType.SIMULATION,
        description="Mô phỏng toàn bộ supply chain để phân tích scenarios, what-if analysis, và risk assessment.",
        status=ModelStatus.ANALYTICS,
        version="1.0.0",
        metrics=[
            ModelMetric(name="Simulation Accuracy", value=None, target=0.85, unit="", description="Simulation accuracy vs real data"),
        ],
        api_endpoint="/v7/digital-twin/simulate",
        api_method="POST",
        docs_path="docs/V6_V7_IMPLEMENTATION_SUMMARY.md",
        form_fields=[
            ModelFormField(name="duration_days", label="Thời gian mô phỏng (ngày)", type="number", required=True, default=30),
            ModelFormField(name="scenario", label="Scenario", type="select", required=False, default="normal", 
                          options=["normal", "demand_surge", "weather_storm", "port_congestion", "supplier_disruption"]),
        ],
        dataset_info="Supply Chain State + Scenarios",
        last_trained=None,
        model_path=None,
        chart_types=["simulation_timeline", "inventory_levels", "cost_analysis"]
    ),
    
    "strategy_engine": AIModel(
        id="strategy_engine",
        name="strategy_engine",
        display_name="Strategic Reasoning Engine",
        type=ModelType.COGNITIVE,
        description="Tạo và so sánh các phương án chiến lược dựa trên model outputs và business context để hỗ trợ decision-making.",
        status=ModelStatus.ANALYTICS,
        version="1.0.0",
        metrics=[
            ModelMetric(name="Strategy Confidence", value=None, target=0.70, unit="", description="Confidence in strategy recommendation"),
        ],
        api_endpoint="/v8/strategies/generate",
        api_method="POST",
        docs_path="docs/STRATEGIC_AI_GUIDE.md",
        form_fields=[],
        dataset_info="Model outputs + Business context",
        last_trained=None,
        model_path=None,
        chart_types=["strategy_comparison", "kpi_comparison"]
    ),
}


def get_all_models() -> List[AIModel]:
    """Lấy tất cả models."""
    return list(MODEL_REGISTRY.values())


def get_model(model_id: str) -> Optional[AIModel]:
    """Lấy model theo ID."""
    return MODEL_REGISTRY.get(model_id)


def get_models_by_type(model_type: ModelType) -> List[AIModel]:
    """Lấy models theo loại."""
    return [model for model in MODEL_REGISTRY.values() if model.type == model_type]


def get_models_by_status(status: ModelStatus) -> List[AIModel]:
    """Lấy models theo trạng thái."""
    return [model for model in MODEL_REGISTRY.values() if model.status == status]


def check_model_exists(model_id: str) -> bool:
    """Kiểm tra model có tồn tại không."""
    return model_id in MODEL_REGISTRY


def get_model_metrics_summary(model_id: str) -> Dict[str, Any]:
    """Lấy summary metrics của model."""
    model = get_model(model_id)
    if not model:
        return {}
    
    # Try to load actual metrics from results or model files
    # For now, return target metrics
    return {
        "model_id": model_id,
        "metrics": [
            {
                "name": metric.name,
                "value": metric.value,
                "target": metric.target,
                "unit": metric.unit,
                "description": metric.description
            }
            for metric in model.metrics
        ]
    }


# Check if model files exist
def check_model_files() -> Dict[str, bool]:
    """Kiểm tra model files có tồn tại không."""
    results = {}
    for model_id, model in MODEL_REGISTRY.items():
        if model.model_path:
            model_file = BASE_DIR / model.model_path
            results[model_id] = model_file.exists()
        else:
            results[model_id] = True  # Models without files (simulation, cognitive)
    return results

