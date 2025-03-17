"""
Unit tests for inventory_manager.py
"""
import unittest
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from risk.inventory_manager import InventoryManager

class TestInventoryManager(unittest.TestCase):
    """Tests for the InventoryManager class."""
    
    def setUp(self):
        """Set up test cases."""
        self.max_inventory_pct = 0.1
        self.skew_threshold = 0.05
        self.inventory_manager = InventoryManager(
            max_inventory_pct=self.max_inventory_pct, 
            skew_threshold=self.skew_threshold
        )
    
    def test_initialization(self):
        """Test initialization of the inventory manager."""
        self.assertEqual(self.inventory_manager.max_inventory_pct, self.max_inventory_pct)
        self.assertEqual(self.inventory_manager.skew_threshold, self.skew_threshold)
        self.assertEqual(self.inventory_manager.current_inventory, 0)
        self.assertEqual(self.inventory_manager.base_balance, 0)
    
    def test_update_inventory_balanced(self):
        """Test updating inventory with balanced position."""
        # Equal base and quote values
        base_balance = 1.0
        quote_balance = 100.0
        mid_price = 100.0
        
        # Call the method
        inventory_pct = self.inventory_manager.update_inventory(base_balance, quote_balance, mid_price)
        
        # Check result - should be close to 0 (balanced)
        self.assertAlmostEqual(inventory_pct, 0.0, places=6)
        self.assertEqual(self.inventory_manager.base_balance, base_balance)
    
    def test_update_inventory_base_heavy(self):
        """Test updating inventory with base-heavy position."""
        # More base value than quote
        base_balance = 2.0
        quote_balance = 100.0
        mid_price = 100.0
        
        # Call the method
        inventory_pct = self.inventory_manager.update_inventory(base_balance, quote_balance, mid_price)
        
        # Check result - should be positive (base-heavy)
        self.assertTrue(inventory_pct > 0)
        self.assertEqual(self.inventory_manager.base_balance, base_balance)
    
    def test_update_inventory_quote_heavy(self):
        """Test updating inventory with quote-heavy position."""
        # More quote value than base
        base_balance = 0.5
        quote_balance = 100.0
        mid_price = 100.0
        
        # Call the method
        inventory_pct = self.inventory_manager.update_inventory(base_balance, quote_balance, mid_price)
        
        # Check result - should be negative (quote-heavy)
        self.assertTrue(inventory_pct < 0)
        self.assertEqual(self.inventory_manager.base_balance, base_balance)
    
    def test_adjust_spreads_no_adjustment(self):
        """Test spread adjustment with balanced inventory."""
        # Set balanced inventory
        self.inventory_manager.current_inventory = 0.02  # Within threshold
        
        # Base spreads
        base_bid_spread = 0.5
        base_ask_spread = 0.5
        base_spreads = (base_bid_spread, base_ask_spread)
        
        # Call the method
        adjusted_bid_spread, adjusted_ask_spread = self.inventory_manager.adjust_spreads(base_spreads)
        
        # Check result - should be no change to spreads
        self.assertEqual(adjusted_bid_spread, base_bid_spread)
        self.assertEqual(adjusted_ask_spread, base_ask_spread)
    
    def test_adjust_spreads_base_heavy(self):
        """Test spread adjustment with base-heavy inventory."""
        # Set base-heavy inventory
        self.inventory_manager.current_inventory = 0.08  # Above threshold
        
        # Base spreads
        base_bid_spread = 0.5
        base_ask_spread = 0.5
        base_spreads = (base_bid_spread, base_ask_spread)
        
        # Call the method
        adjusted_bid_spread, adjusted_ask_spread = self.inventory_manager.adjust_spreads(base_spreads)
        
        # Check result - bid spread should increase, ask spread should decrease
        self.assertTrue(adjusted_bid_spread > base_bid_spread)
        self.assertTrue(adjusted_ask_spread < base_ask_spread)
    
    def test_adjust_spreads_quote_heavy(self):
        """Test spread adjustment with quote-heavy inventory."""
        # Set quote-heavy inventory
        self.inventory_manager.current_inventory = -0.08  # Below negative threshold
        
        # Base spreads
        base_bid_spread = 0.5
        base_ask_spread = 0.5
        base_spreads = (base_bid_spread, base_ask_spread)
        
        # Call the method
        adjusted_bid_spread, adjusted_ask_spread = self.inventory_manager.adjust_spreads(base_spreads)
        
        # Check result - bid spread should decrease, ask spread should increase
        self.assertTrue(adjusted_bid_spread < base_bid_spread)
        self.assertTrue(adjusted_ask_spread > base_ask_spread)

if __name__ == '__main__':
    unittest.main()