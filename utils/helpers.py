import pandas as pd
import numpy as np
import os
import json
import datetime
from typing import Dict, Any, List, Tuple, Optional, Union
import time

def format_date(date_obj):
    """
    Format date object to string
    
    Parameters:
    -----------
    date_obj : datetime.date or str
        Date object to format
        
    Returns:
    --------
    str
        Formatted date string (YYYY-MM-DD)
    """
    if isinstance(date_obj, str):
        try:
            date_obj = pd.to_datetime(date_obj).date()
        except:
            return date_obj
    
    if isinstance(date_obj, (datetime.date, datetime.datetime)):
        return date_obj.strftime('%Y-%m-%d')
    
    return str(date_obj)

def calculate_date_range(end_date, period):
    """
    Calculate start date based on end date and period
    
    Parameters:
    -----------
    end_date : datetime.date
        End date of the range
    period : str
        Period description ('1 Week', '1 Month', '3 Months', '6 Months', '1 Year', 'YTD')
        
    Returns:
    --------
    datetime.date
        Start date of the range
    """
    if period == "1 Week":
        start_date = end_date - datetime.timedelta(days=7)
    elif period == "1 Month":
        start_date = end_date - datetime.timedelta(days=30)
    elif period == "3 Months":
        start_date = end_date - datetime.timedelta(days=90)
    elif period == "6 Months":
        start_date = end_date - datetime.timedelta(days=180)
    elif period == "1 Year":
        start_date = end_date - datetime.timedelta(days=365)
    elif period == "YTD":
        start_date = datetime.date(end_date.year, 1, 1)
    else:
        # Default to 3 months
        start_date = end_date - datetime.timedelta(days=90)
    
    return start_date

def map_frequency(freq_str):
    """
    Map user-friendly frequency to API format
    
    Parameters:
    -----------
    freq_str : str
        User-friendly frequency ('1 Minute', '5 Minutes', '15 Minutes', '1 Hour', 'Daily')
        
    Returns:
    --------
    dict
        Dictionary mapping frequency strings for different APIs
    """
    freq_map = {
        '1 Minute': {
            'yfinance': '1m',
            'alpha_vantage': '1min',
            'tushare': '1min'
        },
        '5 Minutes': {
            'yfinance': '5m',
            'alpha_vantage': '5min',
            'tushare': '5min'
        },
        '15 Minutes': {
            'yfinance': '15m',
            'alpha_vantage': '15min',
            'tushare': '15min'
        },
        '30 Minutes': {
            'yfinance': '30m',
            'alpha_vantage': '30min',
            'tushare': '30min'
        },
        '1 Hour': {
            'yfinance': '1h',
            'alpha_vantage': '60min',
            'tushare': '1h'
        },
        'Daily': {
            'yfinance': '1d',
            'alpha_vantage': 'daily',
            'tushare': '1d'
        }
    }
    
    return freq_map.get(freq_str, {'yfinance': '1d', 'alpha_vantage': 'daily', 'tushare': '1d'})

def check_api_keys():
    """
    Check if necessary API keys are available in environment variables
    
    Returns:
    --------
    dict
        Dictionary with API key statuses
    """
    api_keys = {
        'alpha_vantage': os.getenv('ALPHA_VANTAGE_API_KEY'),
        'tushare': os.getenv('TUSHARE_API_KEY')
    }
    
    api_status = {
        'alpha_vantage': api_keys['alpha_vantage'] is not None and len(api_keys['alpha_vantage']) > 0,
        'tushare': api_keys['tushare'] is not None and len(api_keys['tushare']) > 0
    }
    
    return api_status

def load_config(config_file='config.json'):
    """
    Load configuration from file
    
    Parameters:
    -----------
    config_file : str
        Path to configuration file
        
    Returns:
    --------
    dict
        Configuration dictionary
    """
    # Default configuration
    default_config = {
        'default_period': '3 Months',
        'default_frequency': 'Daily',
        'default_indicators': ['VWAP', 'MACD', 'RSI', 'Bollinger Bands'],
        'default_strategy': 'Mean Reversion',
        'chart_height': 600,
        'max_datapoints': 1000
    }
    
    # Try to load from file
    if os.path.isfile(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            return {**default_config, **config}  # Merge with defaults
        except:
            return default_config
    
    return default_config

def save_config(config, config_file='config.json'):
    """
    Save configuration to file
    
    Parameters:
    -----------
    config : dict
        Configuration dictionary
    config_file : str
        Path to configuration file
        
    Returns:
    --------
    bool
        True if saved successfully, False otherwise
    """
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)
        return True
    except:
        return False

def resample_data(df, freq):
    """
    Resample time series data to a different frequency
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    freq : str
        Target frequency ('1min', '5min', '15min', '30min', '1h', '1d')
        
    Returns:
    --------
    pandas.DataFrame
        Resampled data
    """
    if df is None or df.empty:
        return df
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except:
            return df
    
    # Map to pandas frequency string
    freq_map = {
        '1min': '1T',
        '5min': '5T',
        '15min': '15T',
        '30min': '30T',
        '1h': '1H',
        '1d': 'D'
    }
    
    pd_freq = freq_map.get(freq, 'D')
    
    # Resample OHLCV data
    resampled = df.resample(pd_freq).agg({
        'Open': 'first',
        'High': 'max',
        'Low': 'min',
        'Close': 'last',
        'Volume': 'sum'
    })
    
    # Handle other columns if present
    for col in df.columns:
        if col not in ['Open', 'High', 'Low', 'Close', 'Volume']:
            if col in ['OpenInterest', 'Contract']:
                resampled[col] = df[col].resample(pd_freq).last()
    
    return resampled.dropna()

def create_asset_comparison(data_dict):
    """
    Create comparison data between multiple assets
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with asset names as keys and DataFrames as values
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with comparison data
    """
    if not data_dict:
        return None
    
    comparison_data = []
    
    for asset_name, df in data_dict.items():
        if df is not None and not df.empty:
            latest_close = df['Close'].iloc[-1]
            change_1d = df['Close'].pct_change().iloc[-1] * 100
            change_5d = df['Close'].pct_change(5).iloc[-1] * 100
            change_1m = df['Close'].pct_change(20).iloc[-1] * 100
            
            # Calculate volatility
            volatility = df['Close'].pct_change().std() * np.sqrt(252) * 100
            
            # Calculate RSI if available
            rsi = df['RSI'].iloc[-1] if 'RSI' in df.columns else None
            
            # Calculate MACD signal if available
            macd_signal = None
            if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
                macd = df['MACD'].iloc[-1]
                macd_signal_val = df['MACD_Signal'].iloc[-1]
                macd_signal = "Bullish" if macd > macd_signal_val else "Bearish"
            
            comparison_data.append({
                'Asset': asset_name,
                'Last Price': latest_close,
                '1D Change (%)': change_1d,
                '5D Change (%)': change_5d,
                '1M Change (%)': change_1m,
                'Volatility (%)': volatility,
                'RSI': rsi,
                'MACD Signal': macd_signal
            })
    
    if not comparison_data:
        return None
    
    return pd.DataFrame(comparison_data)

def rate_limit_handler(func):
    """
    Decorator to handle rate limits in API calls
    
    Parameters:
    -----------
    func : function
        Function to decorate
        
    Returns:
    --------
    function
        Decorated function
    """
    def wrapper(*args, **kwargs):
        max_retries = 3
        retry_count = 0
        base_delay = 2  # seconds
        
        while retry_count < max_retries:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                    retry_count += 1
                    if retry_count < max_retries:
                        delay = base_delay * (2 ** (retry_count - 1))  # Exponential backoff
                        print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                        time.sleep(delay)
                    else:
                        print("Max retries exceeded for rate limit.")
                        raise
                else:
                    raise
    
    return wrapper

def filter_dataframe_by_date(df, start_date, end_date):
    """
    Filter DataFrame by date range
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with datetime index
    start_date : datetime.date
        Start date for filtering
    end_date : datetime.date
        End date for filtering
        
    Returns:
    --------
    pandas.DataFrame
        Filtered DataFrame
    """
    if df is None or df.empty:
        return df
    
    # Ensure index is datetime
    if not isinstance(df.index, pd.DatetimeIndex):
        try:
            df.index = pd.to_datetime(df.index)
        except:
            return df
    
    # Convert dates to timestamps if they are date objects
    if isinstance(start_date, datetime.date) and not isinstance(start_date, datetime.datetime):
        start_date = pd.Timestamp(start_date)
    
    if isinstance(end_date, datetime.date) and not isinstance(end_date, datetime.datetime):
        end_date = pd.Timestamp(end_date)
    
    # Filter the DataFrame
    mask = (df.index >= start_date) & (df.index <= end_date)
    return df.loc[mask]

def get_common_date_range(dataframes):
    """
    Get common date range across multiple dataframes
    
    Parameters:
    -----------
    dataframes : list
        List of pandas DataFrames
        
    Returns:
    --------
    tuple
        (start_date, end_date) as datetime objects
    """
    if not dataframes:
        return None, None
    
    # Filter out None or empty dataframes
    valid_dfs = [df for df in dataframes if df is not None and not df.empty]
    
    if not valid_dfs:
        return None, None
    
    # Get min and max dates from each dataframe
    start_dates = [df.index.min() for df in valid_dfs]
    end_dates = [df.index.max() for df in valid_dfs]
    
    # Find common range
    common_start = max(start_dates)
    common_end = min(end_dates)
    
    return common_start, common_end
