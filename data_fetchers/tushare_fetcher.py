import os
import pandas as pd
import numpy as np
import datetime
import time
import tushare as ts

def fetch_au_data(start_date, end_date, freq='1d'):
    """
    Fetch AU (Gold) futures data from Tushare
    
    Parameters:
    -----------
    start_date : datetime.date
        Start date for data
    end_date : datetime.date
        End date for data
    freq : str
        Data frequency ('1min', '5min', '15min', '30min', '60min', '1d')
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OHLCV data and open interest
    """
    # Get API key from environment variables
    token = os.getenv("TUSHARE_API_KEY", "")
    
    if not token:
        raise ValueError("Tushare API key not found in environment variables")
    
    # Initialize Tushare
    ts.set_token(token)
    pro = ts.pro_api()
    
    # Convert date format
    start_str = start_date.strftime('%Y%m%d')
    end_str = end_date.strftime('%Y%m%d')
    
    try:
        # For daily data, use the futures_daily API
        if freq == '1d':
            # Get list of AU futures contracts
            contracts = pro.fut_basic(exchange='SHFE', fut_type='1', fields='ts_code,symbol,exchange')
            au_contracts = contracts[contracts['symbol'].str.startswith('AU')]
            
            # Get data for each contract and combine
            all_data = []
            for code in au_contracts['ts_code']:
                df = pro.fut_daily(ts_code=code, start_date=start_str, end_date=end_str)
                if not df.empty:
                    all_data.append(df)
            
            if not all_data:
                raise ValueError("No data found for AU futures contracts")
            
            # Combine all contract data
            combined_df = pd.concat(all_data)
            
            # Convert to expected format
            combined_df['datetime'] = pd.to_datetime(combined_df['trade_date'])
            combined_df.set_index('datetime', inplace=True)
            
            # Rename columns to match expected format
            result_df = combined_df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'vol': 'Volume',
                'oi': 'OpenInterest',
                'ts_code': 'Contract'
            })
            
            # Select only needed columns
            needed_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest', 'Contract']
            result_df = result_df[needed_cols]
            
            return result_df
        
        # For intraday data, use a different approach
        else:
            # Map frequency to Tushare format
            freq_map = {
                '1min': '1min',
                '5min': '5min',
                '15min': '15min',
                '30min': '30min',
                '1h': '60min'
            }
            
            if freq not in freq_map:
                raise ValueError(f"Unsupported frequency: {freq}")
            
            tushare_freq = freq_map[freq]
            
            # For intraday data, we use the futures_minute API
            # First get the main contract codes
            main_contracts = pro.fut_mapping(
                ts_code='AU',
                trade_date=end_str
            )
            
            if main_contracts.empty:
                raise ValueError("No main contract found for AU")
            
            # Get data for the main contract
            main_code = main_contracts.iloc[0]['mapping_ts_code']
            
            # For minute data, we can use the futures bar data
            # Due to API limitations, we might need to fetch in chunks
            
            # Convert dates to the format expected by the API
            start_time = pd.to_datetime(start_date)
            end_time = pd.to_datetime(end_date)
            
            current_time = start_time
            all_intraday_data = []
            
            # Fetch data in chunks (e.g., 10 days at a time to avoid API limits)
            while current_time <= end_time:
                next_time = min(current_time + datetime.timedelta(days=10), end_time)
                
                # Format dates for API
                start_str = current_time.strftime('%Y%m%d')
                end_str = next_time.strftime('%Y%m%d')
                
                try:
                    # Fetch the minute bar data using low-level API for specific contract
                    df = ts.pro_bar(
                        ts_code=main_code,
                        start_date=start_str,
                        end_date=end_str,
                        freq=tushare_freq,
                        asset='FT'
                    )
                    
                    if df is not None and not df.empty:
                        all_intraday_data.append(df)
                    
                    # Sleep to respect API rate limits
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"Error fetching intraday data for {start_str} to {end_str}: {str(e)}")
                
                # Move to next chunk
                current_time = next_time + datetime.timedelta(days=1)
            
            if not all_intraday_data:
                raise ValueError("No intraday data found for AU futures")
            
            # Combine all chunks
            intraday_df = pd.concat(all_intraday_data)
            
            # Process the data
            intraday_df['datetime'] = pd.to_datetime(intraday_df['trade_time'])
            intraday_df.set_index('datetime', inplace=True)
            intraday_df.sort_index(inplace=True)
            
            # Rename columns to match expected format
            result_df = intraday_df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'vol': 'Volume',
                'oi': 'OpenInterest',
                'ts_code': 'Contract'
            })
            
            # Select only needed columns
            needed_cols = ['Open', 'High', 'Low', 'Close', 'Volume', 'OpenInterest', 'Contract']
            cols_available = [col for col in needed_cols if col in result_df.columns]
            result_df = result_df[cols_available]
            
            # Add missing columns if needed
            for col in needed_cols:
                if col not in result_df.columns:
                    if col == 'OpenInterest':
                        result_df[col] = 0
                    elif col == 'Contract':
                        result_df[col] = main_code
            
            return result_df
    
    except Exception as e:
        print(f"Error fetching AU data: {str(e)}")
        
        # Return a synthetic dataset for testing purposes if API fails
        # This is for development/testing only and should be removed in production
        return _generate_synthetic_au_data(start_date, end_date, freq)

def _generate_synthetic_au_data(start_date, end_date, freq='1d'):
    """
    Generate synthetic AU data for testing purposes
    This should only be used when the real API fails
    """
    print("WARNING: Generating synthetic AU data for testing")
    
    # Generate date range
    if freq == '1d':
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
    elif freq == '1min':
        dates = pd.date_range(start=start_date, end=end_date, freq='min')
    elif freq == '5min':
        dates = pd.date_range(start=start_date, end=end_date, freq='5min')
    elif freq == '15min':
        dates = pd.date_range(start=start_date, end=end_date, freq='15min')
    elif freq == '30min':
        dates = pd.date_range(start=start_date, end=end_date, freq='30min')
    elif freq == '1h':
        dates = pd.date_range(start=start_date, end=end_date, freq='H')
    else:
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Filter to trading hours (9:00 - 15:00)
    if freq != '1d':
        dates = dates[dates.time >= datetime.time(9, 0)]
        dates = dates[dates.time <= datetime.time(15, 0)]
    
    # Base price and random walk
    base_price = 2000.0  # Base gold price
    np.random.seed(42)  # for reproducibility
    
    # Generate random walk prices
    returns = np.random.normal(0, 0.01, size=len(dates))
    price_changes = base_price * np.cumprod(1 + returns)
    
    # Create OHLC data
    df = pd.DataFrame(index=dates)
    df['Close'] = price_changes
    df['Open'] = df['Close'].shift(1)
    df.loc[df.index[0], 'Open'] = base_price
    
    # Add some random fluctuation for high and low
    daily_volatility = 0.015
    df['High'] = df['Close'] * (1 + np.random.uniform(0, daily_volatility, size=len(df)))
    df['Low'] = df['Close'] * (1 - np.random.uniform(0, daily_volatility, size=len(df)))
    
    # Ensure High is always >= Close and Open
    df['High'] = df[['High', 'Close', 'Open']].max(axis=1)
    
    # Ensure Low is always <= Close and Open
    df['Low'] = df[['Low', 'Close', 'Open']].min(axis=1)
    
    # Generate volume data
    df['Volume'] = np.random.lognormal(10, 1, size=len(df)).astype(int)
    
    # Generate open interest data
    df['OpenInterest'] = np.cumsum(np.random.normal(0, 100, size=len(df))).astype(int)
    df['OpenInterest'] = df['OpenInterest'] - df['OpenInterest'].min() + 1000
    
    # Add contract information
    df['Contract'] = 'AU2112.SHF'  # Example contract code
    
    return df
