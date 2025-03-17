"""
Module for fetching data from cryptocurrency exchanges.
"""
import pandas as pd
import ccxt
import logging
from config.settings import API_KEY, API_SECRET

logger = logging.getLogger('market_maker')

class ExchangeData:
    """Class for interacting with cryptocurrency exchanges."""
    
    def __init__(self, exchange_id='kraken'):
        """
        Initialize the exchange connection.
        
        Args:
            exchange_id (str): The exchange identifier (default: 'kraken')
        """
        self.exchange_id = exchange_id
        self.exchange = self._initialize_exchange()
        
    def _initialize_exchange(self):
        """Initialize the exchange connection."""
        try:
            # Initialize exchange with API credentials
            exchange = getattr(ccxt, self.exchange_id)({
                'apiKey': API_KEY,
                'secret': API_SECRET,
                'enableRateLimit': True,
            })
            logger.info(f"Successfully initialized {self.exchange_id} exchange")
            return exchange
        except Exception as e:
            logger.error(f"Error initializing exchange: {e}")
            raise
            
    def fetch_ohlcv(self, symbol, timeframe='1m', limit=60):
        """
        Fetch OHLCV data from the exchange.
        
        Args:
            symbol (str): Trading pair symbol
            timeframe (str): Timeframe for candles
            limit (int): Number of candles to fetch
            
        Returns:
            pd.DataFrame: DataFrame with OHLCV data or None if error
        """
        try:
            logger.info(f"Fetching {limit} {timeframe} candles for {symbol}")
            
            # Fetch the OHLCV data
            bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            # Convert to DataFrame
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            logger.info(f"Successfully fetched {len(df)} candles")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return None
    
    def fetch_ticker(self, symbol):
        """
        Fetch current ticker information.
        
        Args:
            symbol (str): Trading pair symbol
            
        Returns:
            dict: Ticker information or None if error
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return ticker
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            return None
            
    def fetch_order_book(self, symbol, limit=20):
        """
        Fetch order book for a symbol.
        
        Args:
            symbol (str): Trading pair symbol
            limit (int): Depth of the order book to fetch
            
        Returns:
            dict: Order book or None if error
        """
        try:
            order_book = self.exchange.fetch_order_book(symbol, limit)
            return order_book
        except Exception as e:
            logger.error(f"Error fetching order book: {e}")
            return None