import pandas as pd
from pathlib import Path
path = Path("data/DataCoSupplyChainDataset.csv")
df = pd.read_csv(path, encoding='latin-1', nrows=1)
print(df.columns.tolist())
