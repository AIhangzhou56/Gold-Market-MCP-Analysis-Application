import streamlit as st
import pandas as pd
import numpy as np
import datetime
import time
import os
import base64
from datetime import timedelta
from streamlit_option_menu import option_menu

# Import custom modules
from data_fetchers import alpha_vantage, tushare_fetcher, yfinance_fetcher
from data_processing import cleaner, continuous_stitcher
from indicators import technical, orderflow
from visualization import charts, signal_maps
from backtesting import strategy, evaluator
from reporting import html_generator, pdf_exporter
from utils import helpers
from database.manager import DatabaseManager

# Set page configuration
st.set_page_config(
    page_title="MCP智能分析系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with MCP theme
st.markdown("""
<style>
    :root {
        --primary: #004e89;      /* 深海蓝 */
        --secondary: #ffc745;    /* MCP 金 */
        --bg: #f6f9fc;
        --font-sans: 'Inter', sans-serif;
    }
    
    html, body, [class*="st-"] {
        font-family: var(--font-sans);
    }
    
    .title-box {
        background-color: var(--primary);
        padding: 1rem 2rem;
        border-radius: 10px;
        color: white;
        font-size: 26px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    [data-baseweb="tab"] button {
        font-weight: 600;
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: var(--bg);
        padding: 10px 20px;
        border-radius: 5px 5px 0px 0px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: var(--primary);
        color: white;
    }
    
    .stDateInput > div > div {
        background-color: var(--bg);
    }
    
    .stRadio > div {
        background-color: var(--bg);
        padding: 10px;
        border-radius: 5px;
    }
    
    .stSlider > div > div {
        background-color: var(--primary);
    }
    
    .stButton > button {
        background-color: var(--primary);
        color: white;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background-color: var(--secondary);
        color: var(--primary);
    }
    
    .metric-card {
        background-color: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        text-align: center;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: var(--primary);
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
    }
    
    .signal-positive {
        color: #5cb85c;
    }
    
    .signal-negative {
        color: #d9534f;
    }
    
    .signal-neutral {
        color: #f0ad4e;
    }
    
    .footer {
        text-align: center;
        color: #888;
        padding: 10px;
        font-size: 0.8rem;
        margin-top: 2rem;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# Top nav bar with option_menu
selected_section = option_menu(
    menu_title=None,
    options=["Data Lab", "MCP Signals", "Strategy", "Reports", "Settings"],
    icons=["database", "activity", "cpu", "file-earmark-richtext", "gear"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#004e89", "margin-bottom": "15px"},
        "icon": {"color": "white", "font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#023664", "color": "white"},
        "nav-link-selected": {"background-color": "#ffc745", "color": "#004e89", "font-weight": "bold"},
    }
)

# Custom Header
st.markdown("""
    <div class='title-box'>
        MCP智能分析系统 · 上海期货黄金合约（AU）与国际金价联动研究
    </div>
""", unsafe_allow_html=True)

# Display svg logo
try:
    with open("assets/logo.svg", "r") as file:
        svg_content = file.read()
    st.sidebar.markdown(f'<div style="text-align:center">{svg_content}</div>', unsafe_allow_html=True)
except Exception as e:
    st.sidebar.image("generated-icon.png", width=120)

# Sidebar title
st.sidebar.markdown("<h2 style='text-align: center; color: #1f3b4d;'>数据控制面板</h2>", unsafe_allow_html=True)

# Sidebar with improved layout
with st.sidebar:
    # Date range selection with better layout
    st.sidebar.subheader("日期范围")
    col1, col2 = st.columns(2)
    with col1:
        end_date = st.date_input("结束", value=datetime.datetime.now().date())
    with col2:
        date_range = st.selectbox(
            "时间周期",
            ["1周", "1个月", "3个月", "6个月", "1年", "今年至今"],
            index=2
        )

    # Calculate start date based on selection
    if date_range == "1周":
        start_date = end_date - timedelta(days=7)
    elif date_range == "1个月":
        start_date = end_date - timedelta(days=30)
    elif date_range == "3个月":
        start_date = end_date - timedelta(days=90)
    elif date_range == "6个月":
        start_date = end_date - timedelta(days=180)
    elif date_range == "1年":
        start_date = end_date - timedelta(days=365)
    elif date_range == "今年至今":
        start_date = datetime.date(end_date.year, 1, 1)
    
    # Show date range
    st.caption(f"数据日期: {start_date} 至 {end_date}")
    
    # Data frequency selection
    st.sidebar.subheader("数据频率")
    freq = st.select_slider(
        "频率", 
        ["Tick", "1分钟", "5分钟", "15分钟", "1小时", "日线"],
        value="日线"
    )
    
    # Map frequency to standard format
    freq_map = {
        "Tick": "tick",
        "1分钟": "1min",
        "5分钟": "5min",
        "15分钟": "15min",
        "1小时": "1h",
        "日线": "1d"
    }
    data_frequency = freq

    # Data source selection
    st.sidebar.subheader("数据源选择")
    markets = st.multiselect(
        "市场",
        ["上海期货交易所黄金主力合约 (AU)", "COMEX 黄金期货 (GC)", "国际现货金价 (XAU/USD)"],
        default=["上海期货交易所黄金主力合约 (AU)", "COMEX 黄金期货 (GC)", "国际现货金价 (XAU/USD)"]
    )
    
    # Map markets to code
    use_tushare = "上海期货交易所黄金主力合约 (AU)" in markets
    use_yfinance = "COMEX 黄金期货 (GC)" in markets
    use_alphavantage = "国际现货金价 (XAU/USD)" in markets
    
    # Technical Indicators with better grouping
    st.sidebar.subheader("MCP 因子")
    factors = st.multiselect(
        "选择因子",
        ["成交量加权平均价格 (VWAP)", 
         "指数平滑异同移动平均线 (MACD)", 
         "相对强弱指标 (RSI)", 
         "布林带 (Bollinger Bands)", 
         "持仓量变化 (OI Delta)",
         "订单流 (Order Flow)",
         "市场深度 (Market Depth)"],
        default=["成交量加权平均价格 (VWAP)", "指数平滑异同移动平均线 (MACD)"]
    )
    
    # Map factors to variables
    use_vwap = "成交量加权平均价格 (VWAP)" in factors
    use_macd = "指数平滑异同移动平均线 (MACD)" in factors
    use_rsi = "相对强弱指标 (RSI)" in factors
    use_bollinger = "布林带 (Bollinger Bands)" in factors
    use_oi_delta = "持仓量变化 (OI Delta)" in factors
    use_order_flow = "订单流 (Order Flow)" in factors
    use_book_depth = "市场深度 (Market Depth)" in factors

    # Strategy settings
    st.sidebar.subheader("策略回测")
    strategy_type = st.selectbox(
        "策略类型",
        ["均值回归 (Mean Reversion)", "趋势跟踪 (Trend Following)", "突破 (Breakout)", "套利 (Arbitrage)", "自定义 (Custom)"],
        index=0
    )

# Generate tabs using option menu
selected_tab = option_menu(
    menu_title=None,
    options=["数据分析", "技术指标", "信号图谱", "策略回测", "报告导出"],
    icons=["bar-chart-line", "activity", "graph-up", "cpu", "file-pdf"],
    menu_icon="cast",
    default_index=0,
    orientation="horizontal",
    styles={
        "container": {"padding": "0!important", "background-color": "#f0f2f6"},
        "icon": {"color": "#1f3b4d", "font-size": "18px"}, 
        "nav-link": {"font-size": "16px", "text-align": "center", "margin":"0px", "--hover-color": "#eee"},
        "nav-link-selected": {"background-color": "#1f3b4d", "color": "white"},
    }
)

# Initialize database manager
db_manager = DatabaseManager()

# Function to load data from API/db
@st.cache_data(ttl=3600)
def load_data(data_sources, start_date, end_date, frequency):
    data_dict = {}
    status_messages = []
    
    if "AU Main Contract" in data_sources:
        try:
            # First try to load from the database
            db_data = db_manager.get_market_data("AU Main Contract", start_date, end_date)
            
            if not db_data.empty:
                # Found data in database
                data_dict["AU Main Contract"] = db_data
                status_messages.append(("AU Main Contract data loaded from database", "success"))
            else:
                # Fetch from API
                au_data = tushare_fetcher.fetch_au_data(start_date, end_date, frequency)
                if au_data is not None and not au_data.empty:
                    # Clean and process AU data - stitching continuous series
                    au_data = cleaner.clean_data(au_data)
                    au_data = continuous_stitcher.stitch_continuous_series(au_data)
                    data_dict["AU Main Contract"] = au_data
                    
                    # Save to database
                    db_manager.save_market_data({"AU Main Contract": au_data})
                    
                    status_messages.append(("AU Main Contract data loaded from API and saved to database", "success"))
                else:
                    status_messages.append(("Error loading AU Main Contract data", "error"))
        except Exception as e:
            status_messages.append((f"Error loading AU Main Contract data: {str(e)}", "error"))
    
    if "COMEX GC" in data_sources:
        try:
            # First try to load from the database
            db_data = db_manager.get_market_data("COMEX GC", start_date, end_date)
            
            if not db_data.empty:
                # Found data in database
                data_dict["COMEX GC"] = db_data
                status_messages.append(("COMEX GC data loaded from database", "success"))
            else:
                # Fetch from API
                gc_data = yfinance_fetcher.fetch_comex_gc(start_date, end_date, frequency)
                if gc_data is not None and not gc_data.empty:
                    gc_data = cleaner.clean_data(gc_data)
                    data_dict["COMEX GC"] = gc_data
                    
                    # Save to database
                    db_manager.save_market_data({"COMEX GC": gc_data})
                    
                    status_messages.append(("COMEX GC data loaded from API and saved to database", "success"))
                else:
                    status_messages.append(("Error loading COMEX GC data", "error"))
        except Exception as e:
            status_messages.append((f"Error loading COMEX GC data: {str(e)}", "error"))
    
    if "XAU USD" in data_sources:
        try:
            # First try to load from the database
            db_data = db_manager.get_market_data("XAU USD", start_date, end_date)
            
            if not db_data.empty:
                # Found data in database
                data_dict["XAU USD"] = db_data
                status_messages.append(("XAU USD data loaded from database", "success"))
            else:
                # Fetch from API
                xau_data = alpha_vantage.fetch_xau_usd(start_date, end_date, frequency)
                if xau_data is not None and not xau_data.empty:
                    xau_data = cleaner.clean_data(xau_data)
                    data_dict["XAU USD"] = xau_data
                    
                    # Save to database
                    db_manager.save_market_data({"XAU USD": xau_data})
                    
                    status_messages.append(("XAU USD data loaded from API and saved to database", "success"))
                else:
                    status_messages.append(("Error loading XAU USD data", "error"))
        except Exception as e:
            status_messages.append((f"Error loading XAU USD data: {str(e)}", "error"))
    
    return data_dict, status_messages

# Start data loading when button is clicked
data_sources = []
if use_tushare:
    data_sources.append("AU Main Contract")
if use_yfinance:
    data_sources.append("COMEX GC")
if use_alphavantage:
    data_sources.append("XAU USD")

# Create an attractive button for running analysis
st.sidebar.markdown("""
<style>
.run-button {
    background-color: #004e89;
    color: white;
    padding: 12px 20px;
    text-align: center;
    text-decoration: none;
    font-size: 16px;
    border-radius: 8px;
    border: none;
    cursor: pointer;
    width: 100%;
    transition: all 0.3s ease;
    margin-top: 20px;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    font-weight: bold;
}
.run-button:hover {
    background-color: #ffc745;
    color: #004e89;
    transform: translateY(-2px);
    box-shadow: 0 6px 8px rgba(0, 0, 0, 0.15);
}
</style>
""", unsafe_allow_html=True)

# Custom run button with more visibility
st.sidebar.markdown("<button class='run-button'>🚀 运行分析</button>", unsafe_allow_html=True)

# Actual button that triggers the code
if st.sidebar.button("加载数据", key="load_button", help="点击加载所选数据源的数据", use_container_width=True):
    with st.spinner("正在加载数据，请稍候..."):
        # Convert frequency to appropriate format for fetchers
        freq_map = {
            "1分钟": "1min",
            "5分钟": "5min",
            "15分钟": "15min",
            "1小时": "1h",
            "日线": "1d"
        }
        
        data_dict, status_messages = load_data(
            data_sources,
            start_date,
            end_date,
            freq_map[data_frequency]
        )
        
        # Display status messages
        for msg, status in status_messages:
            if status == "success":
                st.success(msg)
            else:
                st.error(msg)
        
        if data_dict:
            # Store data in session state for use across all tabs
            st.session_state['data'] = data_dict
            st.session_state['data_loaded'] = True
        else:
            st.error("No data could be loaded. Please check your settings and try again.")
            st.session_state['data_loaded'] = False

# Only show tabs content if data is loaded
if 'data_loaded' in st.session_state and st.session_state['data_loaded']:
    if selected_tab == "数据分析":
        st.header("数据分析")
        
        # Select data source to display
        selected_source = st.selectbox("选择数据源", list(st.session_state['data'].keys()))
        
        if selected_source:
            # Display data info
            data = st.session_state['data'][selected_source]
            st.write(f"**{selected_source} 数据**")
            st.write(f"日期范围: {data.index.min().date()} 至 {data.index.max().date()}")
            st.write(f"数据记录数: {len(data)}")
            
            # Display a sample of the data
            st.subheader("数据样本")
            st.dataframe(data.head())
            
            # Display basic statistics
            st.subheader("统计分析")
            st.dataframe(data.describe())
            
            # Plot the price data
            st.subheader("价格图表")
            fig = charts.plot_ohlc_data(data, selected_source)
            st.plotly_chart(fig, use_container_width=True)
            
            # Volume analysis
            st.subheader("成交量分析")
            vol_fig = charts.plot_volume_analysis(data, selected_source)
            st.plotly_chart(vol_fig, use_container_width=True)

    elif selected_tab == "技术指标":
        st.header("技术指标分析")
        
        # Select data source
        selected_source = st.selectbox("选择数据源", list(st.session_state['data'].keys()), key="ti_source")
        
        if selected_source:
            data = st.session_state['data'][selected_source]
            
            # Calculate selected indicators
            indicators_data = data.copy()
            
            # Create columns for indicators
            col1, col2 = st.columns(2)
            
            with col1:
                # VWAP
                if use_vwap:
                    st.subheader("成交量加权平均价格 (VWAP)")
                    indicators_data = technical.add_vwap(indicators_data)
                    vwap_fig = charts.plot_vwap(indicators_data, selected_source)
                    st.plotly_chart(vwap_fig, use_container_width=True)
                
                # MACD
                if use_macd:
                    st.subheader("指数平滑异同移动平均线 (MACD)")
                    indicators_data = technical.add_macd(indicators_data)
                    macd_fig = charts.plot_macd(indicators_data, selected_source)
                    st.plotly_chart(macd_fig, use_container_width=True)
                
                # RSI
                if use_rsi:
                    st.subheader("相对强弱指标 (RSI)")
                    indicators_data = technical.add_rsi(indicators_data)
                    rsi_fig = charts.plot_rsi(indicators_data, selected_source)
                    st.plotly_chart(rsi_fig, use_container_width=True)
            
            with col2:
                # Bollinger Bands
                if use_bollinger:
                    st.subheader("布林带 (Bollinger Bands)")
                    indicators_data = technical.add_bollinger_bands(indicators_data)
                    bb_fig = charts.plot_bollinger_bands(indicators_data, selected_source)
                    st.plotly_chart(bb_fig, use_container_width=True)
                
                # OI Delta
                if use_oi_delta:
                    st.subheader("持仓量变化 (OI Delta)")
                    if 'open_interest' in indicators_data.columns:
                        indicators_data = technical.add_oi_delta(indicators_data)
                        oi_fig = charts.plot_oi_delta(indicators_data, selected_source)
                        st.plotly_chart(oi_fig, use_container_width=True)
                    else:
                        st.warning("该数据源没有持仓量数据")
                
                # Order Flow
                if use_order_flow:
                    st.subheader("订单流 (Order Flow)")
                    try:
                        order_flow_data = orderflow.calculate_order_flow(data)
                        of_fig = charts.plot_order_flow(order_flow_data, selected_source)
                        st.plotly_chart(of_fig, use_container_width=True)
                    except Exception as e:
                        st.warning(f"无法计算订单流: {str(e)}")
            
            # Book Depth (if available)
            if use_book_depth:
                st.subheader("市场深度分析 (Market Depth)")
                try:
                    depth_data = orderflow.analyze_book_depth(data)
                    depth_fig = charts.plot_market_depth(depth_data, selected_source)
                    st.plotly_chart(depth_fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"市场深度数据不可用: {str(e)}")
            
            # Save indicators to database
            try:
                with st.spinner("正在保存指标数据到数据库..."):
                    save_result = db_manager.save_technical_indicators(selected_source, indicators_data)
                    if save_result["status"] == "success":
                        st.success("技术指标数据已保存到数据库")
                    else:
                        st.warning(f"保存技术指标数据时发生错误: {save_result['message']}")
            except Exception as e:
                st.warning(f"保存技术指标数据时发生错误: {str(e)}")

    elif selected_tab == "信号图谱":
        st.header("信号图谱分析")
        
        # Select data sources for comparison
        available_sources = list(st.session_state['data'].keys())
        
        if len(available_sources) > 1:
            sources_for_map = st.multiselect(
                "Select Data Sources for Signal Map", 
                available_sources,
                default=available_sources[:2]
            )
            
            if len(sources_for_map) >= 2:
                # Create correlation map
                st.subheader("Correlation Signal Map")
                corr_fig = signal_maps.create_correlation_map(
                    [st.session_state['data'][src] for src in sources_for_map], 
                    sources_for_map
                )
                st.plotly_chart(corr_fig, use_container_width=True)
                
                # Create heatmap of technical indicators
                st.subheader("Technical Indicator Signal Map")
                
                # Parameters for signal generation
                lookback_period = st.slider("Lookback Period (days)", 5, 30, 14)
                
                # Generate signal map
                signal_map_fig = signal_maps.create_technical_signal_map(
                    {src: st.session_state['data'][src] for src in sources_for_map},
                    lookback_period
                )
                st.plotly_chart(signal_map_fig, use_container_width=True)
                
                # Create divergence map
                st.subheader("Divergence Map")
                divergence_fig = signal_maps.create_divergence_map(
                    {src: st.session_state['data'][src] for src in sources_for_map}
                )
                st.plotly_chart(divergence_fig, use_container_width=True)
            else:
                st.info("Please select at least 2 data sources for comparison")
        else:
            st.info("Signal maps require at least 2 data sources. Please load more data.")

    elif selected_tab == "策略回测":
        st.header("策略回测")
        
        # Strategy configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Strategy Configuration")
            
            # Select data source
            strategy_data_source = st.selectbox(
                "Select Data Source for Testing",
                list(st.session_state['data'].keys()),
                key="strat_data_source"
            )
            
            # Strategy parameters
            if strategy_type == "Mean Reversion":
                lookback = st.slider("Lookback Period", 5, 50, 20)
                std_dev = st.slider("Standard Deviation Threshold", 1.0, 3.0, 2.0, 0.1)
                exit_threshold = st.slider("Exit Threshold", 0.0, 1.0, 0.5, 0.1)
                
                strategy_params = {
                    "type": strategy_type,
                    "lookback": lookback,
                    "std_dev": std_dev,
                    "exit_threshold": exit_threshold
                }
                
            elif strategy_type == "Trend Following":
                fast_period = st.slider("Fast MA Period", 5, 50, 10)
                slow_period = st.slider("Slow MA Period", 10, 200, 50)
                
                strategy_params = {
                    "type": strategy_type,
                    "fast_period": fast_period,
                    "slow_period": slow_period
                }
                
            elif strategy_type == "Breakout":
                channel_period = st.slider("Channel Period", 10, 100, 20)
                atr_multiplier = st.slider("ATR Multiplier", 0.5, 5.0, 2.0, 0.1)
                
                strategy_params = {
                    "type": strategy_type,
                    "channel_period": channel_period,
                    "atr_multiplier": atr_multiplier
                }
                
            elif strategy_type == "Arbitrage":
                sec_data_source = st.selectbox(
                    "Select Second Data Source",
                    [src for src in list(st.session_state['data'].keys()) if src != strategy_data_source],
                    key="sec_data_source"
                )
                z_score_threshold = st.slider("Z-Score Threshold", 1.0, 3.0, 2.0, 0.1)
                
                strategy_params = {
                    "type": strategy_type,
                    "primary_source": strategy_data_source,
                    "secondary_source": sec_data_source,
                    "z_score_threshold": z_score_threshold
                }
                
            elif strategy_type == "Custom":
                indicator_choice = st.multiselect(
                    "Select Indicators for Strategy",
                    ["VWAP", "MACD", "RSI", "Bollinger Bands", "OI Delta"],
                    default=["MACD", "RSI"]
                )
                
                # Custom parameters based on selected indicators
                custom_params = {}
                if "MACD" in indicator_choice:
                    custom_params["macd_fast"] = st.slider("MACD Fast Period", 5, 20, 12)
                    custom_params["macd_slow"] = st.slider("MACD Slow Period", 20, 40, 26)
                    custom_params["macd_signal"] = st.slider("MACD Signal Period", 5, 15, 9)
                
                if "RSI" in indicator_choice:
                    custom_params["rsi_period"] = st.slider("RSI Period", 5, 30, 14)
                    custom_params["rsi_overbought"] = st.slider("RSI Overbought Level", 70, 90, 70)
                    custom_params["rsi_oversold"] = st.slider("RSI Oversold Level", 10, 30, 30)
                
                strategy_params = {
                    "type": strategy_type,
                    "indicators": indicator_choice,
                    "params": custom_params
                }
            
            # Backtesting parameters
            st.subheader("Backtesting Parameters")
            initial_capital = st.number_input("Initial Capital", min_value=1000, value=10000)
            position_size = st.slider("Position Size (%)", 1, 100, 10)
            commission_pct = st.number_input("Commission (%)", min_value=0.0, max_value=1.0, value=0.1, step=0.01)
            
            backtest_params = {
                "initial_capital": initial_capital,
                "position_size_pct": position_size,
                "commission_pct": commission_pct
            }
            
            # Run backtest button
            if st.button("Run Backtest"):
                with st.spinner("Running backtest..."):
                    if strategy_type != "Arbitrage":
                        # Single-asset strategy
                        strategy_data = st.session_state['data'][strategy_data_source]
                        
                        # Create and run strategy
                        strat = strategy.create_strategy(strategy_data, strategy_params)
                        backtest_results = evaluator.run_backtest(strat, strategy_data, backtest_params)
                        
                        # Store results in session state
                        st.session_state['backtest_results'] = backtest_results
                        st.session_state['backtest_complete'] = True
                    else:
                        # Arbitrage strategy between two assets
                        primary_data = st.session_state['data'][strategy_data_source]
                        secondary_data = st.session_state['data'][strategy_params["secondary_source"]]
                        
                        # Create and run arbitrage strategy
                        strat = strategy.create_arbitrage_strategy(
                            primary_data, 
                            secondary_data, 
                            strategy_params
                        )
                        backtest_results = evaluator.run_arbitrage_backtest(
                            strat, 
                            primary_data,
                            secondary_data,
                            backtest_params
                        )
                        
                        # Store results in session state
                        st.session_state['backtest_results'] = backtest_results
                        st.session_state['backtest_complete'] = True
        
        with col2:
            st.subheader("Backtesting Results")
            
            # Display results if available
            if 'backtest_complete' in st.session_state and st.session_state['backtest_complete']:
                results = st.session_state['backtest_results']
                
                # Display performance metrics
                st.write("**Performance Metrics**")
                metrics_df = pd.DataFrame(results['metrics'], index=[0])
                st.dataframe(metrics_df)
                
                # Plot equity curve
                st.write("**Equity Curve**")
                equity_fig = charts.plot_equity_curve(results['equity_curve'])
                st.plotly_chart(equity_fig, use_container_width=True)
                
                # Plot drawdowns
                st.write("**Drawdowns**")
                drawdown_fig = charts.plot_drawdowns(results['drawdowns'])
                st.plotly_chart(drawdown_fig, use_container_width=True)
                
                # Plot trade distribution
                st.write("**Trade Distribution**")
                trades_fig = charts.plot_trade_distribution(results['trades'])
                st.plotly_chart(trades_fig, use_container_width=True)
                
                # Strategy code
                st.write("**Strategy Pseudocode**")
                strategy_code = results.get('strategy_code', "No strategy code available")
                st.code(strategy_code, language='python')
            else:
                st.info("Run a backtest to see results")

    elif selected_tab == "报告导出":
        st.header("报告导出")
        
        # Report generation options
        report_type = st.radio("报告类型", ["HTML", "PDF"])
        
        # Select data sources to include
        report_data_sources = st.multiselect(
            "Select Data Sources for Report",
            list(st.session_state['data'].keys()),
            default=list(st.session_state['data'].keys())
        )
        
        # Select sections to include in report
        report_sections = st.multiselect(
            "Select Sections to Include",
            ["Market Overview", "Technical Analysis", "Signal Map", "Strategy Backtest", "Conclusions"],
            default=["Market Overview", "Technical Analysis", "Strategy Backtest"]
        )
        
        # Report header info
        st.subheader("Report Header Information")
        report_title = st.text_input("Report Title", "Gold Market Analysis Report")
        report_author = st.text_input("Author", "Financial Analyst")
        report_date = st.date_input("Report Date", datetime.datetime.now().date())
        
        # Generate report button
        if st.button("Generate Report"):
            if report_data_sources:
                with st.spinner("Generating report..."):
                    # Collect data for report
                    report_data = {
                        src: st.session_state['data'][src] for src in report_data_sources 
                        if src in st.session_state['data']
                    }
                    
                    # Report metadata
                    report_meta = {
                        "title": report_title,
                        "author": report_author,
                        "date": report_date.strftime("%Y-%m-%d"),
                        "sections": report_sections
                    }
                    
                    # Get backtest results if available
                    backtest_results = st.session_state.get('backtest_results', None)
                    
                    # Generate HTML report
                    html_content = html_generator.generate_report(
                        report_data, 
                        report_meta, 
                        backtest_results
                    )
                    
                    # If PDF is selected, convert HTML to PDF
                    if report_type == "PDF":
                        try:
                            pdf_path = pdf_exporter.html_to_pdf(html_content, report_title)
                            
                            # Provide download link
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="Download PDF Report",
                                data=pdf_bytes,
                                file_name=f"{report_title.replace(' ', '_')}.pdf",
                                mime="application/pdf"
                            )
                        except Exception as e:
                            st.error(f"Error generating PDF: {str(e)}")
                            st.info("Falling back to HTML report")
                            st.components.v1.html(html_content, height=600)
                    else:
                        # Display HTML report
                        st.components.v1.html(html_content, height=600)
                        
                        # Provide download option for HTML
                        st.download_button(
                            label="Download HTML Report",
                            data=html_content,
                            file_name=f"{report_title.replace(' ', '_')}.html",
                            mime="text/html"
                        )
            else:
                st.error("Please select at least one data source for the report")
else:
    # Show placeholder when no data is loaded
    st.markdown("""
    <div style="text-align: center; padding: 40px; background-color: #f8f9fa; border-radius: 10px; margin: 30px;">
        <h2 style="color: #1f3b4d;">黄金市场 MCP 智能分析系统</h2>
        <p style="font-size: 18px;">请使用左侧控制面板选择数据源和时间范围，然后点击"加载数据"按钮开始分析。</p>
        <p style="font-size: 16px;">系统将对黄金市场进行全面分析，包括技术指标、市场特征与仓位因子（MCP）、信号图谱和策略回测。</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display sample charts
    st.markdown("### 系统功能展示")
    cols = st.columns(3)
    with cols[0]:
        st.markdown("**技术指标分析**")
        st.image("https://miro.medium.com/max/1400/1*3a4RYwUm1nN4NdPNS1WrTA.png", use_column_width=True)
    with cols[1]:
        st.markdown("**信号图谱**")
        st.image("https://www.researchgate.net/publication/329962620/figure/fig2/AS:705181092614144@1545149549518/Heatmap-of-the-correlations-between-the-attributes-in-the-data-set.png", use_column_width=True)
    with cols[2]:
        st.markdown("**策略回测**")
        st.image("https://www.tradingview.com/x/wKjvBtut/", use_column_width=True)

# Add footer
st.markdown("""
<style>
.footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: #f0f2f6;
    color: #1f3b4d;
    text-align: center;
    padding: 10px;
    font-size: 12px;
    border-top: 1px solid #ddd;
}
</style>
<div class="footer">
    © 2025 黄金市场 MCP 智能分析系统 | 版本 1.0.0 | 数据来源: Tushare, Yahoo Finance, Alpha Vantage
</div>
""", unsafe_allow_html=True)
