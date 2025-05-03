import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from scipy.stats import pearsonr

def create_correlation_map(dataframes, labels):
    """
    Create a correlation heatmap between multiple assets
    
    Parameters:
    -----------
    dataframes : list of pandas.DataFrame
        List of DataFrames with price data
    labels : list of str
        Labels for each DataFrame
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive correlation heatmap
    """
    # Check input
    if not dataframes or len(dataframes) < 2:
        raise ValueError("At least two dataframes are required for correlation analysis")
    
    if len(dataframes) != len(labels):
        raise ValueError("Number of dataframes must match number of labels")
    
    # Extract closing prices
    close_prices = pd.DataFrame()
    
    for i, df in enumerate(dataframes):
        if df is not None and not df.empty and 'Close' in df.columns:
            # Resample to daily if necessary to align dates
            daily_data = df['Close']
            close_prices[labels[i]] = daily_data
    
    # Calculate returns
    returns = close_prices.pct_change().dropna()
    
    # Calculate correlation matrix
    corr_matrix = returns.corr()
    
    # Create heatmap
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        color_continuous_scale='RdBu_r',
        zmin=-1,
        zmax=1,
        labels=dict(color="Correlation")
    )
    
    # Update layout
    fig.update_layout(
        title="Price Correlation Between Assets",
        height=600,
        width=800,
        margin=dict(l=65, r=50, b=65, t=90)
    )
    
    # Adjust text size
    fig.update_traces(text=corr_matrix.round(2), texttemplate="%{text}")
    
    return fig

def create_technical_signal_map(data_dict, lookback_period=14):
    """
    Create a technical indicator signal map for multiple assets
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with asset names as keys and DataFrames as values
    lookback_period : int
        Lookback period for technical signals
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive technical signal map
    """
    # Prepare signal data
    signal_data = pd.DataFrame()
    
    for asset_name, df in data_dict.items():
        if df is None or df.empty:
            continue
        
        # Calculate various technical signals
        
        # Trend signals
        sma_fast = df['Close'].rolling(window=lookback_period).mean()
        sma_slow = df['Close'].rolling(window=lookback_period * 2).mean()
        trend_signal = np.where(sma_fast > sma_slow, 1, -1)
        
        # Momentum signals
        momentum = df['Close'].pct_change(lookback_period)
        momentum_signal = np.where(momentum > 0, 1, -1)
        
        # Volatility signals
        returns = df['Close'].pct_change()
        volatility = returns.rolling(window=lookback_period).std()
        volatility_signal = np.where(volatility > volatility.rolling(window=lookback_period).mean(), 1, 0)
        
        # RSI signals
        if 'RSI' in df.columns:
            rsi = df['RSI']
            rsi_signal = np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0))
        else:
            # Calculate RSI if not available
            delta = df['Close'].diff()
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=lookback_period).mean()
            avg_loss = loss.rolling(window=lookback_period).mean()
            rs = avg_gain / avg_loss.replace(0, 1e-10)  # Avoid division by zero
            rsi = 100 - (100 / (1 + rs))
            rsi_signal = np.where(rsi < 30, 1, np.where(rsi > 70, -1, 0))
        
        # MACD signals
        if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
            macd = df['MACD']
            macd_signal = df['MACD_Signal']
            macd_hist = macd - macd_signal
            macd_signal_value = np.where(macd_hist > 0, 1, -1)
        else:
            # Calculate MACD if not available
            ema_fast = df['Close'].ewm(span=12, adjust=False).mean()
            ema_slow = df['Close'].ewm(span=26, adjust=False).mean()
            macd = ema_fast - ema_slow
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - macd_signal
            macd_signal_value = np.where(macd_hist > 0, 1, -1)
        
        # Combine signals into a DataFrame
        df_signals = pd.DataFrame({
            'Date': df.index,
            'Asset': asset_name,
            'Trend': trend_signal,
            'Momentum': momentum_signal,
            'RSI': rsi_signal,
            'MACD': macd_signal_value,
            'Volatility': volatility_signal
        })
        
        # Append to main signal data
        signal_data = pd.concat([signal_data, df_signals])
    
    # Create a pivot table for the heatmap
    signal_pivot = pd.DataFrame()
    
    # Process each signal type
    for signal_type in ['Trend', 'Momentum', 'RSI', 'MACD', 'Volatility']:
        temp_pivot = pd.pivot_table(
            signal_data, 
            values=signal_type, 
            index=['Date'], 
            columns=['Asset']
        )
        
        # Get the latest available data point
        latest_date = temp_pivot.index.max()
        latest_signals = temp_pivot.loc[latest_date]
        
        # Add to signal pivot
        signal_pivot = pd.concat([signal_pivot, pd.DataFrame(latest_signals).T], keys=[signal_type])
    
    # Reset index to get signal types as a column
    signal_pivot = signal_pivot.reset_index(level=0)
    
    # Map signal values to colors
    signal_colors = {
        1: '#26a69a',    # Strong buy / positive - green
        0.5: '#81c784',  # Weak buy - light green
        0: '#e0e0e0',    # Neutral - gray
        -0.5: '#ef9a9a', # Weak sell - light red
        -1: '#ef5350'    # Strong sell / negative - red
    }
    
    # Create heatmap figure
    fig = px.imshow(
        signal_pivot.set_index('level_0').values,
        x=signal_pivot.columns[1:],  # Asset names
        y=signal_pivot['level_0'],   # Signal types
        color_continuous_scale=[
            [0, '#ef5350'],  # Strong sell
            [0.25, '#ef9a9a'],  # Weak sell
            [0.5, '#e0e0e0'],  # Neutral
            [0.75, '#81c784'],  # Weak buy
            [1, '#26a69a']     # Strong buy
        ],
        zmin=-1,
        zmax=1,
        text_auto=True
    )
    
    # Update layout
    fig.update_layout(
        title="Technical Signal Map",
        xaxis_title="Asset",
        yaxis_title="Signal Type",
        height=500,
        width=800,
        margin=dict(l=65, r=50, b=65, t=90)
    )
    
    # Update axis labels
    fig.update_xaxes(title_text="Asset")
    fig.update_yaxes(title_text="Signal Type")
    
    # Add custom hover information
    hover_template = "<b>%{y}</b><br>" + \
                     "<b>%{x}</b><br>" + \
                     "Signal: %{z}<br>" + \
                     "<extra></extra>"
    fig.update_traces(hovertemplate=hover_template)
    
    return fig

def create_divergence_map(data_dict):
    """
    Create a divergence map to identify price-indicator divergences
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with asset names as keys and DataFrames as values
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive divergence map
    """
    # Prepare divergence data
    divergence_data = []
    
    for asset_name, df in data_dict.items():
        if df is None or df.empty:
            continue
        
        # Calculate price changes
        price_change_1d = df['Close'].pct_change().iloc[-1] * 100
        price_change_5d = df['Close'].pct_change(5).iloc[-1] * 100
        price_change_20d = df['Close'].pct_change(20).iloc[-1] * 100
        
        # RSI divergence
        if 'RSI' in df.columns:
            rsi = df['RSI']
            rsi_current = rsi.iloc[-1]
            rsi_change = rsi.diff(5).iloc[-1]
            
            # Bearish divergence: price making higher highs, RSI making lower highs
            bearish_div_rsi = True if (price_change_5d > 0 and rsi_change < 0 and rsi_current > 70) else False
            
            # Bullish divergence: price making lower lows, RSI making higher lows
            bullish_div_rsi = True if (price_change_5d < 0 and rsi_change > 0 and rsi_current < 30) else False
        else:
            bearish_div_rsi = False
            bullish_div_rsi = False
        
        # MACD divergence
        if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
            macd = df['MACD']
            macd_signal = df['MACD_Signal']
            macd_hist = macd - macd_signal
            
            # Check for MACD divergence
            # Bearish: price up, MACD histogram down
            bearish_div_macd = True if (price_change_5d > 0 and macd_hist.diff(5).iloc[-1] < 0) else False
            
            # Bullish: price down, MACD histogram up
            bullish_div_macd = True if (price_change_5d < 0 and macd_hist.diff(5).iloc[-1] > 0) else False
        else:
            bearish_div_macd = False
            bullish_div_macd = False
        
        # Volume divergence
        if 'Volume' in df.columns:
            vol_change_5d = df['Volume'].pct_change(5).iloc[-1] * 100
            
            # Bearish: price up, volume down
            bearish_div_vol = True if (price_change_5d > 0 and vol_change_5d < 0) else False
            
            # Bullish: price down, volume up
            bullish_div_vol = True if (price_change_5d < 0 and vol_change_5d > 0) else False
        else:
            bearish_div_vol = False
            bullish_div_vol = False
        
        # Combine all divergences
        divergence_data.append({
            'Asset': asset_name,
            'Price_1D_%': round(price_change_1d, 2),
            'Price_5D_%': round(price_change_5d, 2),
            'Price_20D_%': round(price_change_20d, 2),
            'RSI_Bullish': bullish_div_rsi,
            'RSI_Bearish': bearish_div_rsi,
            'MACD_Bullish': bullish_div_macd,
            'MACD_Bearish': bearish_div_macd,
            'Volume_Bullish': bullish_div_vol,
            'Volume_Bearish': bearish_div_vol
        })
    
    # Convert to DataFrame
    div_df = pd.DataFrame(divergence_data)
    
    # Create a figure with subplots
    fig = make_subplots(
        rows=2, cols=1,
        row_heights=[0.3, 0.7],
        subplot_titles=["Price Performance (%)", "Divergence Map"]
    )
    
    # Add price performance bars
    for col in ['Price_1D_%', 'Price_5D_%', 'Price_20D_%']:
        fig.add_trace(
            go.Bar(
                name=col.replace('Price_', '').replace('_%', ''),
                x=div_df['Asset'],
                y=div_df[col],
                marker_color=['#26a69a' if val >= 0 else '#ef5350' for val in div_df[col]]
            ),
            row=1, col=1
        )
    
    # Create divergence heatmap data
    div_columns = ['RSI_Bullish', 'RSI_Bearish', 'MACD_Bullish', 'MACD_Bearish', 'Volume_Bullish', 'Volume_Bearish']
    
    # Pivot data for heatmap
    heatmap_data = []
    for asset in div_df['Asset']:
        asset_row = div_df[div_df['Asset'] == asset].iloc[0]
        for col in div_columns:
            indicator, direction = col.split('_')
            heatmap_data.append({
                'Asset': asset,
                'Indicator': indicator,
                'Direction': direction,
                'Value': 1 if asset_row[col] else 0
            })
    
    heatmap_df = pd.DataFrame(heatmap_data)
    heatmap_pivot = pd.pivot_table(
        heatmap_df,
        values='Value',
        index=['Indicator', 'Direction'],
        columns=['Asset']
    )
    
    # Add the heatmap
    fig.add_trace(
        go.Heatmap(
            z=heatmap_pivot.values,
            x=heatmap_pivot.columns,
            y=[f"{idx[0]} {idx[1]}" for idx in heatmap_pivot.index],
            colorscale=[
                [0, 'white'],
                [1, '#4caf50']  # Green for active divergences
            ],
            showscale=False,
            text=heatmap_pivot.values,
            texttemplate="%{text:1.0f}",
            hoverinfo='text',
            hovertext=[[f"{col} - {idx[0]} {idx[1]}: {'Yes' if val == 1 else 'No'}" 
                      for col in heatmap_pivot.columns] 
                     for idx, row in zip(heatmap_pivot.index, heatmap_pivot.values) 
                     for val in row]
        ),
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title="Price Performance and Technical Divergences",
        barmode='group',
        height=800,
        width=1000,
        margin=dict(l=65, r=50, b=65, t=90)
    )
    
    return fig

def create_regime_change_map(data_dict, lookback_window=50):
    """
    Create a market regime change map
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with asset names as keys and DataFrames as values
    lookback_window : int
        Lookback window for regime detection
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive regime change map
    """
    # Prepare regime data
    regime_data = []
    
    for asset_name, df in data_dict.items():
        if df is None or df.empty or len(df) < lookback_window:
            continue
        
        # Calculate returns and volatility
        returns = df['Close'].pct_change()
        volatility = returns.rolling(window=20).std() * np.sqrt(252)  # Annualized
        
        # Calculate trend strength (absolute value of average return)
        trend_strength = abs(returns.rolling(window=20).mean() * 252)  # Annualized
        
        # Calculate volume trend
        if 'Volume' in df.columns:
            volume_trend = df['Volume'].pct_change(20)
        else:
            volume_trend = pd.Series(0, index=df.index)
        
        # Determine regimes
        # High volatility + strong trend = Trending regime
        # High volatility + weak trend = Volatile regime
        # Low volatility + weak trend = Range-bound regime
        # Low volatility + strong trend = Steady trend regime
        
        # Current values
        curr_vol = volatility.iloc[-1]
        curr_trend = trend_strength.iloc[-1]
        curr_vol_percentile = percentile_rank(volatility, curr_vol)
        curr_trend_percentile = percentile_rank(trend_strength, curr_trend)
        
        # Determine current regime
        if curr_vol_percentile > 0.7 and curr_trend_percentile > 0.7:
            current_regime = "Trending"
            regime_color = "rgba(76, 175, 80, 0.8)"  # Green
        elif curr_vol_percentile > 0.7 and curr_trend_percentile <= 0.7:
            current_regime = "Volatile"
            regime_color = "rgba(244, 67, 54, 0.8)"  # Red
        elif curr_vol_percentile <= 0.7 and curr_trend_percentile <= 0.3:
            current_regime = "Range-bound"
            regime_color = "rgba(255, 152, 0, 0.8)"  # Orange
        else:
            current_regime = "Steady Trend"
            regime_color = "rgba(33, 150, 243, 0.8)"  # Blue
        
        # Check if regime changed in the last n periods
        last_n_periods = 5
        if len(volatility) <= last_n_periods or len(trend_strength) <= last_n_periods:
            regime_changed = False
        else:
            prev_vol = volatility.iloc[-last_n_periods-1]
            prev_trend = trend_strength.iloc[-last_n_periods-1]
            prev_vol_percentile = percentile_rank(volatility.iloc[:-last_n_periods], prev_vol)
            prev_trend_percentile = percentile_rank(trend_strength.iloc[:-last_n_periods], prev_trend)
            
            # Determine previous regime
            if prev_vol_percentile > 0.7 and prev_trend_percentile > 0.7:
                previous_regime = "Trending"
            elif prev_vol_percentile > 0.7 and prev_trend_percentile <= 0.7:
                previous_regime = "Volatile"
            elif prev_vol_percentile <= 0.7 and prev_trend_percentile <= 0.3:
                previous_regime = "Range-bound"
            else:
                previous_regime = "Steady Trend"
            
            regime_changed = previous_regime != current_regime
        
        # Momentum and mean reversion signals
        momentum_signal = returns.rolling(window=20).mean() > 0
        mean_rev_signal = (df['Close'] - df['Close'].rolling(window=20).mean()) / (df['Close'].rolling(window=20).std())
        
        # Current signal values
        curr_momentum = "Positive" if momentum_signal.iloc[-1] else "Negative"
        curr_mean_rev = "Overbought" if mean_rev_signal.iloc[-1] > 1.5 else "Oversold" if mean_rev_signal.iloc[-1] < -1.5 else "Neutral"
        
        # Add to regime data
        regime_data.append({
            'Asset': asset_name,
            'Current_Regime': current_regime,
            'Regime_Color': regime_color,
            'Regime_Changed': regime_changed,
            'Volatility': curr_vol,
            'Trend_Strength': curr_trend,
            'Momentum': curr_momentum,
            'Mean_Reversion': curr_mean_rev,
            'Volume_Trend': volume_trend.iloc[-1] if not pd.isna(volume_trend.iloc[-1]) else 0
        })
    
    # Convert to DataFrame
    regime_df = pd.DataFrame(regime_data)
    
    # Create figure
    fig = make_subplots(
        rows=2, cols=1,
        specs=[[{"type": "table"}], [{"type": "xy"}]],
        row_heights=[0.3, 0.7],
        subplot_titles=["Market Regime Analysis", "Volatility vs. Trend Strength"]
    )
    
    # Add table
    table_data = [
        list(regime_df['Asset']),
        list(regime_df['Current_Regime']),
        list(regime_df['Regime_Changed'].map({True: "Yes", False: "No"})),
        list(regime_df['Momentum']),
        list(regime_df['Mean_Reversion'])
    ]
    
    fig.add_trace(
        go.Table(
            header=dict(
                values=['Asset', 'Current Regime', 'Regime Changed', 'Momentum', 'Mean Reversion'],
                fill_color='rgb(230, 230, 230)',
                align='center'
            ),
            cells=dict(
                values=table_data,
                fill_color=[['white'], [regime_df['Regime_Color']], ['white'], ['white'], ['white']],
                align='center'
            )
        ),
        row=1, col=1
    )
    
    # Add scatter plot
    fig.add_trace(
        go.Scatter(
            x=regime_df['Volatility'],
            y=regime_df['Trend_Strength'],
            mode='markers+text',
            marker=dict(
                size=15,
                color=[color for color in regime_df['Regime_Color']],
                line=dict(width=1, color='black')
            ),
            text=regime_df['Asset'],
            textposition="top center",
            hovertemplate=
            '<b>%{text}</b><br>' +
            'Volatility: %{x:.2f}<br>' +
            'Trend Strength: %{y:.2f}<br>' +
            '<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add quadrant lines
    vol_median = regime_df['Volatility'].median()
    trend_median = regime_df['Trend_Strength'].median()
    
    fig.add_vline(x=vol_median, line_dash="dash", line_color="gray", row=2, col=1)
    fig.add_hline(y=trend_median, line_dash="dash", line_color="gray", row=2, col=1)
    
    # Add quadrant labels
    fig.add_annotation(
        x=vol_median/2,
        y=trend_median*1.5,
        text="Steady Trend",
        showarrow=False,
        row=2, col=1
    )
    
    fig.add_annotation(
        x=vol_median*1.5,
        y=trend_median*1.5,
        text="Trending",
        showarrow=False,
        row=2, col=1
    )
    
    fig.add_annotation(
        x=vol_median/2,
        y=trend_median/2,
        text="Range-bound",
        showarrow=False,
        row=2, col=1
    )
    
    fig.add_annotation(
        x=vol_median*1.5,
        y=trend_median/2,
        text="Volatile",
        showarrow=False,
        row=2, col=1
    )
    
    # Update layout
    fig.update_layout(
        title="Market Regime Analysis",
        xaxis2_title="Volatility (Annualized)",
        yaxis2_title="Trend Strength",
        height=800,
        width=1000,
        margin=dict(l=65, r=50, b=65, t=90)
    )
    
    return fig

def percentile_rank(series, value):
    """Calculate the percentile rank of a value in a series"""
    return (series < value).sum() / float(len(series))

def create_volume_profile(df, price_segments=20, title="Volume Profile"):
    """
    Create a volume profile for price distribution analysis
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    price_segments : int
        Number of price segments for the profile
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive volume profile chart
    """
    if df is None or df.empty or 'Volume' not in df.columns:
        return None
    
    # Calculate price range
    price_low = df['Low'].min()
    price_high = df['High'].max()
    
    # Create price segments
    segment_size = (price_high - price_low) / price_segments
    segments = [price_low + i * segment_size for i in range(price_segments + 1)]
    segment_mids = [(segments[i] + segments[i+1]) / 2 for i in range(price_segments)]
    
    # Calculate volume in each price segment
    volume_profile = np.zeros(price_segments)
    
    for i in range(len(df)):
        row = df.iloc[i]
        for j in range(price_segments):
            low_bound = segments[j]
            high_bound = segments[j+1]
            
            # Check if the price range overlaps with the segment
            if not (row['High'] < low_bound or row['Low'] > high_bound):
                # Calculate the ratio of the segment covered by the price range
                segment_coverage = min(high_bound, row['High']) - max(low_bound, row['Low'])
                segment_coverage = max(0, segment_coverage) / (row['High'] - row['Low'])
                
                # Add the proportional volume to the segment
                volume_profile[j] += row['Volume'] * segment_coverage
    
    # Create the figure
    fig = make_subplots(rows=1, cols=2, column_widths=[0.7, 0.3], shared_yaxes=True)
    
    # Add price chart
    fig.add_trace(
        go.Candlestick(
            x=df.index,
            open=df['Open'],
            high=df['High'],
            low=df['Low'],
            close=df['Close'],
            name='Price',
            increasing_line_color='#26a69a', 
            decreasing_line_color='#ef5350'
        ),
        row=1, col=1
    )
    
    # Add volume profile
    fig.add_trace(
        go.Bar(
            x=volume_profile,
            y=segment_mids,
            orientation='h',
            name='Volume Profile',
            marker_color='rgba(100, 100, 255, 0.7)'
        ),
        row=1, col=2
    )
    
    # Calculate point of control (price level with highest volume)
    poc_idx = np.argmax(volume_profile)
    poc_price = segment_mids[poc_idx]
    
    # Add point of control line
    fig.add_shape(
        type='line',
        x0=df.index[0],
        y0=poc_price,
        x1=df.index[-1],
        y1=poc_price,
        line=dict(color='red', width=2, dash='dash'),
        row=1, col=1
    )
    
    # Add annotation for POC
    fig.add_annotation(
        x=df.index[-1],
        y=poc_price,
        text="POC",
        showarrow=True,
        arrowhead=1,
        row=1, col=1
    )
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis2_title='Volume',
        showlegend=False,
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Update y-axis range to match price range
    fig.update_yaxes(range=[price_low, price_high])
    
    # Remove rangeslider
    fig.update_layout(xaxis_rangeslider_visible=False)
    
    return fig
