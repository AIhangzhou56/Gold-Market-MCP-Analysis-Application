"""
Database manager for the MCP Intelligent Analysis System.
"""
import pandas as pd
import json
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
import numpy as np

from database.models import (
    Session as DatabaseSession,
    MarketData,
    TechnicalIndicator,
    Strategy,
    BacktestResult,
    Trade,
    UserSavedReport,
    create_tables
)

class DatabaseManager:
    """Database manager for handling database operations."""
    
    def __init__(self):
        """Initialize the database manager."""
        # Create tables if they don't exist
        create_tables()
        
    def save_market_data(self, data_dict):
        """
        Save market data to the database.
        
        Parameters:
        -----------
        data_dict : dict
            Dictionary of DataFrames with keys as data sources
            
        Returns:
        --------
        dict
            Dictionary with status messages for each data source
        """
        status_messages = {}
        session = DatabaseSession()
        
        try:
            for source, df in data_dict.items():
                # Convert DataFrame to list of MarketData objects
                records = []
                for index, row in df.iterrows():
                    market_data = MarketData(
                        source=source,
                        symbol=source,  # Use source as symbol for now
                        timestamp=index,
                        open=row['open'],
                        high=row['high'],
                        low=row['low'],
                        close=row['close'],
                        volume=row.get('volume', 0),
                        open_interest=row.get('open_interest', 0)
                    )
                    records.append(market_data)
                
                # Bulk insert records
                session.bulk_save_objects(records)
                status_messages[source] = {"status": "success", "message": f"Saved {len(records)} records for {source}"}
            
            session.commit()
        except Exception as e:
            session.rollback()
            status_messages["error"] = {"status": "error", "message": str(e)}
        finally:
            session.close()
            
        return status_messages
    
    def save_technical_indicators(self, source, data_df):
        """
        Save technical indicators to the database.
        
        Parameters:
        -----------
        source : str
            Data source name
        data_df : pandas.DataFrame
            DataFrame with technical indicators
            
        Returns:
        --------
        dict
            Status message
        """
        session = DatabaseSession()
        status = {"status": "success", "message": ""}
        
        try:
            # Get all market data for the source
            market_data_records = session.query(MarketData).filter(
                MarketData.source == source
            ).all()
            
            # Create a dictionary of timestamps to MarketData objects
            market_data_dict = {record.timestamp: record for record in market_data_records}
            
            # Define indicator columns
            indicator_columns = {
                "vwap": {"type": "VWAP", "value": "vwap"},
                "macd": {"type": "MACD", "value": "macd", "secondary": "macd_signal", "tertiary": "macd_hist"},
                "rsi": {"type": "RSI", "value": "rsi"},
                "bbands_upper": {"type": "Bollinger_Upper", "value": "bbands_upper"},
                "bbands_middle": {"type": "Bollinger_Middle", "value": "bbands_middle"},
                "bbands_lower": {"type": "Bollinger_Lower", "value": "bbands_lower"},
                "oi_delta": {"type": "OI_Delta", "value": "oi_delta"}
            }
            
            # Convert DataFrame to list of TechnicalIndicator objects
            records = []
            for index, row in data_df.iterrows():
                # If the timestamp exists in market_data_dict
                if index in market_data_dict:
                    market_data = market_data_dict[index]
                    
                    # Add each indicator if it exists in the DataFrame
                    for col, config in indicator_columns.items():
                        if config["value"] in row.index:
                            # Create TechnicalIndicator record
                            indicator = TechnicalIndicator(
                                market_data_id=market_data.id,
                                indicator_type=config["type"],
                                value=row[config["value"]],
                                secondary_value=row.get(config.get("secondary", ""), None),
                                tertiary_value=row.get(config.get("tertiary", ""), None)
                            )
                            records.append(indicator)
            
            # Bulk insert records
            session.bulk_save_objects(records)
            session.commit()
            status["message"] = f"Saved {len(records)} indicator records for {source}"
        except Exception as e:
            session.rollback()
            status = {"status": "error", "message": str(e)}
        finally:
            session.close()
            
        return status
    
    def get_market_data(self, source, start_date=None, end_date=None):
        """
        Get market data from the database.
        
        Parameters:
        -----------
        source : str
            Data source name
        start_date : datetime.date
            Start date for filtering data
        end_date : datetime.date
            End date for filtering data
            
        Returns:
        --------
        pandas.DataFrame
            DataFrame with market data
        """
        session = DatabaseSession()
        
        try:
            # Build query
            query = session.query(MarketData).filter(MarketData.source == source)
            
            # Add date filters if provided
            if start_date:
                query = query.filter(MarketData.timestamp >= start_date)
            if end_date:
                query = query.filter(MarketData.timestamp <= end_date)
            
            # Execute query and order by timestamp
            records = query.order_by(MarketData.timestamp).all()
            
            # Convert to DataFrame
            if records:
                data = {
                    "open": [record.open for record in records],
                    "high": [record.high for record in records],
                    "low": [record.low for record in records],
                    "close": [record.close for record in records],
                    "volume": [record.volume for record in records],
                    "open_interest": [record.open_interest for record in records]
                }
                
                df = pd.DataFrame(data, index=[record.timestamp for record in records])
                return df
            else:
                return pd.DataFrame()
        finally:
            session.close()
    
    def save_strategy(self, name, description, strategy_type, parameters):
        """
        Save a strategy to the database.
        
        Parameters:
        -----------
        name : str
            Strategy name
        description : str
            Strategy description
        strategy_type : str
            Strategy type (Mean Reversion, Trend Following, etc.)
        parameters : dict
            Strategy parameters
            
        Returns:
        --------
        int
            ID of the created strategy
        """
        session = DatabaseSession()
        
        try:
            # Convert parameters to JSON string
            params_json = json.dumps(parameters)
            
            # Create Strategy record
            strategy = Strategy(
                name=name,
                description=description,
                strategy_type=strategy_type,
                parameters=params_json
            )
            
            session.add(strategy)
            session.commit()
            
            return strategy.id
        finally:
            session.close()
    
    def save_backtest_result(self, strategy_id, result_data, trades_data):
        """
        Save backtest results to the database.
        
        Parameters:
        -----------
        strategy_id : int
            ID of the strategy
        result_data : dict
            Backtest result data
        trades_data : pandas.DataFrame
            DataFrame with trades data
            
        Returns:
        --------
        dict
            Status message
        """
        session = DatabaseSession()
        status = {"status": "success", "message": ""}
        
        try:
            # Create BacktestResult record
            backtest_result = BacktestResult(
                strategy_id=strategy_id,
                start_date=result_data["start_date"],
                end_date=result_data["end_date"],
                initial_capital=result_data["initial_capital"],
                final_capital=result_data["final_capital"],
                total_return=result_data["total_return"],
                annualized_return=result_data.get("annualized_return", 0),
                sharpe_ratio=result_data.get("sharpe_ratio", 0),
                max_drawdown=result_data.get("max_drawdown", 0),
                win_rate=result_data.get("win_rate", 0),
                profit_factor=result_data.get("profit_factor", 0),
                total_trades=result_data.get("total_trades", 0)
            )
            
            session.add(backtest_result)
            session.flush()  # Get the ID of the backtest result
            
            # Create Trade records
            if not trades_data.empty:
                trade_records = []
                for _, row in trades_data.iterrows():
                    trade = Trade(
                        backtest_result_id=backtest_result.id,
                        entry_date=row["entry_date"],
                        exit_date=row.get("exit_date", None),
                        entry_price=row["entry_price"],
                        exit_price=row.get("exit_price", None),
                        quantity=row["quantity"],
                        profit_loss=row.get("profit_loss", 0),
                        is_long=row.get("is_long", True),
                        is_closed=row.get("is_closed", True)
                    )
                    trade_records.append(trade)
                
                session.bulk_save_objects(trade_records)
            
            session.commit()
            status["message"] = f"Saved backtest result with ID {backtest_result.id}"
            status["backtest_id"] = backtest_result.id
        except Exception as e:
            session.rollback()
            status = {"status": "error", "message": str(e)}
        finally:
            session.close()
            
        return status
    
    def save_report(self, title, description, report_type, file_path):
        """
        Save a report to the database.
        
        Parameters:
        -----------
        title : str
            Report title
        description : str
            Report description
        report_type : str
            Report type (HTML, PDF)
        file_path : str
            Path to the report file
            
        Returns:
        --------
        dict
            Status message
        """
        session = DatabaseSession()
        status = {"status": "success", "message": ""}
        
        try:
            # Create UserSavedReport record
            report = UserSavedReport(
                title=title,
                description=description,
                report_type=report_type,
                file_path=file_path
            )
            
            session.add(report)
            session.commit()
            
            status["message"] = f"Saved report with ID {report.id}"
            status["report_id"] = report.id
        except Exception as e:
            session.rollback()
            status = {"status": "error", "message": str(e)}
        finally:
            session.close()
            
        return status
    
    def get_saved_reports(self):
        """
        Get all saved reports from the database.
        
        Returns:
        --------
        list
            List of saved reports
        """
        session = DatabaseSession()
        
        try:
            reports = session.query(UserSavedReport).order_by(desc(UserSavedReport.created_at)).all()
            
            return [
                {
                    "id": report.id,
                    "title": report.title,
                    "description": report.description,
                    "report_type": report.report_type,
                    "file_path": report.file_path,
                    "created_at": report.created_at
                }
                for report in reports
            ]
        finally:
            session.close()
    
    def get_strategies(self):
        """
        Get all strategies from the database.
        
        Returns:
        --------
        list
            List of strategies
        """
        session = DatabaseSession()
        
        try:
            strategies = session.query(Strategy).order_by(desc(Strategy.created_at)).all()
            
            return [
                {
                    "id": strategy.id,
                    "name": strategy.name,
                    "description": strategy.description,
                    "strategy_type": strategy.strategy_type,
                    "parameters": json.loads(strategy.parameters),
                    "created_at": strategy.created_at
                }
                for strategy in strategies
            ]
        finally:
            session.close()
    
    def get_backtest_results(self, strategy_id=None):
        """
        Get backtest results from the database.
        
        Parameters:
        -----------
        strategy_id : int, optional
            ID of the strategy to filter results
            
        Returns:
        --------
        list
            List of backtest results
        """
        session = DatabaseSession()
        
        try:
            query = session.query(BacktestResult)
            
            if strategy_id:
                query = query.filter(BacktestResult.strategy_id == strategy_id)
            
            results = query.order_by(desc(BacktestResult.created_at)).all()
            
            return [
                {
                    "id": result.id,
                    "strategy_id": result.strategy_id,
                    "start_date": result.start_date,
                    "end_date": result.end_date,
                    "initial_capital": result.initial_capital,
                    "final_capital": result.final_capital,
                    "total_return": result.total_return,
                    "annualized_return": result.annualized_return,
                    "sharpe_ratio": result.sharpe_ratio,
                    "max_drawdown": result.max_drawdown,
                    "win_rate": result.win_rate,
                    "profit_factor": result.profit_factor,
                    "total_trades": result.total_trades,
                    "created_at": result.created_at
                }
                for result in results
            ]
        finally:
            session.close()