import MetaTrader5 as mt5
import pandas as pd
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MetaTraderConnector:
    """Connector class for MetaTrader5 API"""
    
    def __init__(self):
        self.connected = False
    
    def initialize(self, path=None, login=None, password=None, server=None):
        """
        Initialize connection to MetaTrader5
        
        Args:
            path: Path to MetaTrader5 terminal (optional)
            login: Account login (optional)
            password: Account password (optional)
            server: Trading server (optional)
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            # Initialize MT5
            if not mt5.initialize():
                error_code = mt5.last_error()
                logger.error(f"MetaTrader5 initialization failed: {error_code}")
                return False
            
            self.connected = True
            logger.info("MetaTrader5 initialized successfully")
            
            # Display account info
            account_info = mt5.account_info()
            if account_info:
                logger.info(f"Connected to account: {account_info.login}, Server: {account_info.server}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing MetaTrader5: {str(e)}")
            self.connected = False
            return False
    
    def is_connected(self):
        """Check if MetaTrader5 is connected"""
        return self.connected and mt5.terminal_info() is not None
    
    def shutdown(self):
        """Shutdown MetaTrader5 connection"""
        mt5.shutdown()
        self.connected = False
        logger.info("MetaTrader5 connection closed")
    
    def get_timeframe_code(self, timeframe_str):
        """
        Convert timeframe string to MT5 timeframe constant
        
        Args:
            timeframe_str: Timeframe string (e.g., 'M1', 'M5', 'M15', 'H1', 'D1')
        
        Returns:
            MT5 timeframe constant
        """
        timeframe_map = {
            'M1': mt5.TIMEFRAME_M1,
            'M2': mt5.TIMEFRAME_M2,
            'M3': mt5.TIMEFRAME_M3,
            'M4': mt5.TIMEFRAME_M4,
            'M5': mt5.TIMEFRAME_M5,
            'M6': mt5.TIMEFRAME_M6,
            'M10': mt5.TIMEFRAME_M10,
            'M12': mt5.TIMEFRAME_M12,
            'M15': mt5.TIMEFRAME_M15,
            'M20': mt5.TIMEFRAME_M20,
            'M30': mt5.TIMEFRAME_M30,
            'H1': mt5.TIMEFRAME_H1,
            'H2': mt5.TIMEFRAME_H2,
            'H3': mt5.TIMEFRAME_H3,
            'H4': mt5.TIMEFRAME_H4,
            'H6': mt5.TIMEFRAME_H6,
            'H8': mt5.TIMEFRAME_H8,
            'H12': mt5.TIMEFRAME_H12,
            'D1': mt5.TIMEFRAME_D1,
            'W1': mt5.TIMEFRAME_W1,
            'MN1': mt5.TIMEFRAME_MN1,
        }
        
        return timeframe_map.get(timeframe_str.upper(), mt5.TIMEFRAME_H1)
    
    def get_quotes(self, symbol, timeframe='H1', count=100, start_date=None, end_date=None):
        """
        Get quotes data from MetaTrader5
        
        Args:
            symbol: Currency pair symbol (e.g., 'EURUSD')
            timeframe: Timeframe string (e.g., 'M1', 'H1', 'D1')
            count: Number of bars to retrieve
            start_date: Start date string in 'YYYY-MM-DD' format (optional)
            end_date: End date string in 'YYYY-MM-DD' format (optional)
        
        Returns:
            list: List of quote dictionaries or None if error
        """
        if not self.is_connected():
            logger.error("MetaTrader5 is not connected")
            return None
        
        try:
            # Convert timeframe string to MT5 constant
            timeframe_code = self.get_timeframe_code(timeframe)
            
            # Prepare date range
            if start_date and end_date:
                # Get quotes for date range
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                rates = mt5.copy_rates_range(symbol, timeframe_code, start, end)
            elif start_date:
                # Get quotes from start date
                start = datetime.strptime(start_date, '%Y-%m-%d')
                rates = mt5.copy_rates_from(symbol, timeframe_code, start, count)
            else:
                # Get latest quotes
                rates = mt5.copy_rates_from_pos(symbol, timeframe_code, 0, count)
            
            if rates is None or len(rates) == 0:
                error_code = mt5.last_error()
                logger.error(f"Failed to get rates for {symbol}: {error_code}")
                return None
            
            # Convert to DataFrame for easier manipulation
            df = pd.DataFrame(rates)
            
            # Convert time to readable format
            df['time'] = pd.to_datetime(df['time'], unit='s')
            
            # Convert to list of dictionaries
            quotes = []
            for _, row in df.iterrows():
                quotes.append({
                    'time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'tick_volume': int(row['tick_volume']),
                    'spread': int(row['spread']) if 'spread' in row else None,
                    'real_volume': int(row['real_volume']) if 'real_volume' in row else None
                })
            
            logger.info(f"Retrieved {len(quotes)} quotes for {symbol} ({timeframe})")
            return quotes
            
        except Exception as e:
            logger.error(f"Error getting quotes for {symbol}: {str(e)}")
            return None
    
    def get_symbols(self):
        """
        Get list of available symbols from MetaTrader5
        
        Returns:
            list: List of symbol names or None if error
        """
        if not self.is_connected():
            logger.error("MetaTrader5 is not connected")
            return None
        
        try:
            symbols = mt5.symbols_get()
            if symbols is None:
                error_code = mt5.last_error()
                logger.error(f"Failed to get symbols: {error_code}")
                return None
            
            symbol_names = [symbol.name for symbol in symbols]
            logger.info(f"Retrieved {len(symbol_names)} symbols")
            return symbol_names
            
        except Exception as e:
            logger.error(f"Error getting symbols: {str(e)}")
            return None

