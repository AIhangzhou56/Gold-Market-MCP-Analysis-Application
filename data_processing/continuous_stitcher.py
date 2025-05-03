import pandas as pd
import numpy as np

def stitch_continuous_series(futures_data, volume_threshold=0.5):
    """
    Create a continuous futures series by properly stitching together contracts.
    
    Parameters:
    -----------
    futures_data : pandas.DataFrame
        DataFrame with futures data including a 'Contract' column
    volume_threshold : float
        Threshold for volume comparison to determine rollover points (0-1)
        
    Returns:
    --------
    pandas.DataFrame
        Continuous futures series
    """
    if futures_data is None or futures_data.empty:
        return futures_data
    
    # Check if Contract column exists
    if 'Contract' not in futures_data.columns:
        print("Contract column not found, returning original data")
        return futures_data
    
    # Sort by date
    futures_data = futures_data.sort_index()
    
    # Group data by contract
    contracts = futures_data['Contract'].unique()
    
    if len(contracts) <= 1:
        # Only one contract, no need for stitching
        return futures_data
    
    # Identify active contracts for each day based on volume
    daily_volumes = futures_data.groupby([futures_data.index.date, 'Contract'])['Volume'].sum()
    daily_volumes = daily_volumes.reset_index()
    daily_volumes.columns = ['Date', 'Contract', 'Volume']
    
    # For each date, calculate relative volume
    date_groups = daily_volumes.groupby('Date')
    relative_volumes = []
    
    for date, group in date_groups:
        total_volume = group['Volume'].sum()
        if total_volume > 0:
            for _, row in group.iterrows():
                relative_volumes.append({
                    'Date': date,
                    'Contract': row['Contract'],
                    'Volume': row['Volume'],
                    'RelativeVolume': row['Volume'] / total_volume
                })
        else:
            # If no volume, use equal weight
            for _, row in group.iterrows():
                relative_volumes.append({
                    'Date': date,
                    'Contract': row['Contract'],
                    'Volume': row['Volume'],
                    'RelativeVolume': 1.0 / len(group)
                })
    
    volume_df = pd.DataFrame(relative_volumes)
    
    # Determine the primary contract for each date
    # A contract becomes primary when its relative volume exceeds the threshold
    primary_contracts = []
    current_primary = None
    
    # Sort by date to process chronologically
    dates = sorted(volume_df['Date'].unique())
    
    for date in dates:
        date_data = volume_df[volume_df['Date'] == date]
        max_vol_contract = date_data.loc[date_data['RelativeVolume'].idxmax()]['Contract']
        max_vol = date_data.loc[date_data['RelativeVolume'].idxmax()]['RelativeVolume']
        
        if current_primary is None:
            # First date, set primary to the highest volume contract
            current_primary = max_vol_contract
        elif max_vol >= volume_threshold and max_vol_contract != current_primary:
            # If a new contract exceeds the threshold, switch to it
            current_primary = max_vol_contract
        
        primary_contracts.append({
            'Date': date,
            'PrimaryContract': current_primary
        })
    
    primary_df = pd.DataFrame(primary_contracts)
    
    # Merge primary contract info back to original data
    futures_data = futures_data.reset_index()
    futures_data['Date'] = futures_data['datetime'].dt.date
    futures_data = pd.merge(futures_data, primary_df, on='Date', how='left')
    
    # Filter data to include only primary contracts
    continuous_data = futures_data[futures_data['Contract'] == futures_data['PrimaryContract']]
    
    # Calculate adjustment factors for price gaps at rollover points
    continuous_data = continuous_data.sort_values('datetime')
    continuous_data.reset_index(drop=True, inplace=True)
    
    # Find rollover points
    rollover_points = continuous_data['PrimaryContract'].shift() != continuous_data['PrimaryContract']
    rollover_indices = continuous_data.index[rollover_points]
    
    # Backward adjustment (adjust older contracts to match newer ones)
    adjusted_prices = continuous_data[['Open', 'High', 'Low', 'Close']].copy()
    adjustment_factor = 1.0
    
    for i in range(len(rollover_indices) - 1, -1, -1):
        idx = rollover_indices[i]
        if idx > 0:
            # Calculate ratio between new and old contract at rollover
            old_close = continuous_data.loc[idx - 1, 'Close']
            new_close = continuous_data.loc[idx, 'Close']
            
            if old_close != 0 and not np.isnan(old_close) and not np.isnan(new_close):
                # Calculate adjustment for this rollover
                this_adjustment = new_close / old_close
                
                # Apply adjustment to all previous data
                adjustment_factor *= this_adjustment
                mask = continuous_data.index < idx
                for col in ['Open', 'High', 'Low', 'Close']:
                    adjusted_prices.loc[mask, col] = continuous_data.loc[mask, col] * adjustment_factor
    
    # Update the dataframe with adjusted prices
    continuous_data[['Open', 'High', 'Low', 'Close']] = adjusted_prices
    
    # Clean up and set index back to datetime
    continuous_data.drop(['Date', 'PrimaryContract'], axis=1, inplace=True)
    continuous_data.set_index('datetime', inplace=True)
    
    # Recalculate returns based on adjusted prices
    continuous_data['Returns'] = continuous_data['Close'].pct_change()
    continuous_data['LogReturns'] = np.log(continuous_data['Close'] / continuous_data['Close'].shift(1))
    
    return continuous_data

def get_front_month_series(futures_data):
    """
    Extract front month contract series from futures data
    
    Parameters:
    -----------
    futures_data : pandas.DataFrame
        DataFrame with futures data including a 'Contract' column
        
    Returns:
    --------
    pandas.DataFrame
        Front month series
    """
    if futures_data is None or futures_data.empty:
        return futures_data
    
    # Check if Contract column exists
    if 'Contract' not in futures_data.columns:
        print("Contract column not found, returning original data")
        return futures_data
    
    # Sort by date
    futures_data = futures_data.sort_index()
    
    # Extract contract expiration from contract code
    # This assumes standard format like 'AUZ1' for Dec 2021
    def extract_expiration(contract):
        if isinstance(contract, str) and len(contract) >= 4:
            # Extract month code and year
            month_code = contract[-2]
            year_code = contract[-1]
            
            # Map month codes to months
            month_map = {
                'F': 1,   # January
                'G': 2,   # February
                'H': 3,   # March
                'J': 4,   # April
                'K': 5,   # May
                'M': 6,   # June
                'N': 7,   # July
                'Q': 8,   # August
                'U': 9,   # September
                'V': 10,  # October
                'X': 11,  # November
                'Z': 12   # December
            }
            
            # Convert year code to year
            current_year = pd.Timestamp.now().year
            current_decade = current_year - (current_year % 10)
            year = current_decade + int(year_code)
            
            # If it seems in the future by more than 3 years, go back a decade
            if year > current_year + 3:
                year -= 10
            
            # Get month
            month = month_map.get(month_code, 1)
            
            # Return as timestamp for easy comparison
            return pd.Timestamp(year=year, month=month, day=1)
        else:
            return pd.Timestamp.now()
    
    # Add expiration to data
    futures_data = futures_data.copy()
    futures_data['Expiration'] = futures_data['Contract'].apply(extract_expiration)
    
    # For each date, select the nearest expiring contract (front month)
    grouped = futures_data.groupby(futures_data.index.date)
    front_month_rows = []
    
    for date, group in grouped:
        # Convert date to timestamp for comparison
        current_date = pd.Timestamp(date)
        
        # Filter contracts that haven't expired yet
        valid_contracts = group[group['Expiration'] >= current_date]
        
        if not valid_contracts.empty:
            # Get the contract closest to expiration
            front_month = valid_contracts.loc[valid_contracts['Expiration'].idxmin()]
            front_month_rows.append(front_month)
        else:
            # If all contracts are expired, use the most recently expired one
            front_month = group.loc[group['Expiration'].idxmax()]
            front_month_rows.append(front_month)
    
    front_month_data = pd.DataFrame(front_month_rows)
    
    # Clean up
    if 'Expiration' in front_month_data.columns:
        front_month_data.drop('Expiration', axis=1, inplace=True)
    
    return front_month_data

def create_spread_series(primary_data, secondary_data):
    """
    Create a spread series between two markets
    
    Parameters:
    -----------
    primary_data : pandas.DataFrame
        DataFrame with primary market data
    secondary_data : pandas.DataFrame
        DataFrame with secondary market data
        
    Returns:
    --------
    pandas.DataFrame
        Spread series between the two markets
    """
    if primary_data is None or primary_data.empty or secondary_data is None or secondary_data.empty:
        return None
    
    # Resample both series to common timeframe if needed
    if not primary_data.index.equals(secondary_data.index):
        # Find common frequency
        freq = pd.infer_freq(primary_data.index)
        if freq is None:
            freq = pd.infer_freq(secondary_data.index)
        if freq is None:
            # Default to daily if can't infer
            freq = 'D'
        
        # Resample to common frequency
        primary_resampled = primary_data.resample(freq).last().ffill()
        secondary_resampled = secondary_data.resample(freq).last().ffill()
        
        # Get common date range
        start_date = max(primary_resampled.index.min(), secondary_resampled.index.min())
        end_date = min(primary_resampled.index.max(), secondary_resampled.index.max())
        
        primary_aligned = primary_resampled.loc[start_date:end_date]
        secondary_aligned = secondary_resampled.loc[start_date:end_date]
    else:
        primary_aligned = primary_data
        secondary_aligned = secondary_data
    
    # Create spread series
    spread_data = pd.DataFrame(index=primary_aligned.index)
    spread_data['Primary'] = primary_aligned['Close']
    spread_data['Secondary'] = secondary_aligned['Close']
    spread_data['Spread'] = spread_data['Primary'] - spread_data['Secondary']
    spread_data['SpreadPct'] = (spread_data['Primary'] / spread_data['Secondary']) - 1.0
    
    # Calculate spread z-score (for mean reversion analysis)
    spread_data['SpreadMean'] = spread_data['Spread'].rolling(window=20).mean()
    spread_data['SpreadStd'] = spread_data['Spread'].rolling(window=20).std()
    spread_data['SpreadZScore'] = (spread_data['Spread'] - spread_data['SpreadMean']) / spread_data['SpreadStd']
    
    return spread_data
