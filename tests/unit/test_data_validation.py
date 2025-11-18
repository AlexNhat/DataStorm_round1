import pandas as pd
from pathlib import Path

def test_required_columns_low_nan_ratio():
    df = pd.read_csv(Path('data') / 'DataCoSupplyChainDataset.csv', encoding='latin-1')
    required = ['Order Id', 'Order Date', 'Sales']
    nan_ratio = df[required].isna().mean()
    assert all(nan_ratio < 0.01), f"Tỉ lệ NaN vượt 1%: {nan_ratio.to_dict()}"

def test_country_vocab_is_string():
    df = pd.read_csv(Path('data') / 'DataCoSupplyChainDataset.csv', encoding='latin-1')
    countries = df['Order Country'].dropna()
    assert countries.apply(lambda c: isinstance(c, str)).all(), "Phát hiện country không phải chuỗi"
