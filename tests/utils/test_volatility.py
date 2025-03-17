"""
Unit tests for volatility.py
"""
import unittest
import pandas as pd
import numpy as np
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from utils.volatility import get_volatility_from_bollinger

class TestVolatility(unittest.TestCase):
    """Tests for the volatility utility functions."""
    
    def test_get_volatility_from_bollinger(self):
        """Test calculating volatility from bollinger bands."""
        # Create test market data
        dates = pd.date_range('2022-01-01', periods=100)
        price_data = np.sin(np.linspace(0, 4*np.pi, 100)) * 10 + 100  # Sine wave + base
        
        market_data = pd.DataFrame({
            'open': price_data,
            'high': price_data * 1.01,
            'low': price_data * 0.99,
            'close': price_data,
            'volume': np.random.rand(100) * 100
        }, index=dates)
        
        # Call the function
        result = get_volatility_from_bollinger(market_data, window=20)
        
        # Check result
        self.assertIsInstance(result, float)
        self.assertTrue(0 < result < 1, f"Volatility should be between 0 and 1, got {result}")
    
    def test_get_volatility_empty_data(self):
        """Test with empty dataframe."""
        # Empty dataframe
        market_data = pd.DataFrame()
        
        # Call the function
        result = get_volatility_from_bollinger(market_data, window=20)
        
        # Check result - default to a small non-zero value
        self.assertEqual(result, 0.001)  # Assume default fallback is 0.001
    
    def test_get_volatility_insufficient_data(self):
        """Test with insufficient data points."""
        # Create small dataframe
        market_data = pd.DataFrame({
            'open': [100, 101],
            'high': [102, 103],
            'low': [99, 98],
            'close': [101, 100],
            'volume': [50, 60]
        })
        
        # Call the function with window larger than data
        result = get_volatility_from_bollinger(market_data, window=20)
        
        # Check result - should use available data
        self.assertIsInstance(result, float)
    
    def test_get_volatility_constant_price(self):
        """Test with constant price data."""
        # Create dataframe with constant prices
        dates = pd.date_range('2022-01-01', periods=100)
        price_data = np.ones(100) * 100  # Constant price
        
        market_data = pd.DataFrame({
            'open': price_data,
            'high': price_data,
            'low': price_data,
            'close': price_data,
            'volume': np.random.rand(100) * 100
        }, index=dates)
        
        # Call the function
        result = get_volatility_from_bollinger(market_data, window=20)
        
        # Check result - should be very close to 0
        self.assertAlmostEqual(result, 0.0, places=6)

if __name__ == '__main__':
    unittest.main()