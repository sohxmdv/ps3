import pandas as pd
import os

def load_and_merge_csvs(data_dir_path):
    # Updated to match your exact screenshot filenames
    files = {
        "equity": "equity_dataset.csv",
        "macro": "macro_dataset.csv", 
        "multi_asset": "multi_asset_dataset.csv",
        "oil": "oil_dataset.csv"
    }
    
    merged_df = None
    
    for name, filename in files.items():
        filepath = os.path.join(data_dir_path, filename)
        
        if not os.path.exists(filepath):
            print(f"Warning: File {filename} not found in {data_dir_path}.")
            continue
            
        df = pd.read_csv(filepath, parse_dates=['Date'])
        df.set_index('Date', inplace=True)

        # Rename columns to avoid the "overlap" error
        if name != "macro":
            df.columns = [f"{name}_{col}" for col in df.columns]
        
        if merged_df is None:
            merged_df = df
        else:
            merged_df = merged_df.join(df, how='outer')
            
    return merged_df