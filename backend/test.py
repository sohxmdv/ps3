from data_pipeline import get_clean_data

# Adjusted path to go up one level then into data\raw
try:
    df = get_clean_data(data_dir_path="../data/raw", save_processed=True)
    print("--- SUCCESS: Data Loaded ---")
    print(df.head())
    print("\nColumns found:", df.columns.tolist())
except Exception as e:
    print(f"--- ERROR ---\n{e}")
