import pandas as pd
from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
import sys
sys.path.append('scripts')
import train_model_logistics_delay as ld

def test_late_delivery_end_to_end_subset():
    df = ld.load_features().head(2000)
    data = ld.prepare_features(df)
    model = LogisticRegression(max_iter=200)
    model.fit(data['X_train'], data['y_train'])
    preds = model.predict(data['X_test'])
    f1 = f1_score(data['y_test'], preds)
    assert f1 > 0.85, 'F1 trên subset quá thấp'
