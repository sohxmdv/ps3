import os
from .loader import load_and_merge_csvs
from .preprocessor import clean_and_align_data


def get_clean_data(data_dir_path="../data/raw", save_processed=False):
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

    # --- NEW: Save physical file for Judges/Audit ---
    if save_processed:
        # We save it one level up from 'raw' into the main 'data' folder
        output_path = os.path.join(data_dir_path, "../processed_cleaned_data.csv")
        clean_df.to_csv(output_path)
        print(f"[!] Audit file generated: {output_path}")

    print(
        f"[+] Data Pipeline Complete. Ready for simulation. Total aligned rows: {len(clean_df)}"
    )
    return clean_df
