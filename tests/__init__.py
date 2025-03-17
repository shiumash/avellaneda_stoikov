"""
Unit tests for main.py
"""
import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

# Add the parent directory to the path so we can import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import initialize, market_making_cycle

class TestMain(unittest.TestCase):
    """Tests for the main module functions."""
    
    @patch('main.setup_logging')
    @patch('main.ExchangeData')
    @patch('main.OrderManager')
    @patch('main.PositionTracker')
    @patch('main.CircuitBreakers')
    @patch('main.InventoryManager')
    @patch('main.AvellanedaStoikov')
    def test_initialize(self, mock_as, mock_im, mock_cb, mock_pt, mock_om, mock_ed, mock_logging):
        """Test the initialize function."""
        # Setup mocks
        mock_logging.return_value = MagicMock()
        mock_ed.return_value = MagicMock()
        mock_ed.return_value.exchange = MagicMock()
        
        # Call the function
        components = initialize()
        
        # Check that all required components are initialized
        self.assertIn('logger', components)
        self.assertIn('exchange_data', components)
        self.assertIn('order_manager', components)
        self.assertIn('position_tracker', components)
        self.assertIn('circuit_breakers', components)
        self.assertIn('inventory_manager', components)
        self.assertIn('model', components)
        
        # Verify that components are initialized with correct parameters
        mock_om.assert_called_once()
        mock_pt.assert_called_once()
        mock_cb.assert_called_once()
        mock_im.assert_called_once()
        mock_as.assert_called_once()
    
    @patch('main.get_volatility_from_bollinger')
    def test_market_making_cycle_success(self, mock_get_volatility):
        """Test the market making cycle with successful execution."""
        # Create mock components
        mock_logger = MagicMock()
        mock_exchange_data = MagicMock()
        mock_order_manager = MagicMock()
        mock_position_tracker = MagicMock()
        mock_circuit_breakers = MagicMock()
        mock_inventory_manager = MagicMock()
        mock_model = MagicMock()
        
        components = {
            'logger': mock_logger,
            'exchange_data': mock_exchange_data,
            'order_manager': mock_order_manager,
            'position_tracker': mock_position_tracker,
            'circuit_breakers': mock_circuit_breakers,
            'inventory_manager': mock_inventory_manager,
            'model': mock_model
        }
        
        # Configure mocks
        mock_market_data = pd.DataFrame({
            'open': [1.0, 2.0, 3.0],
            'high': [1.1, 2.1, 3.1],
            'low': [0.9, 1.9, 2.9],
            'close': [1.05, 2.05, 3.05],
            'volume': [100, 200, 300]
        })
        mock_exchange_data.fetch_ohlcv.return_value = mock_market_data
        mock_circuit_breakers.check_all_circuit_breakers.return_value = False
        mock_get_volatility.return_value = 0.01
        mock_order_manager.fetch_balances.return_value = (100.0, 5000.0)
        
        mock_ticker = {'bid': 1.0, 'ask': 1.02, 'last': 1.01}
        mock_exchange_data.fetch_ticker.return_value = mock_ticker
        
        mock_inventory_manager.update_inventory.return_value = 0.0
        mock_model.calculate_spreads.return_value = (0.98, 1.04)
        mock_inventory_manager.adjust_spreads.return_value = (0.02, 0.02)
        mock_order_manager.update_orders.return_value = (MagicMock(), MagicMock())
        
        # Call the function
        result = market_making_cycle(components)
        
        # Check result
        self.assertTrue(result)
        
        # Verify all expected calls were made
        mock_exchange_data.fetch_ohlcv.assert_called_once()
        mock_circuit_breakers.check_all_circuit_breakers.assert_called_once_with(mock_market_data)
        mock_get_volatility.assert_called_once_with(mock_market_data)
        mock_order_manager.fetch_balances.assert_called_once()
        mock_exchange_data.fetch_ticker.assert_called_once()
        mock_inventory_manager.update_inventory.assert_called_once()
        mock_position_tracker.record_position.assert_called_once()
        mock_model.calculate_spreads.assert_called_once()
        mock_inventory_manager.adjust_spreads.assert_called_once()
        mock_order_manager.update_orders.assert_called_once()
    
    @patch('main.get_volatility_from_bollinger')
    def test_market_making_cycle_circuit_breaker(self, mock_get_volatility):
        """Test the market making cycle with circuit breaker triggered."""
        # Create mock components
        mock_logger = MagicMock()
        mock_exchange_data = MagicMock()
        mock_order_manager = MagicMock()
        mock_position_tracker = MagicMock()
        mock_circuit_breakers = MagicMock()
        mock_inventory_manager = MagicMock()
        mock_model = MagicMock()
        
        components = {
            'logger': mock_logger,
            'exchange_data': mock_exchange_data,
            'order_manager': mock_order_manager,
            'position_tracker': mock_position_tracker,
            'circuit_breakers': mock_circuit_breakers,
            'inventory_manager': mock_inventory_manager,
            'model': mock_model
        }
        
        # Configure mocks
        mock_market_data = pd.DataFrame({
            'open': [1.0, 2.0, 3.0],
            'high': [1.1, 2.1, 3.1],
            'low': [0.9, 1.9, 2.9],
            'close': [1.05, 2.05, 3.05],
            'volume': [100, 200, 300]
        })
        mock_exchange_data.fetch_ohlcv.return_value = mock_market_data
        mock_circuit_breakers.check_all_circuit_breakers.return_value = True
        
        # Call the function
        result = market_making_cycle(components)
        
        # Check result
        self.assertFalse(result)
        
        # Verify expected calls
        mock_exchange_data.fetch_ohlcv.assert_called_once()
        mock_circuit_breakers.check_all_circuit_breakers.assert_called_once()
        mock_order_manager.cancel_all_orders.assert_called_once()
        mock_get_volatility.assert_not_called()

if __name__ == '__main__':
    unittest.main()