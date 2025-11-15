import numpy as np
from sklearn.ensemble import RandomForestRegressor
import sys
sys.path.append('scripts')
import train_model_revenue_forecast as rf

def test_forecast_inference_horizon():
    df = rf.load_features().head(5000)
    data = rf.prepare_features(df)
    model = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    model.fit(data['X_train'], data['y_train'])
    preds = model.predict(data['X_test'][:10])
    assert len(preds) == 10
    assert np.isfinite(preds).all(), 'Xuất hiện NaN trong dự báo'
