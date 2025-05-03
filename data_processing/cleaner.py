import pandas as pd
import numpy as np

def clean_data(df):
    """
    Clean and preprocess market data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Raw market data with OHLCV columns
        
    Returns:
    --------
    pandas.DataFrame
        Cleaned data
    """
    if df is None or df.empty:
        return df
    
    # Make a copy to avoid modifying the original
    cleaned_df = df.copy()
    
    # Ensure index is datetime
    if not isinstance(cleaned_df.index, pd.DatetimeIndex):
        try:
            # Try to convert the index to datetime if it's not already
            cleaned_df.index = pd.to_datetime(cleaned_df.index)
        except Exception as e:
            print(f"Error converting index to datetime: {str(e)}")
            # If there's a datetime column, use it as index
            if 'datetime' in cleaned_df.columns:
                cleaned_df.set_index('datetime', inplace=True)
            elif 'date' in cleaned_df.columns:
                cleaned_df.set_index('date', inplace=True)
    
    # Sort index
    cleaned_df.sort_index(inplace=True)
    
    # Ensure column names are consistent
    column_mapping = {
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume',
        'Open': 'Open',
        'High': 'High',
        'Low': 'Low',
        'Close': 'Close',
        'Volume': 'Volume',
        'Adj Close': 'Close',
        'OPEN': 'Open',
        'HIGH': 'High',
        'LOW': 'Low',
        'CLOSE': 'Close',
        'VOLUME': 'Volume'
    }
    
    # Rename columns based on the mapping
    cleaned_df.rename(columns=column_mapping, inplace=True)
    
    # Ensure OHLCV columns exist, set to NaN if missing
    for col in ['Open', 'High', 'Low', 'Close', 'Volume']:
        if col not in cleaned_df.columns:
            cleaned_df[col] = np.nan
    
    # Handle missing values
    # Forward fill Open, High, Low, Close
    cleaned_df[['Open', 'High', 'Low', 'Close']] = cleaned_df[['Open', 'High', 'Low', 'Close']].ffill()
    
    # Fill remaining NaNs with 0 for Volume
    cleaned_df['Volume'] = cleaned_df['Volume'].fillna(0)
    
    # Remove rows with NaN in OHLC columns (can't be imputed)
    cleaned_df = cleaned_df.dropna(subset=['Open', 'High', 'Low', 'Close'])
    
    # Fix data inconsistencies
    # Ensure High >= Low, High >= Open, High >= Close
    cleaned_df['High'] = cleaned_df[['High', 'Open', 'Close']].max(axis=1)
    
    # Ensure Low <= Open, Low <= Close
    cleaned_df['Low'] = cleaned_df[['Low', 'Open', 'Close']].min(axis=1)
    
    # Handle outliers - clip extreme values based on rolling median
    for col in ['Open', 'High', 'Low', 'Close']:
        median = cleaned_df[col].median()
        std = cleaned_df[col].std()
        lower_bound = median - 5 * std
        upper_bound = median + 5 * std
        cleaned_df[col] = cleaned_df[col].clip(lower=lower_bound, upper=upper_bound)
    
    # Ensure Volume is non-negative
    cleaned_df['Volume'] = cleaned_df['Volume'].clip(lower=0)
    
    # Add column for returns
    cleaned_df['Returns'] = cleaned_df['Close'].pct_change()
    
    # Add column for log returns
    cleaned_df['LogReturns'] = np.log(cleaned_df['Close'] / cleaned_df['Close'].shift(1))
    
    # Remove rows with infinite values
    cleaned_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    cleaned_df.dropna(subset=['Returns', 'LogReturns'], inplace=True)
    
    return cleaned_df

def remove_duplicates(df):
    """
    Remove duplicate entries in the dataset
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Market data
        
    Returns:
    --------
    pandas.DataFrame
        Data with duplicates removed
    """
    if df is None or df.empty:
        return df
    
    # Check for duplicate indices
    if df.index.duplicated().any():
        print(f"Found {df.index.duplicated().sum()} duplicate timestamps")
        
        # Keep the last occurrence of each duplicate
        df = df[~df.index.duplicated(keep='last')]
    
    return df

def handle_gaps(df, freq=None):
    """
    Handle gaps in time series data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Market data
    freq : str
        Frequency string for reindexing (e.g., '1D', '1H', '1min')
        
    Returns:
    --------
    pandas.DataFrame
        Data with gaps handled
    """
    if df is None or df.empty:
        return df
    
    # If frequency is not provided, try to infer it
    if freq is None:
        if len(df) > 1:
            # Calculate most common time delta
            time_deltas = df.index[1:] - df.index[:-1]
            most_common_delta = pd.Series(time_deltas).value_counts().index[0]
            
            # Convert to pandas frequency string
            seconds = most_common_delta.total_seconds()
            if seconds < 60:
                freq = f"{int(seconds)}S"
            elif seconds < 3600:
                freq = f"{int(seconds/60)}min"
            elif seconds < 86400:
                freq = f"{int(seconds/3600)}H"
            else:
                freq = f"{int(seconds/86400)}D"
        else:
            # Default to daily if we can't infer
            freq = '1D'
    
    # Create a continuous index
    full_idx = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq=freq
    )
    
    # Reindex the dataframe
    reindexed_df = df.reindex(full_idx)
    
    # For OHLC, forward fill
    reindexed_df[['Open', 'High', 'Low', 'Close']] = reindexed_df[['Open', 'High', 'Low', 'Close']].ffill()
    
    # For Volume, fill with 0
    reindexed_df['Volume'] = reindexed_df['Volume'].fillna(0)
    
    # Recalculate returns based on filled data
    reindexed_df['Returns'] = reindexed_df['Close'].pct_change()
    reindexed_df['LogReturns'] = np.log(reindexed_df['Close'] / reindexed_df['Close'].shift(1))
    
    return reindexed_df

def adjust_for_splits_and_dividends(df):
    """
    Adjust OHLC data for stock splits and dividends
    
    Parameters:
    -----------
    df : pandas.DataFrame
        Market data with possible Adj Close column
        
    Returns:
    --------
    pandas.DataFrame
        Split and dividend adjusted data
    """
    if df is None or df.empty:
        return df
    
    # Check if we have Adj Close column
    if 'Adj Close' in df.columns:
        # Calculate the adjustment ratio
        adj_ratio = df['Adj Close'] / df['Close']
        
        # Adjust OHLC
        df['Open'] = df['Open'] * adj_ratio
        df['High'] = df['High'] * adj_ratio
        df['Low'] = df['Low'] * adj_ratio
        df['Close'] = df['Adj Close']
        
        # Drop the Adj Close column
        df.drop('Adj Close', axis=1, inplace=True)
    
    return df
