"""
Unit tests for order_manager.py
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading.order_manager import OrderManager

class TestOrderManager(unittest.TestCase):
    """Tests for the OrderManager class."""
    
    def setUp(self):
        """Set up test cases."""
        self.exchange = MagicMock()
        self.symbol = 'BTC/USDT'
        self.order_manager = OrderManager(self.exchange, self.symbol)
    
    def test_initialization(self):
        """Test initialization of the order manager."""
        self.assertEqual(self.order_manager.exchange, self.exchange)
        self.assertEqual(self.order_manager.symbol, self.symbol)
        self.assertEqual(self.order_manager.bid_order, None)
        self.assertEqual(self.order_manager.ask_order, None)
    
    def test_fetch_balances(self):
        """Test fetching account balances."""
        # Setup mock response
        mock_balance = {
            'BTC': {'free': 1.0, 'used': 0.5, 'total': 1.5},
            'USDT': {'free': 10000.0, 'used': 5000.0, 'total': 15000.0}
        }
        self.exchange.fetch_balance.return_value = {'free': mock_balance}
        
        # Call the method
        base_balance, quote_balance = self.order_manager.fetch_balances()
        
        # Check result
        self.assertEqual(base_balance, 1.0)  # Free BTC
        self.assertEqual(quote_balance, 10000.0)  # Free USDT
        
        # Verify exchange API was called
        self.exchange.fetch_balance.assert_called_once()
    
    def test_create_order(self):
        """Test creating an order."""
        # Setup mock response
        mock_order = {'id': '12345', 'status': 'open'}
        self.exchange.create_limit_order.return_value = mock_order
        
        # Call the method
        order_type = 'bid'
        price = 20000.0
        size = 0.1
        result = self.order_manager.create_order(order_type, price, size)
        
        # Check result
        self.assertEqual(result, mock_order)
        
        # Verify exchange API was called with correct parameters
        self.exchange.create_limit_order.assert_called_once_with(
            self.symbol, 'buy', size, price
        )
    
    def test_cancel_order(self):
        """Test cancelling an order."""
        # Setup mock order
        mock_order = {'id': '12345', 'status': 'open'}
        
        # Setup mock response
        self.exchange.cancel_order.return_value = {'id': '12345', 'status': 'canceled'}
        
        # Call the method
        result = self.order_manager.cancel_order(mock_order)
        
        # Verify exchange API was called with correct parameters
        self.exchange.cancel_order.assert_called_once_with(mock_order['id'], self.symbol)
    
    def test_update_orders_no_existing_orders(self):
        """Test updating orders when no orders exist."""
        # Setup initial state
        self.order_manager.bid_order = None
        self.order_manager.ask_order = None
        
        # Setup mock responses
        mock_bid_order = {'id': 'bid123', 'status': 'open'}
        mock_ask_order = {'id': 'ask123', 'status': 'open'}
        self.order_manager.create_order = MagicMock(side_effect=[mock_bid_order, mock_ask_order])
        
        # Call the method
        bid_price = 19000.0
        ask_price = 21000.0
        bid_order, ask_order = self.order_manager.update_orders(bid_price, ask_price)
        
        # Check result
        self.assertEqual(bid_order, mock_bid_order)
        self.assertEqual(ask_order, mock_ask_order)
        
        # Verify create_order was called twice
        self.assertEqual(self.order_manager.create_order.call_count, 2)
    
    def test_update_orders_with_existing_orders(self):
        """Test updating orders when orders already exist."""
        # Setup initial state
        self.order_manager.bid_order = {'id': 'old_bid', 'price': 18000.0}
        self.order_manager.ask_order = {'id': 'old_ask', 'price': 22000.0}
        
        # Setup mock methods
        self.order_manager.cancel_order = MagicMock()
        
        mock_bid_order = {'id': 'new_bid', 'status': 'open'}
        mock_ask_order = {'id': 'new_ask', 'status': 'open'}