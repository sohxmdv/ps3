import os
from .loader import load_and_merge_csvs
from .preprocessor import clean_and_align_data


def get_clean_data(data_dir_path="../data"):
    """
    Main execution function for the Data Pipeline.
    Returns a pristine, fully aligned pandas DataFrame for the Quant Engine.
    """
    print(f"[*] Ingesting raw CSVs from {data_dir_path}...")
    raw_df = load_and_merge_csvs(data_dir_path)

    if raw_df is None or raw_df.empty:
        raise ValueError(
            "Data pipeline failed: No data could be loaded. Check file paths."
        )

    print("[*] Applying LOCF imputation and aligning macro timeline...")
    clean_df = clean_and_align_data(raw_df)

    print(
        f"[+] Data Pipeline Complete. Ready for simulation. Total aligned rows: {len(clean_df)}"
    )
    return clean_df
