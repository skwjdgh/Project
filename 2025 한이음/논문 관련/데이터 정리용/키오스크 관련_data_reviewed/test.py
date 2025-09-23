import pandas as pd
df0 = pd.read_csv("input_data/노이즈0 시드0.csv")
print(df0.head())
print(df0["match_b"].value_counts(normalize=True))