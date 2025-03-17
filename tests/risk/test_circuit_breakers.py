"""
Unit tests for circuit_breakers.py
"""
import unittest
import numpy as np
import pandas as pd
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from risk.circuit_breakers import CircuitBreakers

class TestCircuitBreakers(unittest.TestCase):
    """Tests for the CircuitBreakers class."""
    
    def setUp(self):
        """Set up test cases."""
        self.price_change_threshold = 0.1
        self.circuit_breakers = CircuitBreakers(price_change_threshold=self.price_change_threshold)
    
    def test_initialization(self):
        """Test initialization of the circuit breakers."""
        self.assertEqual(self.circuit_breakers.price_change_threshold, self.price_change_threshold)
    
    def test_check_flash_crash_no_crash(self):
        """Test flash crash detection with no crash."""
        # Prices with small fluctuations
        recent_prices = np.array([100.0, 101.0, 99.0, 100.5, 101.2])
        
        # Call the method
        result = self.circuit_breakers.check_flash_crash(recent_prices)
        
        # Check result
        self.assertFalse(result)
    
    def test_check_flash_crash_with_crash(self):
        """Test flash crash detection with a crash."""
        # Prices with a crash (more than 10% drop)
        recent_prices = np.array([100.0, 95.0, 90.0, 85.0, 80.0])
        
        # Call the method
        result = self.circuit_breakers.check_flash_crash(recent_prices)
        
        # Check result
        self.assertTrue(result)
    
    def test_check_stablecoin_depeg_no_depeg(self):
        """Test stablecoin depeg detection with no depeg."""
        # Price close to peg
        price = 1.01
        
        # Call the method
        result = self.circuit_breakers.check_stablecoin_depeg(price)
        
        # Check result
        self.assertFalse(result)
    
    def test_check_stablecoin_depeg_with_depeg(self):
        """Test stablecoin depeg detection with a depeg."""
        # Price significantly away from peg
        price = 0.90
        
        # Call the method
        result = self.circuit_breakers.check_stablecoin_depeg(price)
        
        # Check result
        self.assertTrue(result)
    
    def test_check_abnormal_volume_no_abnormality(self):
        """Test abnormal volume detection with no abnormality."""
        # Normal volume fluctuation
        recent_volumes = np.array([100, 110, 95, 105, 115, 90, 105, 110, 100, 105])
        
        # Call the method
        result = self.circuit_breakers.check_abnormal_volume(recent_volumes)
        
        # Check result
        self.assertFalse(result)
    
    def test_check_abnormal_volume_with_abnormality(self):
        """Test abnormal volume detection with an abnormality."""
        # Last volume is abnormally high
        recent_volumes = np.array([100, 110, 95, 105, 115, 90, 105, 110, 100, 500])
        
        # Call the method
        result = self.circuit_breakers.check_abnormal_volume(recent_volumes)
        
        # Check result
        self.assertTrue(result)
    
    def test_check_all_circuit_breakers(self):
        """Test the comprehensive circuit breaker check."""
        # Create test market data
        market_data = pd.DataFrame({
            'close': [100.0, 101.0, 99.0, 100.5, 101.2, 100.8, 99.5, 98.0, 97.0, 96.0],
            'volume': [100, 110, 95, 105, 115, 90, 105, 110, 100, 95]
        })
        
        # Mock the individual checks
        self.circuit_breakers.check_flash_crash = lambda x: False
        self.circuit_breakers.check_stablecoin_depeg = lambda x: False
        self.circuit_breakers.check_abnormal_volume = lambda x: False
        
        # Call the method
        result = self.circuit_breakers.check_all_circuit_breakers(market_data)
        
        # Check result
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()