import pandas as pd


def clean_and_align_data(df):
    # 1. Chronological Sorting (Absolute necessity for time-series to prevent time travel)
    df = df.sort_index()

    # 2. LOCF (Last Observation Carried Forward)
    # This carries monthly macro data forward to fill the daily gaps until the next month's report.
    # It also fills in weekend gaps for asset prices.
    df = df.ffill()

    # 3. Handle Initialization NaNs (Backward Fill)
    # Indicators like SMA_10 will naturally be NaN for the first 9 days.
    # We bfill ONLY to populate these starting values for the Quant Engine.
    df = df.bfill()

    # 4. Data Validation & Cleanup
    # If any rows still have unrecoverable missing data (e.g., highly corrupted rows), drop them.
    df = df.dropna()

    # Optional: Remove duplicate indices just in case the raw CSVs had duplicate dates
    df = df[~df.index.duplicated(keep="first")]

    return df
