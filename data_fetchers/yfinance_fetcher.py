import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta

def fetch_comex_gc(start_date, end_date, interval='1d'):
    """
    Fetch COMEX Gold Futures (GC) data from Yahoo Finance
    
    Parameters:
    -----------
    start_date : datetime.date
        Start date for data
    end_date : datetime.date
        End date for data
    interval : str
        Data interval ('1min', '5min', '15min', '30min', '60min', '1d')
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OHLCV data
    """
    # Map interval to Yahoo Finance format
    interval_map = {
        '1min': '1m',
        '5min': '5m',
        '15min': '15m',
        '30min': '30m',
        '1h': '1h',
        '1d': '1d'
    }
    
    if interval not in interval_map:
        raise ValueError(f"Unsupported interval: {interval}. Use one of {', '.join(interval_map.keys())}")
    
    yf_interval = interval_map[interval]
    
    # For intraday data, Yahoo only provides a limited time window
    # If requesting minute data for a large date range, we need to adjust
    if yf_interval in ['1m', '5m', '15m'] and (end_date - start_date).days > 7:
        print(f"Warning: Yahoo Finance only provides {yf_interval} data for the last 7 days.")
        print(f"Adjusting start date to {end_date - timedelta(days=7)}")
        start_date = end_date - timedelta(days=7)
    elif yf_interval in ['30m', '1h'] and (end_date - start_date).days > 60:
        print(f"Warning: Yahoo Finance only provides {yf_interval} data for the last 60 days.")
        print(f"Adjusting start date to {end_date - timedelta(days=60)}")
        start_date = end_date - timedelta(days=60)
    
    try:
        # Determine the appropriate contract to use
        # For simplicity, use the continuous contract ticker
        ticker = "GC=F"
        
        # Download data
        data = yf.download(
            ticker,
            start=start_date,
            end=end_date + timedelta(days=1),  # Add a day to include end_date
            interval=yf_interval,
            auto_adjust=True,
            progress=False
        )
        
        if data.empty:
            print("No data returned from Yahoo Finance")
            return None
        
        # Rename columns to standardized format
        data = data.rename(columns={
            'Open': 'Open',
            'High': 'High',
            'Low': 'Low',
            'Close': 'Close',
            'Volume': 'Volume'
        })
        
        # Add contract information
        data['Contract'] = ticker
        
        # Handle case where volume might be missing
        if 'Volume' not in data.columns:
            data['Volume'] = 0
        
        return data
    
    except Exception as e:
        print(f"Error fetching COMEX GC data: {str(e)}")
        return None

def fetch_multi_contract_gc(start_date, end_date, interval='1d'):
    """
    Fetch multiple COMEX Gold Futures contracts and return the most active one
    This is useful for getting data with the correct contract rollover
    
    Parameters:
    -----------
    start_date : datetime.date
        Start date for data
    end_date : datetime.date
        End date for data
    interval : str
        Data interval ('1d' only for multi-contract fetch)
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OHLCV data
    """
    if interval != '1d':
        print(f"Warning: Multi-contract fetch only supports daily interval. Using '1d'.")
    
    # COMEX Gold Futures contract months are typically:
    # February, April, June, August, October, December
    
    # Calculate the contracts we need to cover the date range
    all_data = []
    
    # Generate a list of contracts that might be active during the date range
    start_year = start_date.year
    end_year = end_date.year
    
    contract_months = ['02', '04', '06', '08', '10', '12']  # Feb, Apr, Jun, Aug, Oct, Dec
    contract_codes = {
        '02': 'G', '04': 'J', '06': 'M', '08': 'Q', '10': 'V', '12': 'Z'
    }
    
    contracts = []
    for year in range(start_year, end_year + 2):  # +2 to include contracts that start in end_year
        year_code = str(year)[-2:]  # Last two digits of year
        for month in contract_months:
            contract_symbol = f"GC{contract_codes[month]}{year_code}"
            contracts.append(contract_symbol)
    
    # Fetch data for each contract
    for contract in contracts:
        try:
            ticker = f"{contract}.CMX"
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date + timedelta(days=1),
                interval='1d',
                auto_adjust=True,
                progress=False
            )
            
            if not data.empty:
                data['Contract'] = contract
                all_data.append(data)
        except Exception as e:
            print(f"Error fetching data for {contract}: {str(e)}")
    
    if not all_data:
        print("No data returned for any contract")
        return None
    
    # Combine all contract data
    combined_data = pd.concat(all_data)
    combined_data.sort_index(inplace=True)
    
    # Identify the most active contract for each day based on volume
    # This is a simplified approach - in practice, you might want to use 
    # a more sophisticated approach for contract rollover
    highest_volume = combined_data.groupby([combined_data.index.date, 'Contract'])['Volume'].sum()
    highest_volume = highest_volume.reset_index()
    daily_max = highest_volume.groupby('level_0')['Volume'].transform('max')
    highest_volume = highest_volume[highest_volume['Volume'] == daily_max]
    
    # For each date, select the contract with the highest volume
    result_data = []
    for date, contract in zip(highest_volume['level_0'], highest_volume['Contract']):
        date_data = combined_data[(combined_data.index.date == date) & (combined_data['Contract'] == contract)]
        result_data.append(date_data)
    
    if not result_data:
        print("No data after filtering for most active contracts")
        return None
    
    # Combine the filtered data
    result_df = pd.concat(result_data)
    result_df.sort_index(inplace=True)
    
    return result_df
