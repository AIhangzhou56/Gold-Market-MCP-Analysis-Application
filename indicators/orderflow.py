import pandas as pd
import numpy as np
from scipy import stats

def calculate_order_flow(df):
    """
    Simulate order flow analysis using OHLCV data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with order flow metrics
    """
    # Since we don't have tick data with bid/ask information,
    # we'll simulate order flow based on price and volume patterns
    
    # Check if input dataframe is valid
    if df is None or df.empty:
        return None
    
    # Create a copy to avoid modifying the original
    oflow_df = df.copy()
    
    # Calculate price delta
    oflow_df['PriceDelta'] = oflow_df['Close'] - oflow_df['Open']
    
    # Identify buying and selling pressure
    oflow_df['BuyVolume'] = np.where(oflow_df['PriceDelta'] >= 0, 
                                   oflow_df['Volume'] * (oflow_df['Close'] - oflow_df['Low']) / 
                                   (oflow_df['High'] - oflow_df['Low'] + 1e-10), 
                                   oflow_df['Volume'] * (oflow_df['Close'] - oflow_df['Open']) / 
                                   (oflow_df['High'] - oflow_df['Low'] + 1e-10))
    
    oflow_df['SellVolume'] = np.where(oflow_df['PriceDelta'] < 0,
                                    oflow_df['Volume'] * (oflow_df['High'] - oflow_df['Close']) / 
                                    (oflow_df['High'] - oflow_df['Low'] + 1e-10),
                                    oflow_df['Volume'] * (oflow_df['High'] - oflow_df['Open']) / 
                                    (oflow_df['High'] - oflow_df['Low'] + 1e-10))
    
    # Handle cases where High equals Low (prevent division by zero)
    mask = oflow_df['High'] == oflow_df['Low']
    oflow_df.loc[mask, 'BuyVolume'] = oflow_df.loc[mask, 'Volume'] / 2
    oflow_df.loc[mask, 'SellVolume'] = oflow_df.loc[mask, 'Volume'] / 2
    
    # Calculate order flow indicators
    oflow_df['OrderFlowDelta'] = oflow_df['BuyVolume'] - oflow_df['SellVolume']
    oflow_df['OrderFlowRatio'] = oflow_df['BuyVolume'] / (oflow_df['SellVolume'] + 1e-10)
    
    # Calculate cumulative delta
    oflow_df['CumulativeDelta'] = oflow_df['OrderFlowDelta'].cumsum()
    
    # Calculate delta divergence (divergence between price and cumulative delta)
    oflow_df['DeltaDivergence'] = (oflow_df['Close'] / oflow_df['Close'].iloc[0]) - (oflow_df['CumulativeDelta'] / (oflow_df['CumulativeDelta'].iloc[0] + 1e-10))
    
    # Calculate volume weighted average price (intraday)
    oflow_df['IVWAP'] = (oflow_df['Close'] * oflow_df['Volume']).cumsum() / oflow_df['Volume'].cumsum()
    
    # Identify large orders (volume spikes)
    oflow_df['VolumeSMA'] = oflow_df['Volume'].rolling(window=10).mean()
    oflow_df['LargeOrderFlag'] = oflow_df['Volume'] > (2 * oflow_df['VolumeSMA'])
    
    # Calculate volume profile (simulated)
    num_buckets = 10
    for i in range(num_buckets):
        price_level = oflow_df['Low'] + i * (oflow_df['High'] - oflow_df['Low']) / num_buckets
        mask = (oflow_df['Low'] <= price_level) & (oflow_df['High'] >= price_level)
        oflow_df[f'VolumeAtPrice_{i}'] = np.where(mask, oflow_df['Volume'] / num_buckets, 0)
    
    # Calculate volume-weighted price levels
    oflow_df['VolumeWeightedPriceLevel'] = sum([oflow_df[f'VolumeAtPrice_{i}'] * i for i in range(num_buckets)]) / (oflow_df['Volume'] + 1e-10)
    
    # Calculate order flow momentum
    oflow_df['OrderFlowMomentum'] = oflow_df['OrderFlowDelta'].rolling(window=5).sum()
    
    # Calculate order flow acceleration
    oflow_df['OrderFlowAcceleration'] = oflow_df['OrderFlowMomentum'].diff()
    
    return oflow_df

def analyze_book_depth(df, levels=5):
    """
    Simulates market depth analysis based on OHLCV data
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    levels : int
        Number of price levels to simulate
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with simulated market depth metrics
    """
    # Since we don't have actual order book data,
    # we'll simulate market depth based on price action and volume
    
    # Check if input dataframe is valid
    if df is None or df.empty:
        return None
    
    # Create a copy to avoid modifying the original
    depth_df = df.copy()
    
    # Calculate price range for each period
    depth_df['PriceRange'] = depth_df['High'] - depth_df['Low']
    
    # Relative position of close within the range
    depth_df['RelativeClosePosition'] = (depth_df['Close'] - depth_df['Low']) / (depth_df['PriceRange'] + 1e-10)
    
    # Simulate market depth metrics
    # Higher volume suggests more liquidity
    depth_df['TotalLiquidity'] = depth_df['Volume']
    
    # Distribute liquidity across price levels
    for i in range(1, levels + 1):
        # Calculate bid side depth (below current price)
        bid_distance = i / (2 * levels)
        bid_price_level = depth_df['Close'] * (1 - bid_distance * 0.01)  # 0.01 = 1% range
        
        # Calculate ask side depth (above current price)
        ask_distance = i / (2 * levels)
        ask_price_level = depth_df['Close'] * (1 + ask_distance * 0.01)  # 0.01 = 1% range
        
        # Simulate liquidity at each level
        # Liquidity decreases as distance from current price increases
        liquidity_factor = 1 - (i / (levels + 1))
        
        # Bid side depth is higher when close is near the high (sellers in control)
        # Ask side depth is higher when close is near the low (buyers in control)
        bid_depth_factor = 1 - depth_df['RelativeClosePosition']
        ask_depth_factor = depth_df['RelativeClosePosition']
        
        depth_df[f'BidLevel_{i}_Price'] = bid_price_level
        depth_df[f'BidLevel_{i}_Volume'] = depth_df['TotalLiquidity'] * liquidity_factor * bid_depth_factor
        
        depth_df[f'AskLevel_{i}_Price'] = ask_price_level
        depth_df[f'AskLevel_{i}_Volume'] = depth_df['TotalLiquidity'] * liquidity_factor * ask_depth_factor
    
    # Calculate total book depth
    bid_columns = [f'BidLevel_{i}_Volume' for i in range(1, levels + 1)]
    ask_columns = [f'AskLevel_{i}_Volume' for i in range(1, levels + 1)]
    
    depth_df['TotalBidDepth'] = depth_df[bid_columns].sum(axis=1)
    depth_df['TotalAskDepth'] = depth_df[ask_columns].sum(axis=1)
    depth_df['BookImbalance'] = depth_df['TotalBidDepth'] - depth_df['TotalAskDepth']
    depth_df['BookImbalanceRatio'] = depth_df['TotalBidDepth'] / (depth_df['TotalAskDepth'] + 1e-10)
    
    # Calculate weighted average bid/ask prices
    depth_df['WeightedBidPrice'] = sum([depth_df[f'BidLevel_{i}_Price'] * depth_df[f'BidLevel_{i}_Volume'] 
                                     for i in range(1, levels + 1)]) / (depth_df['TotalBidDepth'] + 1e-10)
    
    depth_df['WeightedAskPrice'] = sum([depth_df[f'AskLevel_{i}_Price'] * depth_df[f'AskLevel_{i}_Volume'] 
                                     for i in range(1, levels + 1)]) / (depth_df['TotalAskDepth'] + 1e-10)
    
    # Calculate spread
    depth_df['SimulatedSpread'] = depth_df['WeightedAskPrice'] - depth_df['WeightedBidPrice']
    depth_df['SimulatedSpreadPct'] = depth_df['SimulatedSpread'] / depth_df['Close']
    
    # Market depth pressure indicator
    depth_df['MarketDepthPressure'] = np.log(depth_df['BookImbalanceRatio'])
    
    # Add depth volatility metrics
    depth_df['DepthVolatility'] = depth_df['BookImbalance'].rolling(window=10).std()
    
    return depth_df

def calculate_cumulative_volume_delta(df):
    """
    Calculate Cumulative Volume Delta (CVD)
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with CVD added
    """
    # Create a copy to avoid modifying the original
    cvd_df = df.copy()
    
    # Determine if volume is buying or selling
    cvd_df['TickDirection'] = np.where(cvd_df['Close'] > cvd_df['Close'].shift(1), 1,
                                  np.where(cvd_df['Close'] < cvd_df['Close'].shift(1), -1, 0))
    
    # Calculate volume delta
    cvd_df['VolumeDelta'] = cvd_df['Volume'] * cvd_df['TickDirection']
    
    # Calculate cumulative volume delta
    cvd_df['CVD'] = cvd_df['VolumeDelta'].cumsum()
    
    # Identify divergences between price and CVD
    cvd_df['PriceChange'] = cvd_df['Close'].pct_change()
    cvd_df['CVDChange'] = cvd_df['CVD'].diff() / abs(cvd_df['CVD'].shift(1) + 1e-10)
    
    # Flag divergences
    cvd_df['PriceCVDDivergence'] = (cvd_df['PriceChange'] * cvd_df['CVDChange'] < 0) & (abs(cvd_df['PriceChange']) > 0.001)
    
    return cvd_df
