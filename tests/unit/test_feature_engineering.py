import pandas as pd
from pathlib import Path
import numpy as np
import sys
sys.path.append('scripts')
from preprocess_and_build_feature_store import add_time_features, calculate_rfm_features

def test_lead_time_calculation():
    df = pd.DataFrame({
        'Days for shipment (scheduled)': [5, 3],
        'Days for shipping (real)': [4, 5]
    })
    df['lead_time'] = df['Days for shipment (scheduled)'] - df['Days for shipping (real)']
    assert df['lead_time'].tolist() == [1, -2]

def test_add_time_features_outputs_columns():
    df = pd.DataFrame({'order date (DateOrders)': ['2020-01-05', '2020-07-15']})
    result = add_time_features(df, 'order date (DateOrders)')
    for col in ['year','month','day_of_week','is_weekend','month_sin','month_cos']:
        assert col in result.columns

def test_rfm_computation():
    data = pd.DataFrame({
        'Order Customer Id': ['c1','c1','c2'],
        'order date (DateOrders)': pd.to_datetime(['2020-01-01','2020-01-10','2020-01-05']),
        'Order Id': [1,2,3],
        'Sales': [100,200,300]
    })
    snapshot = pd.Timestamp('2020-02-01')
    rfm = calculate_rfm_features(data, snapshot)
    recency_c1 = rfm.loc[rfm['customer_id']=='c1','rfm_recency'].iloc[0]
    assert recency_c1 == (snapshot - pd.Timestamp('2020-01-10')).days
