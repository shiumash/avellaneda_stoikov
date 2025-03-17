"""
Unit tests for exchange_data.py
"""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data.exchange_data import ExchangeData

class TestExchangeData(unittest.TestCase):
    """Tests for the ExchangeData class."""
    
    @patch('data.exchange_data.ccxt')
    def test_initialize_exchange(self, mock_ccxt):
        """Test initialization of exchange connection."""
        # Setup mock
        mock_exchange = MagicMock()
        mock_ccxt.kraken.return_value = mock_exchange
        
        # Initialize exchange
        exchange_data = ExchangeData()
        
        # Check exchange was initialized
        self.assertEqual(exchange_data.exchange_id, 'kraken')
        self.assertEqual(exchange_data.exchange, mock_exchange)
        
        # Verify ccxt was called with correct parameters
        mock_ccxt.kraken.assert_called_once()
    
    @patch('data.exchange_data.ccxt')
    def test_fetch_ohlcv(self, mock_ccxt):
        """Test fetching OHLCV data."""
        # Setup mock
        mock_exchange = MagicMock()
        mock_ccxt.kraken.return_value = mock_exchange
        
        # Setup mock response
        mock_bars = [
            [1609459200000, 1.0, 1.1, 0.9, 1.05, 100],
            [1609459260000, 1.05, 1.15, 0.95, 1.1, 150]
        ]
        mock_exchange.fetch_ohlcv.return_value = mock_bars
        
        # Initialize and call method
        exchange_data = ExchangeData()
        result = exchange_data.fetch_ohlcv('USDT/USD', timeframe='1m', limit=10)
        
        # Check result
        self.assertIsInstance(result, pd.DataFrame)
        self.assertEqual(len(result), 2)
        self.assertIn('open', result.columns)
        self.assertIn('high', result.columns)
        self.assertIn('low', result.columns)
        self.assertIn('close', result.columns)
        self.assertIn('volume', result.columns)
        
        # Verify fetch_ohlcv was called with correct parameters
        mock_exchange.fetch_ohlcv.assert_called_once_with('USDT/USD', timeframe='1m', limit=10)
    
    @patch('data.exchange_data.ccxt')
    def test_fetch_ticker(self, mock_ccxt):
        """Test fetching ticker information."""
        # Setup mock
        mock_exchange = MagicMock()
        mock_ccxt.kraken.return_value = mock_exchange
        
        # Setup mock response
        mock_ticker = {'bid': 1.0, 'ask': 1.02, 'last': 1.01}
        mock_exchange.fetch_ticker.return_value = mock_ticker
        
        # Initialize and call method
        exchange_data = ExchangeData()
        result = exchange_data.fetch_ticker('USDT/USD')
        
        # Check result
        self.assertEqual(result, mock_ticker)
        
        # Verify fetch_ticker was called with correct parameters
        mock_exchange.fetch_ticker.assert_called_once_with('USDT/USD')
    
    @patch('data.exchange_data.ccxt')
    def test_fetch_order_book(self, mock_ccxt):
        """Test fetching order book."""
        # Setup mock
        mock_exchange = MagicMock()
        mock_ccxt.kraken.return_value = mock_exchange
        
        # Setup mock response
        mock_order_book = {
            'bids': [[1.0, 100], [0.99, 200]],
            'asks': [[1.01, 100], [1.02, 200]]
        }
        mock_exchange.fetch_order_book.return_value = mock_order_book
        
        # Initialize and call method
        exchange_data = ExchangeData()
        result = exchange_data.fetch_order_book('USDT/USD', limit=10)
        
        # Check result
        self.assertEqual(result, mock_order_book)
        
        # Verify fetch_order_book was called with correct parameters
        mock_exchange.fetch_order_book.assert_called_once_with('USDT/USD', 10)

if __name__ == '__main__':
    unittest.main()