"""
Management of order placement, cancellation and tracking.
"""
import logging
import time
from config.settings import BASE_ORDER_SIZE

logger = logging.getLogger('market_maker')

class OrderManager:
    """
    Class for managing orders on the exchange.
    """
    
    def __init__(self, exchange, symbol, base_order_size=BASE_ORDER_SIZE):
        """
        Initialize the order manager.
        
        Args:
            exchange: Exchange instance
            symbol (str): Trading pair symbol
            base_order_size (float): Base size for orders
        """
        self.exchange = exchange
        self.symbol = symbol
        self.base_order_size = base_order_size
        self.open_orders = {}  # Track open orders by id
        logger.info(f"Initialized order manager for {symbol} with base size {base_order_size}")
        
    def place_limit_order(self, side, price, size=None):
        """
        Place a limit order on the exchange.
        
        Args:
            side (str): 'buy' or 'sell'
            price (float): Limit price
            size (float, optional): Order size or use base size
            
        Returns:
            dict: Order information or None if error
        """
        if size is None:
            size = self.base_order_size
            
        try:
            logger.info(f"Placing {side} order: {size} @ {price:.6f}")
            
            if side == 'buy':
                order = self.exchange.create_limit_buy_order(self.symbol, size, price)
            elif side == 'sell':
                order = self.exchange.create_limit_sell_order(self.symbol, size, price)
            else:
                logger.error(f"Invalid order side: {side}")
                return None
                
            # Track the order
            self.open_orders[order['id']] = {
                'id': order['id'],
                'side': side,
                'price': price,
                'size': size,
                'timestamp': time.time()
            }
            
            logger.info(f"Successfully placed {side} order with ID: {order['id']}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing {side} order: {e}")
            return None
            
    def cancel_order(self, order_id):
        """
        Cancel a specific order.
        
        Args:
            order_id (str): Order ID to cancel
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"Cancelling order ID: {order_id}")
            self.exchange.cancel_order(order_id, self.symbol)
            
            # Remove from tracking
            if order_id in self.open_orders:
                del self.open_orders[order_id]
                
            return True
            
        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False
            
    def cancel_all_orders(self):
        """
        Cancel all open orders for the symbol.
        
        Returns:
            int: Number of orders cancelled
        """
        try:
            logger.info(f"Cancelling all open orders for {self.symbol}")
            orders = self.exchange.fetch_open_orders(self.symbol)
            
            cancel_count = 0
            for order in orders:
                self.exchange.cancel_order(order['id'], self.symbol)
                cancel_count += 1
                
                # Remove from tracking
                if order['id'] in self.open_orders:
                    del self.open_orders[order['id']]
                    
            logger.info(f"Cancelled {cancel_count} open orders")
            return cancel_count
            
        except Exception as e:
            logger.error(f"Error cancelling all orders: {e}")
            return 0
            
    def update_orders(self, bid_price, ask_price, price_threshold=0.0005):
        """
        Update orders only when price changes exceed the threshold.
        
        Args:
            bid_price (float): New bid price
            ask_price (float): New ask price
            price_threshold (float): Minimum price change to trigger an update (as % of price)
            
        Returns:
            tuple: (bid_order, ask_order) information
        """
        update_bid = True
        update_ask = True
        
        # Check if open orders exist
        open_orders = self.exchange.fetch_open_orders(self.symbol)
        bid_order = None
        ask_order = None
        
        # Find current bid/ask orders
        for order in open_orders:
            if order['side'] == 'buy':
                bid_order = order
            elif order['side'] == 'sell':
                ask_order = order
        
        # Check if bid price change is significant
        if bid_order and 'price' in bid_order:
            price_diff_pct = abs(bid_order['price'] - bid_price) / bid_order['price']
            if price_diff_pct < price_threshold:
                update_bid = False
                logger.debug(f"Keeping existing bid order: price change {price_diff_pct:.4%} below threshold")
        
        # Check if ask price change is significant
        if ask_order and 'price' in ask_order:
            price_diff_pct = abs(ask_order['price'] - ask_price) / ask_order['price']
            if price_diff_pct < price_threshold:
                update_ask = False
                logger.debug(f"Keeping existing ask order: price change {price_diff_pct:.4%} below threshold")
                
        # Update orders as needed
        if update_bid and bid_order:
            self.cancel_order(bid_order['id'])
            bid_order = None
            
        if update_ask and ask_order:
            self.cancel_order(ask_order['id'])
            ask_order = None
            
        # Place new orders if needed
        if bid_order is None:
            bid_order = self.place_limit_order('buy', bid_price)
            
        if ask_order is None:  
            ask_order = self.place_limit_order('sell', ask_price)
            
        return bid_order, ask_order
        
    def fetch_balances(self):
        """
        Fetch current balances for the trading pair currencies.
        
        Returns:
            tuple: (base_balance, quote_balance) or (None, None) if error
        """
        try:
            balances = self.exchange.fetch_balance()
            
            # Extract the base and quote currencies from the symbol
            currencies = self.symbol.split('/')
            base_currency = currencies[0]
            quote_currency = currencies[1]
            
            # Get the balances for each currency
            base_balance = balances.get(base_currency, {}).get('free', 0)
            quote_balance = balances.get(quote_currency, {}).get('free', 0)
            
            logger.info(f"Balances: {base_currency}={base_balance}, {quote_currency}={quote_balance}")
            return base_balance, quote_balance
            
        except Exception as e:
            logger.error(f"Error fetching balances: {e}")
            return None, None