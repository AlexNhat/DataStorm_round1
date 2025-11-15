import pandas as pd
from pathlib import Path
path = Path("data/geocoded_weather.csv")
df = pd.read_csv(path, nrows=1)
print(df.columns.tolist())
