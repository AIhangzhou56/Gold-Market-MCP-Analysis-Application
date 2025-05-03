import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union

def create_strategy(data: pd.DataFrame, strategy_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a strategy based on the given parameters
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with OHLCV and indicator data
    strategy_params : dict
        Dictionary with strategy parameters
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with strategy signals
    """
    strategy_type = strategy_params.get('type', '')
    
    if strategy_type == 'Mean Reversion':
        return create_mean_reversion_strategy(data, strategy_params)
    elif strategy_type == 'Trend Following':
        return create_trend_following_strategy(data, strategy_params)
    elif strategy_type == 'Breakout':
        return create_breakout_strategy(data, strategy_params)
    elif strategy_type == 'Custom':
        return create_custom_strategy(data, strategy_params)
    else:
        raise ValueError(f"Unsupported strategy type: {strategy_type}")

def create_mean_reversion_strategy(data: pd.DataFrame, strategy_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a mean reversion strategy
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with OHLCV and indicator data
    strategy_params : dict
        Dictionary with strategy parameters
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with strategy signals
    """
    # Copy data to avoid modifying the original
    df = data.copy()
    
    # Extract parameters
    lookback = strategy_params.get('lookback', 20)
    std_dev = strategy_params.get('std_dev', 2.0)
    exit_threshold = strategy_params.get('exit_threshold', 0.5)
    
    # Calculate mean and standard deviation
    df['Mean'] = df['Close'].rolling(window=lookback).mean()
    df['StdDev'] = df['Close'].rolling(window=lookback).std()
    
    # Calculate upper and lower bands
    df['Upper'] = df['Mean'] + (df['StdDev'] * std_dev)
    df['Lower'] = df['Mean'] - (df['StdDev'] * std_dev)
    
    # Generate signals
    df['Signal'] = 0.0  # 0: no position, 1: long, -1: short
    
    # Entry signals
    df.loc[df['Close'] < df['Lower'], 'Signal'] = 1.0  # Buy signal (oversold)
    df.loc[df['Close'] > df['Upper'], 'Signal'] = -1.0  # Sell signal (overbought)
    
    # Exit signals
    df['PriceToMean'] = (df['Close'] - df['Mean']) / df['StdDev']
    df.loc[(df['Signal'].shift(1) == 1.0) & (df['PriceToMean'] >= -exit_threshold), 'Signal'] = 0.0  # Exit long
    df.loc[(df['Signal'].shift(1) == -1.0) & (df['PriceToMean'] <= exit_threshold), 'Signal'] = 0.0  # Exit short
    
    # Clean up signals (avoid multiple entries/exits)
    df['Position'] = df['Signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    # Generate strategy code as pseudocode
    strategy_code = f"""
# Mean Reversion Strategy
# Parameters:
lookback = {lookback}        # Lookback period for mean calculation
std_dev = {std_dev}          # Standard deviation multiplier for bands
exit_threshold = {exit_threshold}  # Exit when price is within this many StdDevs of the mean

# Calculate indicators
mean = Close.rolling(window=lookback).mean()
std_dev = Close.rolling(window=lookback).std()
upper_band = mean + (std_dev * std_dev_multiplier)
lower_band = mean - (std_dev * std_dev_multiplier)

# Entry rules
if Close < lower_band:
    # Buy signal (oversold)
    enter_long()
elif Close > upper_band:
    # Sell signal (overbought)
    enter_short()

# Exit rules
price_to_mean = (Close - mean) / std_dev
if in_long_position and price_to_mean >= -exit_threshold:
    # Exit long when price returns toward mean
    exit_long()
elif in_short_position and price_to_mean <= exit_threshold:
    # Exit short when price returns toward mean
    exit_short()
"""
    
    # Store strategy code in DataFrame
    df.attrs['strategy_code'] = strategy_code
    
    return df

def create_trend_following_strategy(data: pd.DataFrame, strategy_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a trend following strategy
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with OHLCV and indicator data
    strategy_params : dict
        Dictionary with strategy parameters
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with strategy signals
    """
    # Copy data to avoid modifying the original
    df = data.copy()
    
    # Extract parameters
    fast_period = strategy_params.get('fast_period', 10)
    slow_period = strategy_params.get('slow_period', 50)
    
    # Calculate moving averages
    df['MA_Fast'] = df['Close'].rolling(window=fast_period).mean()
    df['MA_Slow'] = df['Close'].rolling(window=slow_period).mean()
    
    # Generate signals
    df['Signal'] = 0.0  # 0: no position, 1: long, -1: short
    
    # Entry signals
    df.loc[df['MA_Fast'] > df['MA_Slow'], 'Signal'] = 1.0  # Buy signal (fast above slow)
    df.loc[df['MA_Fast'] < df['MA_Slow'], 'Signal'] = -1.0  # Sell signal (fast below slow)
    
    # Clean up signals (only take the first entry in a sequence)
    df['SignalDiff'] = df['Signal'].diff()
    df.loc[df['SignalDiff'] == 0, 'Signal'] = 0.0
    
    # Generate position column (1: long, -1: short, 0: no position)
    df['Position'] = df['Signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    # Generate strategy code as pseudocode
    strategy_code = f"""
# Trend Following Strategy
# Parameters:
fast_period = {fast_period}   # Fast moving average period
slow_period = {slow_period}   # Slow moving average period

# Calculate indicators
ma_fast = Close.rolling(window=fast_period).mean()
ma_slow = Close.rolling(window=slow_period).mean()

# Entry rules
if ma_fast > ma_slow and not in_long_position:
    # Buy signal (fast MA crosses above slow MA)
    enter_long()
elif ma_fast < ma_slow and not in_short_position:
    # Sell signal (fast MA crosses below slow MA)
    enter_short()

# Exit rules
if in_long_position and ma_fast < ma_slow:
    # Exit long when fast crosses below slow
    exit_long()
elif in_short_position and ma_fast > ma_slow:
    # Exit short when fast crosses above slow
    exit_short()
"""
    
    # Store strategy code in DataFrame
    df.attrs['strategy_code'] = strategy_code
    
    return df

def create_breakout_strategy(data: pd.DataFrame, strategy_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a breakout strategy
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with OHLCV and indicator data
    strategy_params : dict
        Dictionary with strategy parameters
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with strategy signals
    """
    # Copy data to avoid modifying the original
    df = data.copy()
    
    # Extract parameters
    channel_period = strategy_params.get('channel_period', 20)
    atr_multiplier = strategy_params.get('atr_multiplier', 2.0)
    
    # Calculate indicators
    df['High_Channel'] = df['High'].rolling(window=channel_period).max()
    df['Low_Channel'] = df['Low'].rolling(window=channel_period).min()
    
    # Calculate ATR if not already present
    if 'ATR' not in df.columns:
        df['TR'] = np.maximum(
            df['High'] - df['Low'],
            np.maximum(
                abs(df['High'] - df['Close'].shift(1)),
                abs(df['Low'] - df['Close'].shift(1))
            )
        )
        df['ATR'] = df['TR'].rolling(window=14).mean()
    
    # Calculate breakout levels
    df['Breakout_Up'] = df['High_Channel'] + (df['ATR'] * atr_multiplier)
    df['Breakout_Down'] = df['Low_Channel'] - (df['ATR'] * atr_multiplier)
    
    # Generate signals
    df['Signal'] = 0.0  # 0: no position, 1: long, -1: short
    
    # Entry signals
    df.loc[df['Close'] > df['Breakout_Up'].shift(1), 'Signal'] = 1.0  # Buy signal (breakout up)
    df.loc[df['Close'] < df['Breakout_Down'].shift(1), 'Signal'] = -1.0  # Sell signal (breakout down)
    
    # Exit signals - opposite breakout or channel boundary touch
    df.loc[(df['Signal'].shift(1) == 1.0) & (df['Close'] < df['Low_Channel']), 'Signal'] = 0.0  # Exit long
    df.loc[(df['Signal'].shift(1) == -1.0) & (df['Close'] > df['High_Channel']), 'Signal'] = 0.0  # Exit short
    
    # Clean up signals
    df['Position'] = df['Signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    # Generate strategy code as pseudocode
    strategy_code = f"""
# Breakout Strategy
# Parameters:
channel_period = {channel_period}  # Period for calculating price channel
atr_multiplier = {atr_multiplier}  # Multiplier for ATR to determine breakout level

# Calculate indicators
high_channel = High.rolling(window=channel_period).max()
low_channel = Low.rolling(window=channel_period).min()
atr = calculate_atr(period=14)

# Calculate breakout levels
breakout_up = high_channel + (atr * atr_multiplier)
breakout_down = low_channel - (atr * atr_multiplier)

# Entry rules
if Close > breakout_up.shift(1):
    # Buy signal (breakout above upper level)
    enter_long()
elif Close < breakout_down.shift(1):
    # Sell signal (breakout below lower level)
    enter_short()

# Exit rules
if in_long_position and Close < low_channel:
    # Exit long when price falls below the channel
    exit_long()
elif in_short_position and Close > high_channel:
    # Exit short when price rises above the channel
    exit_short()
"""
    
    # Store strategy code in DataFrame
    df.attrs['strategy_code'] = strategy_code
    
    return df

def create_arbitrage_strategy(primary_data: pd.DataFrame, secondary_data: pd.DataFrame, 
                             strategy_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Create an arbitrage strategy between two assets
    
    Parameters:
    -----------
    primary_data : pandas.DataFrame
        DataFrame with OHLCV data for primary asset
    secondary_data : pandas.DataFrame
        DataFrame with OHLCV data for secondary asset
    strategy_params : dict
        Dictionary with strategy parameters
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with strategy signals
    """
    # Create a common index for both datasets
    common_idx = primary_data.index.intersection(secondary_data.index)
    primary = primary_data.loc[common_idx].copy()
    secondary = secondary_data.loc[common_idx].copy()
    
    # Extract parameters
    z_score_threshold = strategy_params.get('z_score_threshold', 2.0)
    
    # Calculate the spread
    primary['Spread'] = primary['Close'] - secondary['Close']
    
    # Calculate z-score of the spread
    lookback = 20  # Default lookback period
    primary['SpreadMean'] = primary['Spread'].rolling(window=lookback).mean()
    primary['SpreadStd'] = primary['Spread'].rolling(window=lookback).std()
    primary['ZScore'] = (primary['Spread'] - primary['SpreadMean']) / primary['SpreadStd']
    
    # Generate signals
    primary['Signal'] = 0.0  # 0: no position, 1: long, -1: short
    
    # Entry signals
    # Long spread (long primary, short secondary) when z-score is low
    primary.loc[primary['ZScore'] < -z_score_threshold, 'Signal'] = 1.0
    
    # Short spread (short primary, long secondary) when z-score is high
    primary.loc[primary['ZScore'] > z_score_threshold, 'Signal'] = -1.0
    
    # Exit signals
    # Exit when spread returns to mean
    primary.loc[(primary['Signal'].shift(1) == 1.0) & (primary['ZScore'] >= 0), 'Signal'] = 0.0  # Exit long spread
    primary.loc[(primary['Signal'].shift(1) == -1.0) & (primary['ZScore'] <= 0), 'Signal'] = 0.0  # Exit short spread
    
    # Clean up signals
    primary['Position'] = primary['Signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    # Add secondary asset close price for reference
    primary['SecondaryClose'] = secondary['Close']
    
    # Generate strategy code as pseudocode
    strategy_code = f"""
# Pair Trading / Arbitrage Strategy
# Parameters:
z_score_threshold = {z_score_threshold}  # Z-score threshold for entry
lookback = {lookback}                    # Lookback period for z-score calculation

# Calculate spread between primary and secondary assets
spread = primary_close - secondary_close

# Calculate z-score
spread_mean = spread.rolling(window=lookback).mean()
spread_std = spread.rolling(window=lookback).std()
z_score = (spread - spread_mean) / spread_std

# Entry rules
if z_score < -z_score_threshold:
    # Long spread (long primary, short secondary) when spread is too low
    enter_long_primary()
    enter_short_secondary()
elif z_score > z_score_threshold:
    # Short spread (short primary, long secondary) when spread is too high
    enter_short_primary()
    enter_long_secondary()

# Exit rules
if in_long_spread and z_score >= 0:
    # Exit long spread when spread returns to mean
    exit_long_primary()
    exit_short_secondary()
elif in_short_spread and z_score <= 0:
    # Exit short spread when spread returns to mean
    exit_short_primary()
    exit_long_secondary()
"""
    
    # Store strategy code in DataFrame
    primary.attrs['strategy_code'] = strategy_code
    
    return primary

def create_custom_strategy(data: pd.DataFrame, strategy_params: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a custom strategy based on selected indicators
    
    Parameters:
    -----------
    data : pandas.DataFrame
        DataFrame with OHLCV and indicator data
    strategy_params : dict
        Dictionary with strategy parameters
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with strategy signals
    """
    # Copy data to avoid modifying the original
    df = data.copy()
    
    # Extract parameters
    indicators = strategy_params.get('indicators', [])
    params = strategy_params.get('params', {})
    
    # Initialize signals
    df['Signal'] = 0.0  # 0: no position, 1: long, -1: short
    
    # Generate signals based on selected indicators
    signal_conditions = []
    exit_conditions = []
    indicator_calcs = []
    
    # Add selected indicators
    if 'MACD' in indicators:
        # Get MACD parameters
        macd_fast = params.get('macd_fast', 12)
        macd_slow = params.get('macd_slow', 26)
        macd_signal = params.get('macd_signal', 9)
        
        # Calculate MACD if not already present
        if not all(col in df.columns for col in ['MACD', 'MACD_Signal']):
            df['EMA_Fast'] = df['Close'].ewm(span=macd_fast, adjust=False).mean()
            df['EMA_Slow'] = df['Close'].ewm(span=macd_slow, adjust=False).mean()
            df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
            df['MACD_Signal'] = df['MACD'].ewm(span=macd_signal, adjust=False).mean()
            df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
            
            indicator_calcs.append(f"""
# Calculate MACD
ema_fast = Close.ewm(span={macd_fast}, adjust=False).mean()
ema_slow = Close.ewm(span={macd_slow}, adjust=False).mean()
macd = ema_fast - ema_slow
macd_signal = macd.ewm(span={macd_signal}, adjust=False).mean()
macd_histogram = macd - macd_signal
""")
        
        # MACD signal conditions
        # Buy when MACD crosses above signal line
        signal_conditions.append("(df['MACD'] > df['MACD_Signal']) & (df['MACD'].shift(1) <= df['MACD_Signal'].shift(1))")
        # Exit when MACD crosses below signal line
        exit_conditions.append("(df['MACD'] < df['MACD_Signal']) & (df['MACD'].shift(1) >= df['MACD_Signal'].shift(1))")
        
    if 'RSI' in indicators:
        # Get RSI parameters
        rsi_period = params.get('rsi_period', 14)
        rsi_overbought = params.get('rsi_overbought', 70)
        rsi_oversold = params.get('rsi_oversold', 30)
        
        # Calculate RSI if not already present
        if 'RSI' not in df.columns:
            delta = df['Close'].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=rsi_period).mean()
            avg_loss = loss.rolling(window=rsi_period).mean()
            rs = avg_gain / avg_loss.replace(0, 1e-10)  # Avoid division by zero
            df['RSI'] = 100 - (100 / (1 + rs))
            
            indicator_calcs.append(f"""
# Calculate RSI
delta = Close.diff()
gain = delta.clip(lower=0)
loss = -delta.clip(upper=0)
avg_gain = gain.rolling(window={rsi_period}).mean()
avg_loss = loss.rolling(window={rsi_period}).mean()
rs = avg_gain / avg_loss.replace(0, 1e-10)  # Avoid division by zero
rsi = 100 - (100 / (1 + rs))
""")
        
        # RSI signal conditions
        # Buy when RSI crosses above oversold level
        signal_conditions.append(f"(df['RSI'] > {rsi_oversold}) & (df['RSI'].shift(1) <= {rsi_oversold})")
        # Exit when RSI crosses above overbought level
        exit_conditions.append(f"(df['RSI'] > {rsi_overbought})")
        
    if 'Bollinger Bands' in indicators:
        # Calculate Bollinger Bands if not already present
        if not all(col in df.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
            period = 20  # Default period
            std_dev = 2.0  # Default std dev multiplier
            
            df['BB_Middle'] = df['Close'].rolling(window=period).mean()
            df['BB_Std'] = df['Close'].rolling(window=period).std()
            df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * std_dev)
            df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * std_dev)
            
            indicator_calcs.append(f"""
# Calculate Bollinger Bands
bb_middle = Close.rolling(window={period}).mean()
bb_std = Close.rolling(window={period}).std()
bb_upper = bb_middle + (bb_std * {std_dev})
bb_lower = bb_middle - (bb_std * {std_dev})
""")
        
        # Bollinger Bands signal conditions
        # Buy when price crosses below lower band
        signal_conditions.append("(df['Close'] < df['BB_Lower'])")
        # Exit when price crosses above middle band
        exit_conditions.append("(df['Close'] > df['BB_Middle']) & (df['Close'].shift(1) <= df['BB_Middle'].shift(1))")
        
    if 'VWAP' in indicators:
        # Calculate VWAP if not already present
        if 'VWAP' not in df.columns:
            df['TypicalPrice'] = (df['High'] + df['Low'] + df['Close']) / 3
            df['VWAP'] = (df['TypicalPrice'] * df['Volume']).cumsum() / df['Volume'].cumsum()
            df.drop('TypicalPrice', axis=1, inplace=True)
            
            indicator_calcs.append("""
# Calculate VWAP
typical_price = (High + Low + Close) / 3
vwap = (typical_price * Volume).cumsum() / Volume.cumsum()
""")
        
        # VWAP signal conditions
        # Buy when price crosses above VWAP
        signal_conditions.append("(df['Close'] > df['VWAP']) & (df['Close'].shift(1) <= df['VWAP'].shift(1))")
        # Exit when price crosses below VWAP
        exit_conditions.append("(df['Close'] < df['VWAP']) & (df['Close'].shift(1) >= df['VWAP'].shift(1))")
        
    if 'OI Delta' in indicators and 'OI_Delta' in df.columns:
        # OI Delta signal conditions
        # Buy when OI delta turns positive
        signal_conditions.append("(df['OI_Delta'] > 0) & (df['OI_Delta'].shift(1) <= 0)")
        # Exit when OI delta turns negative
        exit_conditions.append("(df['OI_Delta'] < 0) & (df['OI_Delta'].shift(1) >= 0)")
        
    # Generate combined signal conditions
    if signal_conditions:
        # Generate buy signals
        buy_condition = " | ".join(signal_conditions)
        df.loc[eval(buy_condition), 'Signal'] = 1.0
        
        # Generate exit signals
        if exit_conditions:
            exit_condition = " | ".join(exit_conditions)
            df.loc[(df['Signal'].shift(1) == 1.0) & eval(exit_condition), 'Signal'] = 0.0
    
    # Clean up signals
    df['Position'] = df['Signal'].replace(0, np.nan).fillna(method='ffill').fillna(0)
    
    # Generate strategy code as pseudocode
    strategy_code = "# Custom Strategy\n"
    strategy_code += "# Indicators: " + ", ".join(indicators) + "\n\n"
    
    # Add indicator calculations
    for calc in indicator_calcs:
        strategy_code += calc + "\n"
    
    # Add entry and exit rules
    strategy_code += "# Entry rules\n"
    for i, condition in enumerate(signal_conditions):
        strategy_code += f"if {condition.replace('df[', '').replace(']', '').replace('&', 'and').replace('|', 'or')}:\n"
        strategy_code += "    # Buy signal based on selected indicators\n"
        strategy_code += "    enter_long()\n\n"
    
    strategy_code += "# Exit rules\n"
    for i, condition in enumerate(exit_conditions):
        strategy_code += f"if in_long_position and {condition.replace('df[', '').replace(']', '').replace('&', 'and').replace('|', 'or')}:\n"
        strategy_code += "    # Exit long based on selected indicators\n"
        strategy_code += "    exit_long()\n\n"
    
    # Store strategy code in DataFrame
    df.attrs['strategy_code'] = strategy_code
    
    return df

def get_strategy_pseudocode(df: pd.DataFrame) -> str:
    """
    Get the strategy pseudocode stored in DataFrame attributes
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with strategy data
        
    Returns:
    --------
    str
        Strategy pseudocode
    """
    return df.attrs.get('strategy_code', "No strategy code available")
