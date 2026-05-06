# backend/data_pipeline/loader.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def get_clean_data() -> pd.DataFrame:
    """Generates 100 days of dummy market data for immediate API testing."""
    dates = [datetime(2020, 1, 1) + timedelta(days=i) for i in range(100)]
    
    # Generate a fake price that trends upward with some noise
    prices = 100 + np.cumsum(np.random.normal(0.1, 1.5, 100))
    
    df = pd.DataFrame({'Date': dates, 'Close': prices})
    df.set_index('Date', inplace=True)
    
    # Add necessary columns for your SignalGenerator & RiskManager
    df['Returns'] = df['Close'].pct_change()
    df['SMA_10'] = df['Close'].rolling(window=10).mean()
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['RSI'] = 50.0  # Hardcoded dummy RSI for now
    
    # Fill NaN values to prevent engine crashes on day 1
    df.fillna(method='bfill', inplace=True) 
    return df