"""
Unit tests for avellaneda_stoikov.py
"""
import unittest
import sys
import os
import numpy as np

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from models.avellaneda_stoikov import AvellanedaStoikov

class TestAvellanedaStoikov(unittest.TestCase):
    """Tests for the AvellanedaStoikov class."""
    
    def setUp(self):
        """Set up test cases."""
        self.gamma = 0.1
        self.lambda_b = 1.0
        self.lambda_a = 1.0
        self.model = AvellanedaStoikov(gamma=self.gamma, lambda_b=self.lambda_b, lambda_a=self.lambda_a)
    
    def test_initialization(self):
        """Test initialization of the model."""
        self.assertEqual(self.model.gamma, self.gamma)
        self.assertEqual(self.model.lambda_b, self.lambda_b)
        self.assertEqual(self.model.lambda_a, self.lambda_a)
    
    def test_calculate_bid_spread(self):
        """Test calculation of bid spread."""
        volatility = 0.01
        inventory = 0.0
        
        # Manual calculation of expected result
        expected_first_term = (1 / self.gamma) * np.log(1 + (self.gamma / self.lambda_b))
        expected_second_term = 0.5 * self.gamma * (volatility ** 2) * ((inventory + 1) ** 2)
        expected_spread = expected_first_term + expected_second_term
        
        # Call the method
        spread = self.model.calculate_bid_spread(volatility, inventory)
        
        # Check result
        self.assertAlmostEqual(spread, expected_spread, places=6)
    
    def test_calculate_ask_spread(self):
        """Test calculation of ask spread."""
        volatility = 0.01
        inventory = 0.0
        
        # Manual calculation of expected result
        expected_first_term = (1 / self.gamma) * np.log(1 + (self.gamma / self.lambda_a))
        expected_second_term = 0.5 * self.gamma * (volatility ** 2) * ((inventory - 1) ** 2)
        expected_spread = expected_first_term + expected_second_term
        
        # Call the method
        spread = self.model.calculate_ask_spread(volatility, inventory)
        
        # Check result
        self.assertAlmostEqual(spread, expected_spread, places=6)
    
    def test_calculate_spreads(self):
        """Test calculation of bid and ask prices."""
        mid_price = 100.0
        volatility = 0.01
        inventory = 0.0
        
        # Expected spreads based on the formulas
        expected_bid_spread = self.model.calculate_bid_spread(volatility, inventory)
        expected_ask_spread = self.model.calculate_ask_spread(volatility, inventory)
        
        expected_bid_price = mid_price - expected_bid_spread
        expected_ask_price = mid_price + expected_ask_spread
        
        # Call the method
        bid_price, ask_price = self.model.calculate_spreads(mid_price, volatility, inventory)
        
        # Check results
        self.assertAlmostEqual(bid_price, expected_bid_price, places=6)
        self.assertAlmostEqual(ask_price, expected_ask_price, places=6)
        self.assertTrue(bid_price < mid_price < ask_price, "Bid price should be less than mid price, which should be less than ask price")

if __name__ == '__main__':
    unittest.main()