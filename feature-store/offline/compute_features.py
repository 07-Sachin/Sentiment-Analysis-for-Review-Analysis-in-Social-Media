import pandas as pd

# Step 1: Read raw data
df = pd.read_csv("../data/raw_data.csv")

# Step 2: Create a new feature
df["is_active"] = df["clicks"].apply(lambda x: 1 if x > 10 else 0)

# Step 3: Save computed features
df.to_csv("features.csv", index=False)

print("Features computed successfully")
