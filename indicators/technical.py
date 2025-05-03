import pandas as pd
import numpy as np

def add_vwap(df, period=None):
    """
    Calculate Volume Weighted Average Price (VWAP)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    period : int or None
        Period for VWAP calculation, None means use all available data
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with VWAP column added
    """
    df = df.copy()
    
    # Calculate typical price
    df['TypicalPrice'] = (df['High'] + df['Low'] + df['Close']) / 3
    
    # Calculate VWAP
    if period is None:
        # Use all data
        df['VWAP'] = (df['TypicalPrice'] * df['Volume']).cumsum() / df['Volume'].cumsum()
    else:
        # Use rolling window
        df['VWAP'] = (df['TypicalPrice'] * df['Volume']).rolling(window=period).sum() / df['Volume'].rolling(window=period).sum()
    
    # Remove temporary column
    df.drop('TypicalPrice', axis=1, inplace=True)
    
    return df

def add_macd(df, fast_period=12, slow_period=26, signal_period=9):
    """
    Calculate Moving Average Convergence Divergence (MACD)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    fast_period : int
        Fast EMA period
    slow_period : int
        Slow EMA period
    signal_period : int
        Signal EMA period
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with MACD columns added
    """
    df = df.copy()
    
    # Calculate EMAs
    df['EMA_Fast'] = df['Close'].ewm(span=fast_period, adjust=False).mean()
    df['EMA_Slow'] = df['Close'].ewm(span=slow_period, adjust=False).mean()
    
    # Calculate MACD and Signal
    df['MACD'] = df['EMA_Fast'] - df['EMA_Slow']
    df['MACD_Signal'] = df['MACD'].ewm(span=signal_period, adjust=False).mean()
    df['MACD_Histogram'] = df['MACD'] - df['MACD_Signal']
    
    # Remove temporary columns
    df.drop(['EMA_Fast', 'EMA_Slow'], axis=1, inplace=True)
    
    return df

def add_rsi(df, period=14):
    """
    Calculate Relative Strength Index (RSI)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    period : int
        RSI calculation period
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with RSI column added
    """
    df = df.copy()
    
    # Calculate price changes
    delta = df['Close'].diff()
    
    # Separate gains and losses
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    
    # Calculate average gain and loss
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # Calculate RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # Calculate RSI
    df['RSI'] = 100 - (100 / (1 + rs))
    
    return df

def add_bollinger_bands(df, period=20, std_dev=2):
    """
    Calculate Bollinger Bands
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    period : int
        Moving average period
    std_dev : float
        Number of standard deviations
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with Bollinger Bands columns added
    """
    df = df.copy()
    
    # Calculate middle band (SMA)
    df['BB_Middle'] = df['Close'].rolling(window=period).mean()
    
    # Calculate standard deviation
    df['BB_Std'] = df['Close'].rolling(window=period).std()
    
    # Calculate upper and lower bands
    df['BB_Upper'] = df['BB_Middle'] + (df['BB_Std'] * std_dev)
    df['BB_Lower'] = df['BB_Middle'] - (df['BB_Std'] * std_dev)
    
    # Calculate bandwidth and %B
    df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Middle']
    df['BB_PercentB'] = (df['Close'] - df['BB_Lower']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # Remove temporary column
    df.drop('BB_Std', axis=1, inplace=True)
    
    return df

def add_oi_delta(df, period=1):
    """
    Calculate Open Interest Delta (change in open interest)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data including OpenInterest column
    period : int
        Period for OI change calculation
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with OI_Delta column added
    """
    df = df.copy()
    
    # Check if OpenInterest column exists
    if 'OpenInterest' not in df.columns:
        print("OpenInterest column not found, returning original data")
        return df
    
    # Calculate absolute change in open interest
    df['OI_Delta'] = df['OpenInterest'].diff(period)
    
    # Calculate percentage change in open interest
    df['OI_Delta_Pct'] = df['OpenInterest'].pct_change(period)
    
    return df

def add_atr(df, period=14):
    """
    Calculate Average True Range (ATR)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    period : int
        ATR calculation period
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with ATR column added
    """
    df = df.copy()
    
    # Calculate true range
    df['H-L'] = df['High'] - df['Low']
    df['H-PC'] = abs(df['High'] - df['Close'].shift(1))
    df['L-PC'] = abs(df['Low'] - df['Close'].shift(1))
    
    df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
    
    # Calculate ATR
    df['ATR'] = df['TR'].rolling(window=period).mean()
    
    # Remove temporary columns
    df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
    
    return df

def add_stochastic(df, k_period=14, d_period=3, slowing=3):
    """
    Calculate Stochastic Oscillator
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    k_period : int
        K period
    d_period : int
        D period
    slowing : int
        Slowing period
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with Stochastic columns added
    """
    df = df.copy()
    
    # Calculate %K
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    
    df['Stoch_K_Raw'] = 100 * (df['Close'] - low_min) / (high_max - low_min)
    
    # Apply slowing to %K
    df['Stoch_K'] = df['Stoch_K_Raw'].rolling(window=slowing).mean()
    
    # Calculate %D
    df['Stoch_D'] = df['Stoch_K'].rolling(window=d_period).mean()
    
    # Remove temporary column
    df.drop('Stoch_K_Raw', axis=1, inplace=True)
    
    return df

def add_adx(df, period=14):
    """
    Calculate Average Directional Index (ADX)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    period : int
        ADX calculation period
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with ADX columns added
    """
    df = df.copy()
    
    # Calculate directional movement
    df['H-pH'] = df['High'] - df['High'].shift(1)
    df['pL-L'] = df['Low'].shift(1) - df['Low']
    
    df['DM+'] = np.where((df['H-pH'] > df['pL-L']) & (df['H-pH'] > 0), df['H-pH'], 0)
    df['DM-'] = np.where((df['pL-L'] > df['H-pH']) & (df['pL-L'] > 0), df['pL-L'], 0)
    
    # Add ATR
    df = add_atr(df, period)
    
    # Calculate directional indicators
    df['DI+'] = 100 * (df['DM+'].rolling(window=period).mean() / df['ATR'])
    df['DI-'] = 100 * (df['DM-'].rolling(window=period).mean() / df['ATR'])
    
    # Calculate directional index
    df['DX'] = 100 * abs(df['DI+'] - df['DI-']) / (df['DI+'] + df['DI-'])
    
    # Calculate ADX
    df['ADX'] = df['DX'].rolling(window=period).mean()
    
    # Remove temporary columns
    df.drop(['H-pH', 'pL-L', 'DM+', 'DM-', 'DX'], axis=1, inplace=True)
    
    return df

def add_ichimoku(df, tenkan_period=9, kijun_period=26, senkou_span_b_period=52, displacement=26):
    """
    Calculate Ichimoku Cloud
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    tenkan_period : int
        Tenkan-sen (Conversion Line) period
    kijun_period : int
        Kijun-sen (Base Line) period
    senkou_span_b_period : int
        Senkou Span B (Leading Span B) period
    displacement : int
        Displacement period for Senkou Span
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with Ichimoku columns added
    """
    df = df.copy()
    
    # Calculate Tenkan-sen (Conversion Line)
    tenkan_high = df['High'].rolling(window=tenkan_period).max()
    tenkan_low = df['Low'].rolling(window=tenkan_period).min()
    df['Ichimoku_Tenkan'] = (tenkan_high + tenkan_low) / 2
    
    # Calculate Kijun-sen (Base Line)
    kijun_high = df['High'].rolling(window=kijun_period).max()
    kijun_low = df['Low'].rolling(window=kijun_period).min()
    df['Ichimoku_Kijun'] = (kijun_high + kijun_low) / 2
    
    # Calculate Senkou Span A (Leading Span A)
    df['Ichimoku_SenkouA'] = ((df['Ichimoku_Tenkan'] + df['Ichimoku_Kijun']) / 2).shift(displacement)
    
    # Calculate Senkou Span B (Leading Span B)
    senkou_b_high = df['High'].rolling(window=senkou_span_b_period).max()
    senkou_b_low = df['Low'].rolling(window=senkou_span_b_period).min()
    df['Ichimoku_SenkouB'] = ((senkou_b_high + senkou_b_low) / 2).shift(displacement)
    
    # Calculate Chikou Span (Lagging Span)
    df['Ichimoku_Chikou'] = df['Close'].shift(-displacement)
    
    return df

def add_mcp_factors(df):
    """
    Add Market Class Probability (MCP) factors
    Combines multiple indicators into a comprehensive set of factors
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with MCP factors added
    """
    # Add basic indicators
    df = add_vwap(df)
    df = add_macd(df)
    df = add_rsi(df)
    df = add_bollinger_bands(df)
    df = add_atr(df, period=14)
    df = add_stochastic(df)
    
    # Add market regime factors
    
    # Trend strength indicators
    df['Trend_Strength'] = abs(df['RSI'] - 50)
    
    # Volatility indicators
    df['Volatility'] = df['ATR'] / df['Close']
    
    # Momentum indicators
    df['Momentum_Fast'] = df['Close'].pct_change(5)
    df['Momentum_Slow'] = df['Close'].pct_change(20)
    
    # Mean reversion factor
    df['Mean_Reversion'] = (df['Close'] - df['BB_Middle']) / (df['BB_Upper'] - df['BB_Lower'])
    
    # Volume factors
    df['Volume_Trend'] = df['Volume'].pct_change(5)
    df['Volume_Ratio'] = df['Volume'] / df['Volume'].rolling(window=20).mean()
    
    # VWAP distance
    df['VWAP_Distance'] = (df['Close'] - df['VWAP']) / df['VWAP']
    
    # Combine indicators into MCP factors
    
    # Trend regime factor
    df['MCP_Trend'] = (
        (df['Close'] > df['BB_Middle']).astype(int) * 0.4 +
        (df['RSI'] > 50).astype(int) * 0.3 +
        (df['MACD'] > df['MACD_Signal']).astype(int) * 0.3
    )
    
    # Mean reversion regime factor
    df['MCP_MeanReversion'] = (
        (abs(df['BB_PercentB'] - 0.5) > 0.4).astype(int) * 0.4 +
        ((df['RSI'] < 30) | (df['RSI'] > 70)).astype(int) * 0.3 +
        (df['Mean_Reversion'].abs() > 0.8).astype(int) * 0.3
    )
    
    # Volatility regime factor
    df['MCP_Volatility'] = (
        (df['Volatility'] > df['Volatility'].rolling(window=20).mean()).astype(int) * 0.4 +
        (df['BB_Width'] > df['BB_Width'].rolling(window=20).mean()).astype(int) * 0.3 +
        (df['ATR'] > df['ATR'].rolling(window=20).mean()).astype(int) * 0.3
    )
    
    # Momentum regime factor
    df['MCP_Momentum'] = (
        (df['Momentum_Fast'] > 0).astype(int) * 0.4 +
        (df['Momentum_Slow'] > 0).astype(int) * 0.3 +
        (df['Stoch_K'] > df['Stoch_D']).astype(int) * 0.3
    )
    
    return df
