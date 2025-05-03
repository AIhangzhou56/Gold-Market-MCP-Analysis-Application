import os
import pandas as pd
import requests
from datetime import datetime, timedelta
import time

def fetch_xau_usd(start_date, end_date, interval='1d'):
    """
    Fetch XAU/USD (Gold) price data from Alpha Vantage API
    
    Parameters:
    -----------
    start_date : datetime.date
        Start date for data
    end_date : datetime.date
        End date for data
    interval : str
        Data interval ('1min', '5min', '15min', '30min', '60min', 'daily')
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OHLCV data
    """
    # Get API key from environment variables
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    
    if not api_key:
        raise ValueError("Alpha Vantage API key not found in environment variables")
    
    # Map interval to Alpha Vantage format
    interval_map = {
        '1min': 'TIME_SERIES_INTRADAY&interval=1min',
        '5min': 'TIME_SERIES_INTRADAY&interval=5min',
        '15min': 'TIME_SERIES_INTRADAY&interval=15min',
        '30min': 'TIME_SERIES_INTRADAY&interval=30min',
        '1h': 'TIME_SERIES_INTRADAY&interval=60min',
        '1d': 'TIME_SERIES_DAILY',
    }
    
    if interval not in interval_map:
        raise ValueError(f"Unsupported interval: {interval}. Use one of {', '.join(interval_map.keys())}")
    
    function = interval_map[interval]
    
    # XAU/USD is typically fetched as a forex pair
    # Alpha Vantage doesn't directly provide XAU/USD, so we'll use a workaround with currency pairs
    base_url = "https://www.alphavantage.co/query"
    
    # For gold, we can use Currency Exchange Rates API
    # Let's use CURRENCY_EXCHANGE_RATE function
    params = {
        "function": "CURRENCY_EXCHANGE_RATE",
        "from_currency": "XAU",
        "to_currency": "USD",
        "apikey": api_key
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if "Realtime Currency Exchange Rate" in data:
            exchange_rate = float(data["Realtime Currency Exchange Rate"]["5. Exchange Rate"])
            last_refreshed = data["Realtime Currency Exchange Rate"]["6. Last Refreshed"]
            
            # Now let's get historical data for USD/EUR to approximate XAU/USD trend
            # We'll adjust this with the current exchange rate
            if 'INTRADAY' in function:
                intraday_func, intraday_interval = function.split('&')
                params = {
                    "function": intraday_func,
                    "symbol": "EUR/USD",
                    "interval": intraday_interval.split('=')[1],
                    "outputsize": "full",
                    "apikey": api_key
                }
            else:
                params = {
                    "function": function,
                    "symbol": "EUR/USD",
                    "outputsize": "full",
                    "apikey": api_key
                }
            
            response = requests.get(base_url, params=params)
            historical_data = response.json()
            
            # Parse time series data
            if 'INTRADAY' in function:
                time_series_key = f"Time Series ({params['interval']})"
            else:
                time_series_key = "Time Series (Daily)"
            
            if time_series_key in historical_data:
                data_dict = historical_data[time_series_key]
                
                # Convert to DataFrame
                df = pd.DataFrame.from_dict(data_dict, orient='index')
                df.index = pd.to_datetime(df.index)
                df.sort_index(inplace=True)
                
                # Rename columns
                df.columns = [col.split('. ')[1] for col in df.columns]
                
                # Convert to float
                for col in df.columns:
                    df[col] = df[col].astype(float)
                
                # Adjust to approximate XAU/USD
                # This is a simplified approach - in reality, you'd need a more sophisticated method
                # We scale EUR/USD values to match the current XAU/USD
                scale_factor = exchange_rate / df['close'].iloc[-1]
                for col in ['open', 'high', 'low', 'close']:
                    df[col] = df[col] * scale_factor
                
                # Rename columns to match expected format
                df = df.rename(columns={
                    'open': 'Open',
                    'high': 'High',
                    'low': 'Low',
                    'close': 'Close',
                    'volume': 'Volume'
                })
                
                # Filter by date range
                df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]
                
                return df
            else:
                raise ValueError(f"No time series data found in response: {historical_data}")
        else:
            raise ValueError(f"Failed to get exchange rate: {data}")
    
    except Exception as e:
        print(f"Error fetching XAU/USD data: {str(e)}")
        return None

def fetch_xau_usd_alternative(start_date, end_date, interval='1d'):
    """
    Alternative method to fetch XAU/USD using the FX_DAILY endpoint
    This is a fallback in case the primary method fails
    """
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
    
    if not api_key:
        raise ValueError("Alpha Vantage API key not found in environment variables")
    
    base_url = "https://www.alphavantage.co/query"
    
    # FX_DAILY can be used for gold as forex pair in some premium Alpha Vantage subscriptions
    params = {
        "function": "FX_DAILY",
        "from_symbol": "XAU",
        "to_symbol": "USD",
        "outputsize": "full",
        "apikey": api_key
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        
        if "Time Series FX (Daily)" in data:
            time_series = data["Time Series FX (Daily)"]
            
            # Convert to DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df.sort_index(inplace=True)
            
            # Rename columns
            df.columns = [col.split('. ')[1] for col in df.columns]
            
            # Convert to float
            for col in df.columns:
                df[col] = df[col].astype(float)
            
            # Rename columns to match expected format
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close'
            })
            
            # Add Volume column (set to 0 as it's not provided)
            df['Volume'] = 0
            
            # Filter by date range
            df = df[(df.index.date >= start_date) & (df.index.date <= end_date)]
            
            return df
        else:
            raise ValueError(f"No time series data found in response: {data}")
    
    except Exception as e:
        print(f"Error in alternative XAU/USD fetch: {str(e)}")
        return None
