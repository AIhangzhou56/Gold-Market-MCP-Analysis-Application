import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional, Union

def run_backtest(strategy_df: pd.DataFrame, price_data: pd.DataFrame, backtest_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a backtest on a strategy
    
    Parameters:
    -----------
    strategy_df : pandas.DataFrame
        DataFrame with strategy signals and positions
    price_data : pandas.DataFrame
        DataFrame with price data
    backtest_params : dict
        Dictionary with backtest parameters
        
    Returns:
    --------
    dict
        Dictionary with backtest results
    """
    # Extract parameters
    initial_capital = backtest_params.get('initial_capital', 10000)
    position_size_pct = backtest_params.get('position_size_pct', 100) / 100
    commission_pct = backtest_params.get('commission_pct', 0.1) / 100
    
    # Merge dataframes if necessary
    if strategy_df is not price_data:
        strategy_df = strategy_df.copy()
    else:
        strategy_df = price_data.copy()
    
    # Ensure we have position data
    if 'Position' not in strategy_df.columns:
        raise ValueError("Strategy DataFrame must contain 'Position' column")
    
    # Create a new DataFrame for backtest results
    results = strategy_df.copy()
    
    # Calculate position changes
    results['PositionChange'] = results['Position'].diff()
    
    # Calculate entry and exit prices
    results['EntryPrice'] = np.nan
    results['ExitPrice'] = np.nan
    
    results.loc[results['PositionChange'] != 0, 'EntryPrice'] = results['Close']
    results.loc[results['PositionChange'] != 0, 'ExitPrice'] = results['Close'].shift(-1)
    
    # Fill forward entry prices
    results['EntryPrice'] = results['EntryPrice'].fillna(method='ffill')
    
    # Calculate position size in units
    capital_per_trade = initial_capital * position_size_pct
    results['PositionSize'] = capital_per_trade / results['EntryPrice']
    
    # Calculate trade returns
    results['TradeReturn'] = 0.0
    
    # For long positions
    long_mask = (results['Position'] > 0)
    results.loc[long_mask, 'TradeReturn'] = (results['Close'] / results['EntryPrice'] - 1) * results['Position']
    
    # For short positions
    short_mask = (results['Position'] < 0)
    results.loc[short_mask, 'TradeReturn'] = (results['EntryPrice'] / results['Close'] - 1) * abs(results['Position'])
    
    # Apply commission costs
    trade_mask = (results['PositionChange'] != 0)
    results.loc[trade_mask, 'TradeReturn'] = results.loc[trade_mask, 'TradeReturn'] - commission_pct
    
    # Calculate equity curve
    results['Equity'] = (1 + results['TradeReturn']).cumprod() * initial_capital
    
    # Calculate drawdowns
    results['Peak'] = results['Equity'].cummax()
    results['Drawdown'] = (results['Equity'] - results['Peak']) / results['Peak']
    
    # Extract trade list
    trades = extract_trades(results)
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(results, trades, initial_capital)
    
    # Get strategy pseudocode
    strategy_code = strategy_df.attrs.get('strategy_code', "No strategy code available")
    
    # Compile results
    backtest_results = {
        'equity_curve': results['Equity'],
        'trades': trades,
        'drawdowns': results['Drawdown'],
        'metrics': metrics,
        'strategy_code': strategy_code
    }
    
    return backtest_results

def run_arbitrage_backtest(strategy_df: pd.DataFrame, primary_data: pd.DataFrame, 
                          secondary_data: pd.DataFrame, backtest_params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run a backtest on an arbitrage strategy
    
    Parameters:
    -----------
    strategy_df : pandas.DataFrame
        DataFrame with strategy signals and positions
    primary_data : pandas.DataFrame
        DataFrame with price data for primary asset
    secondary_data : pandas.DataFrame
        DataFrame with price data for secondary asset
    backtest_params : dict
        Dictionary with backtest parameters
        
    Returns:
    --------
    dict
        Dictionary with backtest results
    """
    # Extract parameters
    initial_capital = backtest_params.get('initial_capital', 10000)
    position_size_pct = backtest_params.get('position_size_pct', 100) / 100
    commission_pct = backtest_params.get('commission_pct', 0.1) / 100
    
    # Create a copy to avoid modifying the original
    results = strategy_df.copy()
    
    # Ensure we have position data
    if 'Position' not in results.columns:
        raise ValueError("Strategy DataFrame must contain 'Position' column")
    
    # Create a common index for all datasets
    common_idx = results.index.intersection(primary_data.index).intersection(secondary_data.index)
    results = results.loc[common_idx].copy()
    primary = primary_data.loc[common_idx].copy()
    secondary = secondary_data.loc[common_idx].copy()
    
    # Add secondary close price to results
    results['PrimaryClose'] = primary['Close']
    results['SecondaryClose'] = secondary['Close']
    
    # Calculate position changes
    results['PositionChange'] = results['Position'].diff()
    
    # Calculate entry and exit prices
    results['PrimaryEntryPrice'] = np.nan
    results['PrimaryExitPrice'] = np.nan
    results['SecondaryEntryPrice'] = np.nan
    results['SecondaryExitPrice'] = np.nan
    
    # Set entry prices at position changes
    entry_mask = results['PositionChange'] != 0
    results.loc[entry_mask, 'PrimaryEntryPrice'] = results.loc[entry_mask, 'PrimaryClose']
    results.loc[entry_mask, 'SecondaryEntryPrice'] = results.loc[entry_mask, 'SecondaryClose']
    
    # Fill forward entry prices
    results['PrimaryEntryPrice'] = results['PrimaryEntryPrice'].fillna(method='ffill')
    results['SecondaryEntryPrice'] = results['SecondaryEntryPrice'].fillna(method='ffill')
    
    # Calculate position size (equal dollar value for both assets)
    capital_per_trade = initial_capital * position_size_pct / 2  # Split between two assets
    results['PrimarySize'] = capital_per_trade / results['PrimaryEntryPrice']
    results['SecondarySize'] = capital_per_trade / results['SecondaryEntryPrice']
    
    # Calculate trade returns
    results['PrimaryReturn'] = 0.0
    results['SecondaryReturn'] = 0.0
    
    # For long primary positions (short spread)
    long_primary_mask = results['Position'] > 0
    results.loc[long_primary_mask, 'PrimaryReturn'] = (results['PrimaryClose'] / results['PrimaryEntryPrice'] - 1) * results['Position']
    
    # For short primary positions (long spread)
    short_primary_mask = results['Position'] < 0
    results.loc[short_primary_mask, 'PrimaryReturn'] = (results['PrimaryEntryPrice'] / results['PrimaryClose'] - 1) * abs(results['Position'])
    
    # For secondary, the position is opposite to primary
    results.loc[long_primary_mask, 'SecondaryReturn'] = (results['SecondaryEntryPrice'] / results['SecondaryClose'] - 1) * results['Position']
    results.loc[short_primary_mask, 'SecondaryReturn'] = (results['SecondaryClose'] / results['SecondaryEntryPrice'] - 1) * abs(results['Position'])
    
    # Apply commission costs
    trade_mask = results['PositionChange'] != 0
    results.loc[trade_mask, 'PrimaryReturn'] = results.loc[trade_mask, 'PrimaryReturn'] - commission_pct
    results.loc[trade_mask, 'SecondaryReturn'] = results.loc[trade_mask, 'SecondaryReturn'] - commission_pct
    
    # Calculate total return
    results['TradeReturn'] = results['PrimaryReturn'] + results['SecondaryReturn']
    
    # Calculate equity curve
    results['Equity'] = (1 + results['TradeReturn']).cumprod() * initial_capital
    
    # Calculate drawdowns
    results['Peak'] = results['Equity'].cummax()
    results['Drawdown'] = (results['Equity'] - results['Peak']) / results['Peak']
    
    # Extract trade list
    trades = extract_arbitrage_trades(results)
    
    # Calculate performance metrics
    metrics = calculate_performance_metrics(results, trades, initial_capital)
    
    # Get strategy pseudocode
    strategy_code = strategy_df.attrs.get('strategy_code', "No strategy code available")
    
    # Compile results
    backtest_results = {
        'equity_curve': results['Equity'],
        'trades': trades,
        'drawdowns': results['Drawdown'],
        'metrics': metrics,
        'strategy_code': strategy_code
    }
    
    return backtest_results

def extract_trades(results: pd.DataFrame) -> pd.DataFrame:
    """
    Extract individual trades from backtest results
    
    Parameters:
    -----------
    results : pandas.DataFrame
        DataFrame with backtest results
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with individual trades
    """
    # Find position changes
    position_changes = results['PositionChange'] != 0
    
    # Create a list to store trades
    trade_list = []
    
    # Iterate through position changes
    position_idx = position_changes[position_changes].index
    
    for i in range(len(position_idx) - 1):
        current_idx = position_idx[i]
        next_idx = position_idx[i + 1]
        
        position = results.loc[current_idx, 'Position']
        
        # Skip if the position is zero (exiting a position)
        if position == 0:
            continue
        
        # Extract trade information
        entry_price = results.loc[current_idx, 'Close']
        exit_price = results.loc[next_idx, 'Close']
        entry_date = current_idx
        exit_date = next_idx
        
        # Calculate trade return
        if position > 0:  # Long trade
            trade_return = exit_price / entry_price - 1
        else:  # Short trade
            trade_return = entry_price / exit_price - 1
        
        # Apply commission
        commission = results.loc[current_idx, 'TradeReturn'] - ((exit_price / entry_price - 1) if position > 0 else (entry_price / exit_price - 1))
        
        trade_list.append({
            'entry_date': entry_date,
            'exit_date': exit_date,
            'position': position,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'return': trade_return,
            'commission': abs(commission)
        })
    
    # Create DataFrame from trade list
    if trade_list:
        trades_df = pd.DataFrame(trade_list)
        trades_df['duration'] = (trades_df['exit_date'] - trades_df['entry_date']).dt.total_seconds() / (60 * 60 * 24)  # Duration in days
        return trades_df
    else:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['entry_date', 'exit_date', 'position', 'entry_price', 'exit_price', 'return', 'commission', 'duration'])

def extract_arbitrage_trades(results: pd.DataFrame) -> pd.DataFrame:
    """
    Extract individual arbitrage trades from backtest results
    
    Parameters:
    -----------
    results : pandas.DataFrame
        DataFrame with backtest results
        
    Returns:
    --------
    pandas.DataFrame
        DataFrame with individual trades
    """
    # Find position changes
    position_changes = results['PositionChange'] != 0
    
    # Create a list to store trades
    trade_list = []
    
    # Iterate through position changes
    position_idx = position_changes[position_changes].index
    
    for i in range(len(position_idx) - 1):
        current_idx = position_idx[i]
        next_idx = position_idx[i + 1]
        
        position = results.loc[current_idx, 'Position']
        
        # Skip if the position is zero (exiting a position)
        if position == 0:
            continue
        
        # Extract trade information
        entry_date = current_idx
        exit_date = next_idx
        primary_entry = results.loc[current_idx, 'PrimaryClose']
        primary_exit = results.loc[next_idx, 'PrimaryClose']
        secondary_entry = results.loc[current_idx, 'SecondaryClose']
        secondary_exit = results.loc[next_idx, 'SecondaryClose']
        
        # Calculate spread at entry and exit
        spread_entry = primary_entry - secondary_entry
        spread_exit = primary_exit - secondary_exit
        
        # Calculate trade return
        primary_return = results.loc[next_idx, 'PrimaryReturn']
        secondary_return = results.loc[next_idx, 'SecondaryReturn']
        total_return = primary_return + secondary_return
        
        trade_list.append({
            'entry_date': entry_date,
            'exit_date': exit_date,
            'position': position,
            'primary_entry': primary_entry,
            'primary_exit': primary_exit,
            'secondary_entry': secondary_entry,
            'secondary_exit': secondary_exit,
            'spread_entry': spread_entry,
            'spread_exit': spread_exit,
            'primary_return': primary_return,
            'secondary_return': secondary_return,
            'return': total_return
        })
    
    # Create DataFrame from trade list
    if trade_list:
        trades_df = pd.DataFrame(trade_list)
        trades_df['duration'] = (trades_df['exit_date'] - trades_df['entry_date']).dt.total_seconds() / (60 * 60 * 24)  # Duration in days
        return trades_df
    else:
        # Return empty DataFrame with expected columns
        return pd.DataFrame(columns=['entry_date', 'exit_date', 'position', 'primary_entry', 'primary_exit', 
                                     'secondary_entry', 'secondary_exit', 'spread_entry', 'spread_exit',
                                     'primary_return', 'secondary_return', 'return', 'duration'])

def calculate_performance_metrics(results: pd.DataFrame, trades: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
    """
    Calculate performance metrics for a backtest
    
    Parameters:
    -----------
    results : pandas.DataFrame
        DataFrame with backtest results
    trades : pandas.DataFrame
        DataFrame with individual trades
    initial_capital : float
        Initial capital for the backtest
        
    Returns:
    --------
    dict
        Dictionary with performance metrics
    """
    # Extract equity curve and returns
    equity = results['Equity']
    returns = results['TradeReturn']
    
    # Basic performance metrics
    total_return = (equity.iloc[-1] / initial_capital - 1) * 100
    
    # Calculate annualized return
    days = (results.index[-1] - results.index[0]).days
    years = days / 365
    annualized_return = ((1 + total_return / 100) ** (1 / max(years, 1e-10)) - 1) * 100
    
    # Calculate Sharpe ratio (assuming risk-free rate of 0)
    daily_returns = results['TradeReturn'][results['TradeReturn'] != 0]
    if len(daily_returns) > 1:
        sharpe_ratio = np.sqrt(252) * daily_returns.mean() / daily_returns.std()
    else:
        sharpe_ratio = 0
    
    # Calculate maximum drawdown
    max_drawdown = results['Drawdown'].min() * 100
    
    # Calculate win rate
    if len(trades) > 0:
        win_rate = (trades['return'] > 0).mean() * 100
        avg_win = trades.loc[trades['return'] > 0, 'return'].mean() * 100 if (trades['return'] > 0).any() else 0
        avg_loss = trades.loc[trades['return'] < 0, 'return'].mean() * 100 if (trades['return'] < 0).any() else 0
        profit_factor = abs(trades.loc[trades['return'] > 0, 'return'].sum() / trades.loc[trades['return'] < 0, 'return'].sum()) if (trades['return'] < 0).any() else float('inf')
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
    
    # Compile metrics
    metrics = {
        'total_return': float(round(total_return, 2)),
        'annualized_return': float(round(annualized_return, 2)),
        'sharpe_ratio': float(round(sharpe_ratio, 2)),
        'max_drawdown': float(round(max_drawdown, 2)),
        'win_rate': float(round(win_rate, 2)),
        'avg_win': float(round(avg_win, 2)),
        'avg_loss': float(round(avg_loss, 2)),
        'profit_factor': float(round(profit_factor, 2)),
        'num_trades': len(trades),
        'avg_trade_duration': float(round(trades['duration'].mean(), 2)) if len(trades) > 0 else 0
    }
    
    return metrics
