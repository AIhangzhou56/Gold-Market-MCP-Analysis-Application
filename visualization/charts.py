import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime

def plot_ohlc_data(df, title='Price Chart'):
    """
    Plot OHLC candlestick chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive candlestick chart
    """
    fig = go.Figure()
    
    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC',
        increasing_line_color='#26a69a', 
        decreasing_line_color='#ef5350'
    ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def plot_volume_analysis(df, title='Volume Analysis'):
    """
    Plot volume analysis chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive volume chart
    """
    # Create figure with secondary y-axis
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03, 
                        row_heights=[0.7, 0.3])
    
    # Add price candlestick trace
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC',
        increasing_line_color='#26a69a', 
        decreasing_line_color='#ef5350'
    ), row=1, col=1)
    
    # Determine colors for volume bars
    colors = ['#26a69a' if row.Close >= row.Open else '#ef5350' for _, row in df.iterrows()]
    
    # Add volume bar trace
    fig.add_trace(go.Bar(
        x=df.index,
        y=df['Volume'],
        name='Volume',
        marker_color=colors
    ), row=2, col=1)
    
    # Add a moving average of volume
    volume_ma = df['Volume'].rolling(window=20).mean()
    fig.add_trace(go.Scatter(
        x=df.index,
        y=volume_ma,
        name='Volume MA (20)',
        line=dict(color='rgba(100, 100, 255, 0.8)', width=2)
    ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis2_title='Date',
        yaxis2_title='Volume',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=700,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Hide weekends and major gaps
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # hide weekends
        ]
    )
    
    return fig

def plot_vwap(df, title='Volume Weighted Average Price'):
    """
    Plot VWAP chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OHLCV and VWAP data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive VWAP chart
    """
    fig = make_subplots(rows=1, cols=1)
    
    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC',
        increasing_line_color='#26a69a', 
        decreasing_line_color='#ef5350'
    ))
    
    # Add VWAP trace
    if 'VWAP' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['VWAP'],
            name='VWAP',
            line=dict(color='rgba(75, 0, 130, 0.8)', width=2)
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def plot_macd(df, title='MACD'):
    """
    Plot MACD chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with MACD data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive MACD chart
    """
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[0.7, 0.3])
    
    # Add price trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        name='Price',
        line=dict(color='#1E88E5', width=2)
    ), row=1, col=1)
    
    # Add MACD traces
    if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MACD'],
            name='MACD',
            line=dict(color='#5C6BC0', width=2)
        ), row=2, col=1)
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MACD_Signal'],
            name='Signal',
            line=dict(color='#FF7043', width=2)
        ), row=2, col=1)
        
        # Add histogram for MACD - Signal
        colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['MACD_Histogram']]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['MACD_Histogram'],
            name='Histogram',
            marker_color=colors
        ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis2_title='Date',
        yaxis2_title='MACD',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=700,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add a horizontal line at y=0 for the MACD plot
    fig.add_shape(
        type='line',
        x0=df.index[0],
        y0=0,
        x1=df.index[-1],
        y1=0,
        line=dict(color='gray', width=1, dash='dash'),
        row=2, col=1
    )
    
    return fig

def plot_rsi(df, title='Relative Strength Index'):
    """
    Plot RSI chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with RSI data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive RSI chart
    """
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[0.7, 0.3])
    
    # Add price trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        name='Price',
        line=dict(color='#1E88E5', width=2)
    ), row=1, col=1)
    
    # Add RSI trace
    if 'RSI' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['RSI'],
            name='RSI',
            line=dict(color='#5E35B1', width=2)
        ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis2_title='Date',
        yaxis2_title='RSI',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=700,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add horizontal lines at 30 and 70 for overbought/oversold levels
    fig.add_shape(
        type='line',
        x0=df.index[0],
        y0=30,
        x1=df.index[-1],
        y1=30,
        line=dict(color='green', width=1, dash='dash'),
        row=2, col=1
    )
    
    fig.add_shape(
        type='line',
        x0=df.index[0],
        y0=70,
        x1=df.index[-1],
        y1=70,
        line=dict(color='red', width=1, dash='dash'),
        row=2, col=1
    )
    
    # Add a horizontal line at y=50 for the midpoint
    fig.add_shape(
        type='line',
        x0=df.index[0],
        y0=50,
        x1=df.index[-1],
        y1=50,
        line=dict(color='gray', width=1, dash='dash'),
        row=2, col=1
    )
    
    # Set y-axis range for RSI
    fig.update_yaxes(range=[0, 100], row=2, col=1)
    
    return fig

def plot_bollinger_bands(df, title='Bollinger Bands'):
    """
    Plot Bollinger Bands chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Bollinger Bands data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive Bollinger Bands chart
    """
    fig = go.Figure()
    
    # Add candlestick trace
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC',
        increasing_line_color='#26a69a', 
        decreasing_line_color='#ef5350'
    ))
    
    # Add Bollinger Bands traces
    if all(col in df.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['BB_Upper'],
            name='Upper Band',
            line=dict(color='rgba(68, 138, 255, 0.7)', width=1),
            showlegend=True
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['BB_Middle'],
            name='Middle Band',
            line=dict(color='rgba(41, 98, 255, 0.9)', width=1.5),
            showlegend=True
        ))
        
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['BB_Lower'],
            name='Lower Band',
            line=dict(color='rgba(68, 138, 255, 0.7)', width=1),
            showlegend=True
        ))
        
        # Add fill between the bands
        fig.add_trace(go.Scatter(
            x=df.index.tolist() + df.index.tolist()[::-1],
            y=df['BB_Upper'].tolist() + df['BB_Lower'].tolist()[::-1],
            fill='toself',
            fillcolor='rgba(68, 138, 255, 0.2)',
            line=dict(color='rgba(255, 255, 255, 0)'),
            name='Band Range',
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=600,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def plot_oi_delta(df, title='Open Interest Delta'):
    """
    Plot Open Interest Delta chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with OI data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive OI Delta chart
    """
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[0.6, 0.4])
    
    # Add price trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        name='Price',
        line=dict(color='#1E88E5', width=2)
    ), row=1, col=1)
    
    # Add Open Interest trace
    if 'OpenInterest' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['OpenInterest'],
            name='Open Interest',
            line=dict(color='#7B1FA2', width=2)
        ), row=1, col=1)
    
    # Add OI Delta trace
    if 'OI_Delta' in df.columns:
        colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['OI_Delta']]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['OI_Delta'],
            name='OI Delta',
            marker_color=colors
        ), row=2, col=1)
        
        # Add a moving average of OI Delta
        oi_delta_ma = df['OI_Delta'].rolling(window=5).mean()
        fig.add_trace(go.Scatter(
            x=df.index,
            y=oi_delta_ma,
            name='OI Delta MA (5)',
            line=dict(color='#FF9800', width=2)
        ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price / Open Interest',
        xaxis2_title='Date',
        yaxis2_title='OI Delta',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=700,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add a horizontal line at y=0 for the OI Delta plot
    if 'OI_Delta' in df.columns:
        fig.add_shape(
            type='line',
            x0=df.index[0],
            y0=0,
            x1=df.index[-1],
            y1=0,
            line=dict(color='gray', width=1, dash='dash'),
            row=2, col=1
        )
    
    return fig

def plot_order_flow(df, title='Order Flow Analysis'):
    """
    Plot Order Flow chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Order Flow data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive Order Flow chart
    """
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[0.6, 0.4])
    
    # Add price trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        name='Price',
        line=dict(color='#1E88E5', width=2)
    ), row=1, col=1)
    
    # Add Order Flow metrics
    if 'OrderFlowDelta' in df.columns:
        # Color based on positive or negative values
        colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['OrderFlowDelta']]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['OrderFlowDelta'],
            name='Order Flow Delta',
            marker_color=colors
        ), row=2, col=1)
    
    if 'CumulativeDelta' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['CumulativeDelta'],
            name='Cumulative Delta',
            line=dict(color='#6A1B9A', width=2)
        ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis2_title='Date',
        yaxis2_title='Order Flow',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=700,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add a horizontal line at y=0 for the Order Flow Delta plot
    if 'OrderFlowDelta' in df.columns:
        fig.add_shape(
            type='line',
            x0=df.index[0],
            y0=0,
            x1=df.index[-1],
            y1=0,
            line=dict(color='gray', width=1, dash='dash'),
            row=2, col=1
        )
    
    return fig

def plot_market_depth(df, title='Market Depth Analysis'):
    """
    Plot Market Depth chart using Plotly
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with Market Depth data
    title : str
        Chart title
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive Market Depth chart
    """
    fig = make_subplots(rows=2, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[0.6, 0.4])
    
    # Add price trace
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['Close'],
        name='Price',
        line=dict(color='#1E88E5', width=2)
    ), row=1, col=1)
    
    # Add Market Depth metrics
    if 'BookImbalance' in df.columns:
        colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['BookImbalance']]
        
        fig.add_trace(go.Bar(
            x=df.index,
            y=df['BookImbalance'],
            name='Book Imbalance',
            marker_color=colors
        ), row=2, col=1)
    
    if 'MarketDepthPressure' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index,
            y=df['MarketDepthPressure'],
            name='Depth Pressure',
            line=dict(color='#FF9800', width=2)
        ), row=2, col=1)
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis2_title='Date',
        yaxis2_title='Market Depth',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=700,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Add a horizontal line at y=0 for the Book Imbalance plot
    if 'BookImbalance' in df.columns:
        fig.add_shape(
            type='line',
            x0=df.index[0],
            y0=0,
            x1=df.index[-1],
            y1=0,
            line=dict(color='gray', width=1, dash='dash'),
            row=2, col=1
        )
    
    return fig

def plot_equity_curve(equity_data):
    """
    Plot equity curve from backtesting results
    
    Parameters:
    -----------
    equity_data : pandas.DataFrame or pandas.Series
        Equity curve data
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive equity curve chart
    """
    fig = go.Figure()
    
    # Add equity curve trace
    fig.add_trace(go.Scatter(
        x=equity_data.index,
        y=equity_data,
        name='Equity Curve',
        line=dict(color='#2E7D32', width=2),
        fill='tozeroy',
        fillcolor='rgba(46, 125, 50, 0.2)'
    ))
    
    # Update layout
    fig.update_layout(
        title='Equity Curve',
        xaxis_title='Date',
        yaxis_title='Equity',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def plot_drawdowns(drawdowns):
    """
    Plot drawdowns from backtesting results
    
    Parameters:
    -----------
    drawdowns : pandas.DataFrame or pandas.Series
        Drawdown data
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive drawdowns chart
    """
    fig = go.Figure()
    
    # Add drawdowns trace
    fig.add_trace(go.Scatter(
        x=drawdowns.index,
        y=drawdowns * 100,  # Convert to percentage
        name='Drawdowns',
        line=dict(color='#C62828', width=2),
        fill='tozeroy',
        fillcolor='rgba(198, 40, 40, 0.2)'
    ))
    
    # Update layout
    fig.update_layout(
        title='Drawdowns',
        xaxis_title='Date',
        yaxis_title='Drawdown (%)',
        template='plotly_white',
        height=500,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

def plot_trade_distribution(trades):
    """
    Plot trade distribution from backtesting results
    
    Parameters:
    -----------
    trades : pandas.DataFrame
        Trade data with returns
        
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive trade distribution chart
    """
    fig = go.Figure()
    
    # Check if we have trade returns
    if 'return' in trades.columns:
        # Calculate bins for histogram
        returns = trades['return'] * 100  # Convert to percentage
        bin_size = (returns.max() - returns.min()) / 20
        
        # Add histogram trace
        fig.add_trace(go.Histogram(
            x=returns,
            name='Trade Returns',
            marker_color='#5E35B1',
            opacity=0.7,
            xbins=dict(
                size=bin_size
            )
        ))
        
        # Update layout
        fig.update_layout(
            title='Trade Return Distribution',
            xaxis_title='Return (%)',
            yaxis_title='Count',
            template='plotly_white',
            height=500,
            margin=dict(l=50, r=50, t=80, b=50)
        )
    else:
        # Alternative: plot trade counts by date
        if 'entry_date' in trades.columns:
            # Group trades by date
            trades_by_date = trades.groupby('entry_date').size()
            
            # Add bar chart trace
            fig.add_trace(go.Bar(
                x=trades_by_date.index,
                y=trades_by_date.values,
                name='Trade Count',
                marker_color='#5E35B1'
            ))
            
            # Update layout
            fig.update_layout(
                title='Trade Frequency',
                xaxis_title='Date',
                yaxis_title='Number of Trades',
                template='plotly_white',
                height=500,
                margin=dict(l=50, r=50, t=80, b=50)
            )
    
    return fig

def create_multi_chart(df, indicators=None, title="Multi-Indicator Chart"):
    """
    Create a comprehensive multi-indicator chart
    
    Parameters:
    -----------
    df : pandas.DataFrame
        DataFrame with price and indicator data
    indicators : list of str
        List of indicators to include
    title : str
        Chart title
    
    Returns:
    --------
    plotly.graph_objects.Figure
        Interactive multi-indicator chart
    """
    if indicators is None:
        indicators = []
    
    # Determine how many subplot rows we need
    num_indicator_plots = sum([ind in ['RSI', 'MACD', 'OI_Delta', 'OrderFlowDelta'] for ind in indicators])
    
    # Create subplots
    fig = make_subplots(rows=1 + num_indicator_plots, cols=1, 
                        shared_xaxes=True, 
                        vertical_spacing=0.03,
                        row_heights=[0.6] + [0.4/num_indicator_plots] * num_indicator_plots if num_indicator_plots > 0 else [1])
    
    # Main price chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='OHLC',
        increasing_line_color='#26a69a', 
        decreasing_line_color='#ef5350'
    ), row=1, col=1)
    
    # Add overlay indicators to price chart
    current_row = 2
    for ind in indicators:
        if ind == 'VWAP' and 'VWAP' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['VWAP'],
                name='VWAP',
                line=dict(color='rgba(75, 0, 130, 0.8)', width=2)
            ), row=1, col=1)
            
        elif ind == 'Bollinger Bands' and all(col in df.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['BB_Upper'],
                name='Upper Band',
                line=dict(color='rgba(68, 138, 255, 0.7)', width=1)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['BB_Middle'],
                name='Middle Band',
                line=dict(color='rgba(41, 98, 255, 0.9)', width=1.5)
            ), row=1, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['BB_Lower'],
                name='Lower Band',
                line=dict(color='rgba(68, 138, 255, 0.7)', width=1)
            ), row=1, col=1)
            
        elif ind == 'RSI' and 'RSI' in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['RSI'],
                name='RSI',
                line=dict(color='#5E35B1', width=2)
            ), row=current_row, col=1)
            
            # Add horizontal lines for overbought/oversold levels
            fig.add_shape(
                type='line',
                x0=df.index[0],
                y0=30,
                x1=df.index[-1],
                y1=30,
                line=dict(color='green', width=1, dash='dash'),
                row=current_row, col=1
            )
            
            fig.add_shape(
                type='line',
                x0=df.index[0],
                y0=70,
                x1=df.index[-1],
                y1=70,
                line=dict(color='red', width=1, dash='dash'),
                row=current_row, col=1
            )
            
            fig.add_shape(
                type='line',
                x0=df.index[0],
                y0=50,
                x1=df.index[-1],
                y1=50,
                line=dict(color='gray', width=1, dash='dash'),
                row=current_row, col=1
            )
            
            # Set y-axis range for RSI
            fig.update_yaxes(range=[0, 100], row=current_row, col=1, title_text='RSI')
            current_row += 1
            
        elif ind == 'MACD' and all(col in df.columns for col in ['MACD', 'MACD_Signal', 'MACD_Histogram']):
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MACD'],
                name='MACD',
                line=dict(color='#5C6BC0', width=2)
            ), row=current_row, col=1)
            
            fig.add_trace(go.Scatter(
                x=df.index,
                y=df['MACD_Signal'],
                name='Signal',
                line=dict(color='#FF7043', width=2)
            ), row=current_row, col=1)
            
            # Add histogram for MACD - Signal
            colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['MACD_Histogram']]
            
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['MACD_Histogram'],
                name='Histogram',
                marker_color=colors
            ), row=current_row, col=1)
            
            # Add zero line
            fig.add_shape(
                type='line',
                x0=df.index[0],
                y0=0,
                x1=df.index[-1],
                y1=0,
                line=dict(color='gray', width=1, dash='dash'),
                row=current_row, col=1
            )
            
            fig.update_yaxes(title_text='MACD', row=current_row, col=1)
            current_row += 1
            
        elif ind == 'OI_Delta' and 'OI_Delta' in df.columns:
            colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['OI_Delta']]
            
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['OI_Delta'],
                name='OI Delta',
                marker_color=colors
            ), row=current_row, col=1)
            
            # Add zero line
            fig.add_shape(
                type='line',
                x0=df.index[0],
                y0=0,
                x1=df.index[-1],
                y1=0,
                line=dict(color='gray', width=1, dash='dash'),
                row=current_row, col=1
            )
            
            fig.update_yaxes(title_text='OI Delta', row=current_row, col=1)
            current_row += 1
            
        elif ind == 'OrderFlowDelta' and 'OrderFlowDelta' in df.columns:
            colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df['OrderFlowDelta']]
            
            fig.add_trace(go.Bar(
                x=df.index,
                y=df['OrderFlowDelta'],
                name='Order Flow Delta',
                marker_color=colors
            ), row=current_row, col=1)
            
            # Add zero line
            fig.add_shape(
                type='line',
                x0=df.index[0],
                y0=0,
                x1=df.index[-1],
                y1=0,
                line=dict(color='gray', width=1, dash='dash'),
                row=current_row, col=1
            )
            
            fig.update_yaxes(title_text='Order Flow', row=current_row, col=1)
            current_row += 1
    
    # Update layout
    fig.update_layout(
        title=title,
        xaxis_title='Date',
        yaxis_title='Price',
        xaxis_rangeslider_visible=False,
        template='plotly_white',
        height=800,
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig
