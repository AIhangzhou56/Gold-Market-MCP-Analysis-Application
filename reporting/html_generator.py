import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import jinja2
import base64
import io
import datetime
import os
from typing import Dict, Any, List, Optional

def generate_report(data_dict: Dict[str, pd.DataFrame], report_meta: Dict[str, Any], 
                  backtest_results: Optional[Dict[str, Any]] = None) -> str:
    """
    Generate an HTML report based on market data and analysis results
    
    Parameters:
    -----------
    data_dict : dict
        Dictionary with asset names as keys and DataFrames as values
    report_meta : dict
        Dictionary with report metadata (title, author, date, sections)
    backtest_results : dict or None
        Dictionary with backtest results if available
        
    Returns:
    --------
    str
        HTML content of the report
    """
    # Create Jinja2 environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(os.path.dirname(os.path.abspath(__file__))),
        autoescape=jinja2.select_autoescape(['html', 'xml'])
    )
    
    # If template file doesn't exist, create one inline
    template_str = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{ report_meta.title }}</title>
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        <style>
            body {
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background-color: #fff;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 1px solid #eee;
            }
            h1 {
                color: #2c3e50;
                margin-bottom: 10px;
            }
            h2 {
                color: #2980b9;
                margin-top: 30px;
                padding-bottom: 10px;
                border-bottom: 1px solid #eee;
            }
            h3 {
                color: #3498db;
                margin-top: 20px;
            }
            .meta {
                color: #7f8c8d;
                font-size: 1.1em;
            }
            .chart-container {
                width: 100%;
                height: 500px;
                margin: 20px 0;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            th, td {
                padding: 12px 15px;
                border-bottom: 1px solid #ddd;
                text-align: left;
            }
            th {
                background-color: #f5f5f5;
                font-weight: bold;
            }
            tr:hover {
                background-color: #f9f9f9;
            }
            .section {
                margin-bottom: 40px;
            }
            .code {
                background-color: #f5f5f5;
                padding: 15px;
                border-radius: 5px;
                font-family: Consolas, Monaco, 'Andale Mono', monospace;
                white-space: pre-wrap;
                overflow-x: auto;
            }
            .summary-box {
                background-color: #f8f9fa;
                border-left: 4px solid #4285f4;
                padding: 15px;
                margin: 20px 0;
            }
            .positive {
                color: #27ae60;
            }
            .negative {
                color: #e74c3c;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>{{ report_meta.title }}</h1>
                <div class="meta">
                    <p>Author: {{ report_meta.author }} | Date: {{ report_meta.date }}</p>
                </div>
            </div>
            
            <div class="content">
                {% if 'Market Overview' in report_meta.sections %}
                <div class="section">
                    <h2>Market Overview</h2>
                    {% for asset_name, asset_data in market_overview.items() %}
                    <div class="asset-summary">
                        <h3>{{ asset_name }}</h3>
                        <div class="summary-box">
                            <p><strong>Data Range:</strong> {{ asset_data.date_range }}</p>
                            <p><strong>Latest Price:</strong> {{ asset_data.latest_price }}</p>
                            <p><strong>Change (1D):</strong> 
                                <span class="{{ 'positive' if asset_data.change_1d >= 0 else 'negative' }}">
                                    {{ asset_data.change_1d }}%
                                </span>
                            </p>
                            <p><strong>Change (5D):</strong> 
                                <span class="{{ 'positive' if asset_data.change_5d >= 0 else 'negative' }}">
                                    {{ asset_data.change_5d }}%
                                </span>
                            </p>
                        </div>
                        <div class="chart-container" id="price-chart-{{ loop.index }}"></div>
                        <script>
                            var data = {{ asset_data.price_chart | safe }};
                            Plotly.newPlot('price-chart-{{ loop.index }}', data.data, data.layout);
                        </script>
                    </div>
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if 'Technical Analysis' in report_meta.sections %}
                <div class="section">
                    <h2>Technical Analysis</h2>
                    {% for asset_name, charts in technical_charts.items() %}
                    <h3>{{ asset_name }}</h3>
                    {% for chart_name, chart_data in charts.items() %}
                    <h4>{{ chart_name }}</h4>
                    <div class="chart-container" id="tech-chart-{{ loop.parent.index }}-{{ loop.index }}"></div>
                    <script>
                        var data = {{ chart_data | safe }};
                        Plotly.newPlot('tech-chart-{{ loop.parent.index }}-{{ loop.index }}', data.data, data.layout);
                    </script>
                    {% endfor %}
                    {% endfor %}
                </div>
                {% endif %}
                
                {% if 'Signal Map' in report_meta.sections and correlation_chart %}
                <div class="section">
                    <h2>Signal Map</h2>
                    <h3>Correlation Analysis</h3>
                    <div class="chart-container" id="correlation-chart"></div>
                    <script>
                        var data = {{ correlation_chart | safe }};
                        Plotly.newPlot('correlation-chart', data.data, data.layout);
                    </script>
                    
                    {% if divergence_chart %}
                    <h3>Divergence Analysis</h3>
                    <div class="chart-container" id="divergence-chart"></div>
                    <script>
                        var data = {{ divergence_chart | safe }};
                        Plotly.newPlot('divergence-chart', data.data, data.layout);
                    </script>
                    {% endif %}
                    
                    {% if tech_signal_chart %}
                    <h3>Technical Signal Map</h3>
                    <div class="chart-container" id="tech-signal-chart"></div>
                    <script>
                        var data = {{ tech_signal_chart | safe }};
                        Plotly.newPlot('tech-signal-chart', data.data, data.layout);
                    </script>
                    {% endif %}
                </div>
                {% endif %}
                
                {% if 'Strategy Backtest' in report_meta.sections and backtest_data %}
                <div class="section">
                    <h2>Strategy Backtest</h2>
                    <div class="summary-box">
                        <h3>Performance Summary</h3>
                        <p><strong>Total Return:</strong> 
                            <span class="{{ 'positive' if backtest_data.metrics.total_return >= 0 else 'negative' }}">
                                {{ backtest_data.metrics.total_return }}%
                            </span>
                        </p>
                        <p><strong>Annualized Return:</strong> 
                            <span class="{{ 'positive' if backtest_data.metrics.annualized_return >= 0 else 'negative' }}">
                                {{ backtest_data.metrics.annualized_return }}%
                            </span>
                        </p>
                        <p><strong>Sharpe Ratio:</strong> {{ backtest_data.metrics.sharpe_ratio }}</p>
                        <p><strong>Max Drawdown:</strong> {{ backtest_data.metrics.max_drawdown }}%</p>
                        <p><strong>Win Rate:</strong> {{ backtest_data.metrics.win_rate }}%</p>
                        <p><strong>Profit Factor:</strong> {{ backtest_data.metrics.profit_factor }}</p>
                        <p><strong>Number of Trades:</strong> {{ backtest_data.metrics.num_trades }}</p>
                    </div>
                    
                    <h3>Equity Curve</h3>
                    <div class="chart-container" id="equity-chart"></div>
                    <script>
                        var data = {{ backtest_data.equity_chart | safe }};
                        Plotly.newPlot('equity-chart', data.data, data.layout);
                    </script>
                    
                    <h3>Drawdown</h3>
                    <div class="chart-container" id="drawdown-chart"></div>
                    <script>
                        var data = {{ backtest_data.drawdown_chart | safe }};
                        Plotly.newPlot('drawdown-chart', data.data, data.layout);
                    </script>
                    
                    {% if backtest_data.trade_chart %}
                    <h3>Trade Distribution</h3>
                    <div class="chart-container" id="trade-chart"></div>
                    <script>
                        var data = {{ backtest_data.trade_chart | safe }};
                        Plotly.newPlot('trade-chart', data.data, data.layout);
                    </script>
                    {% endif %}
                    
                    <h3>Strategy Code</h3>
                    <div class="code">{{ backtest_data.strategy_code }}</div>
                </div>
                {% endif %}
                
                {% if 'Conclusions' in report_meta.sections %}
                <div class="section">
                    <h2>Conclusions</h2>
                    <div class="summary-box">
                        <h3>Market Summary</h3>
                        <p>{{ conclusions.market_summary }}</p>
                        
                        <h3>Technical Outlook</h3>
                        <p>{{ conclusions.technical_outlook }}</p>
                        
                        {% if conclusions.strategy_outlook %}
                        <h3>Strategy Outlook</h3>
                        <p>{{ conclusions.strategy_outlook }}</p>
                        {% endif %}
                    </div>
                </div>
                {% endif %}
            </div>
            
            <div class="footer">
                <p>Report generated on {{ generation_timestamp }}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    template = env.from_string(template_str)
    
    # Prepare data for the template
    template_data = {
        'report_meta': report_meta,
        'generation_timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'market_overview': {},
        'technical_charts': {},
        'correlation_chart': None,
        'divergence_chart': None,
        'tech_signal_chart': None,
        'backtest_data': None,
        'conclusions': {
            'market_summary': "The market has shown significant volatility during the analyzed period.",
            'technical_outlook': "Technical indicators suggest a cautious approach to market positioning.",
            'strategy_outlook': None
        }
    }
    
    # Process market overview section
    if 'Market Overview' in report_meta['sections']:
        for asset_name, df in data_dict.items():
            if df is not None and not df.empty:
                # Calculate date range
                date_range = f"{df.index.min().strftime('%Y-%m-%d')} to {df.index.max().strftime('%Y-%m-%d')}"
                
                # Calculate latest price and changes
                latest_price = f"{df['Close'].iloc[-1]:.2f}"
                change_1d = f"{df['Close'].pct_change().iloc[-1] * 100:.2f}"
                change_5d = f"{df['Close'].pct_change(5).iloc[-1] * 100:.2f}"
                
                # Create price chart
                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=df.index,
                    open=df['Open'],
                    high=df['High'],
                    low=df['Low'],
                    close=df['Close'],
                    name='Price'
                ))
                
                fig.update_layout(
                    title=f"{asset_name} Price Chart",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=500,
                    template="plotly_white"
                )
                
                # Store data
                template_data['market_overview'][asset_name] = {
                    'date_range': date_range,
                    'latest_price': latest_price,
                    'change_1d': change_1d,
                    'change_5d': change_5d,
                    'price_chart': fig.to_json()
                }
    
    # Process technical analysis section
    if 'Technical Analysis' in report_meta['sections']:
        for asset_name, df in data_dict.items():
            if df is not None and not df.empty:
                template_data['technical_charts'][asset_name] = {}
                
                # MACD chart
                if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['Close'], name='Price', line=dict(color='#1E88E5')
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['MACD'], name='MACD', line=dict(color='#5C6BC0')
                    ), row=2, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['MACD_Signal'], name='Signal', line=dict(color='#FF7043')
                    ), row=2, col=1)
                    
                    fig.update_layout(
                        title="MACD Analysis",
                        height=500,
                        template="plotly_white"
                    )
                    
                    template_data['technical_charts'][asset_name]['MACD'] = fig.to_json()
                
                # RSI chart
                if 'RSI' in df.columns:
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.03, row_heights=[0.7, 0.3])
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['Close'], name='Price', line=dict(color='#1E88E5')
                    ), row=1, col=1)
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['RSI'], name='RSI', line=dict(color='#5E35B1')
                    ), row=2, col=1)
                    
                    # Add overbought/oversold lines
                    fig.add_shape(
                        type='line', x0=df.index[0], y0=70, x1=df.index[-1], y1=70,
                        line=dict(color='red', width=1, dash='dash'), row=2, col=1
                    )
                    
                    fig.add_shape(
                        type='line', x0=df.index[0], y0=30, x1=df.index[-1], y1=30,
                        line=dict(color='green', width=1, dash='dash'), row=2, col=1
                    )
                    
                    fig.update_layout(
                        title="RSI Analysis",
                        height=500,
                        template="plotly_white"
                    )
                    
                    # Set y-axis range for RSI
                    fig.update_yaxes(range=[0, 100], row=2, col=1)
                    
                    template_data['technical_charts'][asset_name]['RSI'] = fig.to_json()
                
                # Bollinger Bands chart
                if all(col in df.columns for col in ['BB_Upper', 'BB_Middle', 'BB_Lower']):
                    fig = go.Figure()
                    
                    fig.add_trace(go.Candlestick(
                        x=df.index,
                        open=df['Open'],
                        high=df['High'],
                        low=df['Low'],
                        close=df['Close'],
                        name='Price'
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['BB_Upper'], name='Upper Band', line=dict(color='rgba(68, 138, 255, 0.7)')
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['BB_Middle'], name='Middle Band', line=dict(color='rgba(41, 98, 255, 0.9)')
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=df.index, y=df['BB_Lower'], name='Lower Band', line=dict(color='rgba(68, 138, 255, 0.7)')
                    ))
                    
                    fig.update_layout(
                        title="Bollinger Bands Analysis",
                        height=500,
                        template="plotly_white"
                    )
                    
                    template_data['technical_charts'][asset_name]['Bollinger Bands'] = fig.to_json()
    
    # Process Signal Map section
    if 'Signal Map' in report_meta['sections'] and len(data_dict) >= 2:
        # Create correlation matrix
        close_prices = pd.DataFrame()
        
        for asset_name, df in data_dict.items():
            if df is not None and not df.empty:
                close_prices[asset_name] = df['Close']
        
        if not close_prices.empty:
            returns = close_prices.pct_change().dropna()
            corr_matrix = returns.corr()
            
            fig = px.imshow(
                corr_matrix,
                text_auto=True,
                color_continuous_scale='RdBu_r',
                zmin=-1,
                zmax=1,
                labels=dict(color="Correlation")
            )
            
            fig.update_layout(
                title="Price Correlation Between Assets",
                height=500,
                width=700
            )
            
            template_data['correlation_chart'] = fig.to_json()
            
            # Create technical signal map
            signal_data = []
            
            for asset_name, df in data_dict.items():
                if df is not None and not df.empty:
                    # Check for various technical signals
                    rsi_signal = "Oversold" if 'RSI' in df.columns and df['RSI'].iloc[-1] < 30 else \
                                "Overbought" if 'RSI' in df.columns and df['RSI'].iloc[-1] > 70 else "Neutral"
                    
                    macd_signal = "Bullish" if all(col in df.columns for col in ['MACD', 'MACD_Signal']) and \
                                 df['MACD'].iloc[-1] > df['MACD_Signal'].iloc[-1] else \
                                 "Bearish" if all(col in df.columns for col in ['MACD', 'MACD_Signal']) and \
                                 df['MACD'].iloc[-1] < df['MACD_Signal'].iloc[-1] else "Neutral"
                    
                    signal_data.append({
                        'Asset': asset_name,
                        'Price Change (1D)': df['Close'].pct_change().iloc[-1] * 100,
                        'RSI Signal': rsi_signal,
                        'MACD Signal': macd_signal
                    })
            
            if signal_data:
                signal_df = pd.DataFrame(signal_data)
                
                # Create divergence chart
                divergence_data = []
                for asset_name, df in data_dict.items():
                    if df is not None and not df.empty:
                        # Calculate price changes
                        price_change_1d = df['Close'].pct_change().iloc[-1] * 100
                        price_change_5d = df['Close'].pct_change(5).iloc[-1] * 100
                        
                        # Check for RSI divergence
                        rsi_bullish = False
                        rsi_bearish = False
                        if 'RSI' in df.columns:
                            rsi = df['RSI']
                            rsi_change = rsi.diff(5).iloc[-1]
                            
                            rsi_bullish = price_change_5d < 0 and rsi_change > 0 and rsi.iloc[-1] < 30
                            rsi_bearish = price_change_5d > 0 and rsi_change < 0 and rsi.iloc[-1] > 70
                        
                        # Check for MACD divergence
                        macd_bullish = False
                        macd_bearish = False
                        if all(col in df.columns for col in ['MACD', 'MACD_Signal']):
                            macd = df['MACD']
                            macd_signal = df['MACD_Signal']
                            macd_hist = macd - macd_signal
                            
                            macd_bullish = price_change_5d < 0 and macd_hist.diff(5).iloc[-1] > 0
                            macd_bearish = price_change_5d > 0 and macd_hist.diff(5).iloc[-1] < 0
                        
                        divergence_data.append({
                            'Asset': asset_name,
                            'Price_1D_%': round(price_change_1d, 2),
                            'Price_5D_%': round(price_change_5d, 2),
                            'RSI_Bullish': 1 if rsi_bullish else 0,
                            'RSI_Bearish': 1 if rsi_bearish else 0,
                            'MACD_Bullish': 1 if macd_bullish else 0,
                            'MACD_Bearish': 1 if macd_bearish else 0
                        })
                
                if divergence_data:
                    div_df = pd.DataFrame(divergence_data)
                    
                    # Create figure for divergence map
                    fig = make_subplots(
                        rows=2, cols=1,
                        row_heights=[0.3, 0.7],
                        subplot_titles=["Price Performance (%)", "Divergence Map"]
                    )
                    
                    # Add price performance bars
                    for col in ['Price_1D_%', 'Price_5D_%']:
                        fig.add_trace(
                            go.Bar(
                                name=col.replace('Price_', '').replace('_%', ''),
                                x=div_df['Asset'],
                                y=div_df[col],
                                marker_color=['#26a69a' if val >= 0 else '#ef5350' for val in div_df[col]]
                            ),
                            row=1, col=1
                        )
                    
                    # Create heatmap data for divergences
                    div_columns = ['RSI_Bullish', 'RSI_Bearish', 'MACD_Bullish', 'MACD_Bearish']
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
                    
                    # Add heatmap to figure
                    fig.add_trace(
                        go.Heatmap(
                            z=heatmap_pivot.values,
                            x=heatmap_pivot.columns,
                            y=[f"{idx[0]} {idx[1]}" for idx in heatmap_pivot.index],
                            colorscale=[[0, 'white'], [1, '#4caf50']],
                            showscale=False
                        ),
                        row=2, col=1
                    )
                    
                    fig.update_layout(
                        title="Technical Divergences",
                        height=600,
                        template="plotly_white"
                    )
                    
                    template_data['divergence_chart'] = fig.to_json()
    
    # Process Backtest section
    if 'Strategy Backtest' in report_meta['sections'] and backtest_results:
        backtest_data = {}
        
        # Extract metrics
        backtest_data['metrics'] = backtest_results['metrics']
        
        # Create equity curve chart
        equity_curve = backtest_results['equity_curve']
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=equity_curve.index,
            y=equity_curve,
            name='Equity Curve',
            line=dict(color='#2E7D32', width=2),
            fill='tozeroy',
            fillcolor='rgba(46, 125, 50, 0.2)'
        ))
        
        fig.update_layout(
            title='Equity Curve',
            xaxis_title='Date',
            yaxis_title='Equity',
            height=500,
            template="plotly_white"
        )
        
        backtest_data['equity_chart'] = fig.to_json()
        
        # Create drawdown chart
        drawdowns = backtest_results['drawdowns']
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=drawdowns.index,
            y=drawdowns * 100,
            name='Drawdown',
            line=dict(color='#C62828', width=2),
            fill='tozeroy',
            fillcolor='rgba(198, 40, 40, 0.2)'
        ))
        
        fig.update_layout(
            title='Drawdowns',
            xaxis_title='Date',
            yaxis_title='Drawdown (%)',
            height=500,
            template="plotly_white"
        )
        
        backtest_data['drawdown_chart'] = fig.to_json()
        
        # Create trade distribution chart
        if 'trades' in backtest_results and not backtest_results['trades'].empty:
            trades = backtest_results['trades']
            
            if 'return' in trades.columns:
                # Use returns histogram
                fig = go.Figure()
                
                fig.add_trace(go.Histogram(
                    x=trades['return'] * 100,
                    name='Trade Returns',
                    marker_color='#5E35B1',
                    opacity=0.7,
                    nbinsx=20
                ))
                
                fig.update_layout(
                    title='Trade Return Distribution',
                    xaxis_title='Return (%)',
                    yaxis_title='Count',
                    height=500,
                    template="plotly_white"
                )
                
                backtest_data['trade_chart'] = fig.to_json()
        
        # Add strategy code
        backtest_data['strategy_code'] = backtest_results['strategy_code']
        
        # Add strategy outlook to conclusions
        template_data['conclusions']['strategy_outlook'] = get_strategy_outlook(backtest_results)
        
        template_data['backtest_data'] = backtest_data
    
    # Generate HTML
    html_content = template.render(**template_data)
    
    return html_content

def plot_to_html(fig):
    """
    Convert a plotly figure to HTML string
    
    Parameters:
    -----------
    fig : plotly.graph_objects.Figure
        Plotly figure to convert
        
    Returns:
    --------
    str
        HTML representation of the figure
    """
    return fig.to_html(full_html=False, include_plotlyjs=False)

def get_strategy_outlook(backtest_results):
    """
    Generate strategy outlook text based on backtest results
    
    Parameters:
    -----------
    backtest_results : dict
        Dictionary with backtest results
        
    Returns:
    --------
    str
        Strategy outlook text
    """
    metrics = backtest_results['metrics']
    
    if metrics['total_return'] > 0 and metrics['sharpe_ratio'] > 1:
        return (f"The strategy shows promising results with a positive return of {metrics['total_return']}% "
                f"and a Sharpe ratio of {metrics['sharpe_ratio']}. With a win rate of {metrics['win_rate']}%, "
                f"it demonstrates good reliability. Consider implementing this strategy with appropriate risk management.")
    elif metrics['total_return'] > 0:
        return (f"The strategy shows a positive return of {metrics['total_return']}%, but with a Sharpe ratio "
                f"of only {metrics['sharpe_ratio']}, risk-adjusted performance could be improved. "
                f"Consider refining the strategy parameters or combining with additional signals.")
    else:
        return (f"The strategy did not perform well during the test period, with a return of {metrics['total_return']}% "
                f"and a Sharpe ratio of {metrics['sharpe_ratio']}. It's recommended to revise the strategy "
                f"parameters or explore alternative approaches.")
