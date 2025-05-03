"""
Database models for the MCP Intelligent Analysis System.
"""
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os
import datetime

# Get the database URL from the environment variables
DATABASE_URL = os.environ.get('DATABASE_URL')

# Create the SQLAlchemy engine
engine = create_engine(DATABASE_URL)

# Create a sessionmaker
Session = sessionmaker(bind=engine)

# Create a base class for declarative class definitions
Base = declarative_base()

class MarketData(Base):
    """Market data model for storing OHLCV data."""
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    source = Column(String, nullable=False)  # AU Main Contract, COMEX GC, XAU USD
    symbol = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float)
    open_interest = Column(Float)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with technical indicators
    indicators = relationship("TechnicalIndicator", back_populates="market_data", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<MarketData(source='{self.source}', symbol='{self.symbol}', timestamp='{self.timestamp}')>"

class TechnicalIndicator(Base):
    """Technical indicator model for storing indicator values."""
    __tablename__ = 'technical_indicators'
    
    id = Column(Integer, primary_key=True)
    market_data_id = Column(Integer, ForeignKey('market_data.id'), nullable=False)
    indicator_type = Column(String, nullable=False)  # VWAP, MACD, RSI, etc.
    value = Column(Float)
    secondary_value = Column(Float)  # For indicators with multiple values like MACD
    tertiary_value = Column(Float)  # For indicators with multiple values
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with market data
    market_data = relationship("MarketData", back_populates="indicators")
    
    def __repr__(self):
        return f"<TechnicalIndicator(type='{self.indicator_type}', value={self.value})>"

class Strategy(Base):
    """Strategy model for storing strategy configurations."""
    __tablename__ = 'strategies'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    strategy_type = Column(String, nullable=False)  # Mean Reversion, Trend Following, etc.
    parameters = Column(String)  # JSON string of parameters
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationship with backtest results
    backtest_results = relationship("BacktestResult", back_populates="strategy", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Strategy(name='{self.name}', type='{self.strategy_type}')>"

class BacktestResult(Base):
    """Backtest result model for storing backtest performance."""
    __tablename__ = 'backtest_results'
    
    id = Column(Integer, primary_key=True)
    strategy_id = Column(Integer, ForeignKey('strategies.id'), nullable=False)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    initial_capital = Column(Float, nullable=False)
    final_capital = Column(Float, nullable=False)
    total_return = Column(Float, nullable=False)
    annualized_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    total_trades = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with strategy
    strategy = relationship("Strategy", back_populates="backtest_results")
    
    # Relationship with trades
    trades = relationship("Trade", back_populates="backtest_result", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<BacktestResult(strategy_id={self.strategy_id}, total_return={self.total_return})>"

class Trade(Base):
    """Trade model for storing individual trades from backtests."""
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    backtest_result_id = Column(Integer, ForeignKey('backtest_results.id'), nullable=False)
    entry_date = Column(DateTime, nullable=False)
    exit_date = Column(DateTime)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    profit_loss = Column(Float)
    is_long = Column(Boolean, default=True)
    is_closed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationship with backtest result
    backtest_result = relationship("BacktestResult", back_populates="trades")
    
    def __repr__(self):
        return f"<Trade(entry_date='{self.entry_date}', profit_loss={self.profit_loss})>"

class UserSavedReport(Base):
    """User saved report model for storing generated reports."""
    __tablename__ = 'user_saved_reports'
    
    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    description = Column(String)
    report_type = Column(String, nullable=False)  # HTML, PDF
    file_path = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<UserSavedReport(title='{self.title}', type='{self.report_type}')>"

# Create all tables in the database
def create_tables():
    """Create all tables in the database."""
    from sqlalchemy import inspect
    
    # Create inspector to check if tables exist
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Only create tables that don't exist
    if 'market_data' not in existing_tables:
        Base.metadata.create_all(engine)