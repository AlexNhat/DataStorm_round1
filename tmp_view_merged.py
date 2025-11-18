import pandas as pd
from pathlib import Path
path = Path("data/merged/supplychain_weather_merged_global.csv")
df = pd.read_csv(path, nrows=5)
print('Columns:', df.columns.tolist())
print(df.head().to_string())
