import pandas as pd
import sqlite3
import re

# Load the dataset
file_path = 'result/dataset_crawler-google-places_2025-12-08_13-32-02-074.csv'
df = pd.read_csv(file_path)

# --- Feature Engineering & Cleaning Steps ---

# 1. Create 'cuisine_tags'
cat_cols = [f'categories/{i}' for i in range(7)]
def aggregate_cuisines(row):
    tags = [str(row[col]) for col in cat_cols if pd.notna(row[col])]
    seen = set()
    unique_tags = [x for x in tags if not (x in seen or seen.add(x))]
    return ', '.join(unique_tags)

df['cuisine_tags'] = df.apply(aggregate_cuisines, axis=1)

# 2. Create 'primary_cuisine'
def extract_primary_cuisine(val):
    if pd.isna(val): return val
    return re.sub(r'\s+restaurant$', '', str(val), flags=re.IGNORECASE)

df['primary_cuisine'] = df['categoryName'].apply(extract_primary_cuisine)

# 3. Filter sparse columns
threshold = 0.9
df_clean = df.loc[:, df.isnull().mean() < threshold]

# 4. Standardize column names
df_clean.columns = [re.sub(r'[^a-zA-Z0-9]', '_', col).lower() for col in df_clean.columns]

# --- Export to SQLite ---

db_filename = 'result/enhance.db'
conn = sqlite3.connect(db_filename)

# Write the dataframe to the 'places' table
df_clean.to_sql('places', conn, if_exists='replace', index=False)
conn.close()

print(f"Database created: {db_filename}")