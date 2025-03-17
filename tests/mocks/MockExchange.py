"""
Mock implementation of a cryptocurrency exchange for paper trading.
"""
import pandas as pd
import numpy as np
import time
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('market_maker')

class MockExchange:
    """
    Mock implementation of a cryptocurrency exchange for paper trading.
    """
    
    def __init__(self, initial_balances=None, initial_price=1.0, price_volatility=0.01):
        """
        Initialize the mock exchange.
        
        Args:
            initial_balances (dict): Initial balances for paper trading
            initial_price (float): Initial price of the asset
            price_volatility (float): Volatility for price simulation
        """
        # Default initial balances
        self.balances = initial_balances or {
            'BTC': {'free': 1.0, 'used': 0.0, 'total': 1.0},
            'USDT': {'free': 10000.0, 'used': 0.0, 'total': 10000.0},
            'USD': {'free': 10000.0, 'used': 0.0, 'total': 10000.0}
        }
        
        # Order book simulation
        self.current_price = initial_price
        self.price_volatility = price_volatility
        self.orders = {}  # Store open orders
        self.order_id_counter = 1
        
        # Market data simulation
        self.initial_timestamp = datetime.now() - timedelta(days=1)
        
        # Generate some historical data
        self._generate_historical_data()
        
        self.maker_fee = 0.0002  # 0.02% maker fee
        self.taker_fee = 0.0005  # 0.05% taker fee
        self.initial_price = initial_price
        
        logger.info(f"Initialized mock exchange with balances: {self.balances}")
    
    def _generate_historical_data(self):
        """Generate simulated historical price data."""
        # Create 1000 minutes of historical data
        timestamps = [self.initial_timestamp + timedelta(minutes=i) for i in range(1000)]
        
        # Generate a random walk for prices
        prices = [self.current_price]
        for i in range(999):
            # Random price movement with mean reverting tendency
            change = np.random.normal(0, self.price_volatility * self.current_price)
            new_price = max(0.0001, prices[-1] + change)
            prices.append(new_price)
        
        # Store historical candles
        self.historical_data = []
        for i, ts in enumerate(timestamps):
            # Create higher and lower prices around close
            close_price = prices[i]
            high_price = close_price * (1 + abs(np.random.normal(0, self.price_volatility)))
            low_price = close_price * (1 - abs(np.random.normal(0, self.price_volatility)))
            open_price = prices[i-1] if i > 0 else close_price
            
            # Generate random volume
            volume = abs(np.random.normal(100, 30))
            
            # Create candle
            candle = [
                int(ts.timestamp() * 1000),  # timestamp in ms
                float(open_price),           # open
                float(high_price),           # high
                float(low_price),            # low
                float(close_price),          # close
                float(volume)                # volume
            ]
            self.historical_data.append(candle)
        
        logger.info(f"Generated {len(self.historical_data)} historical candles")
    
    def update_volatility(self, new_volatility):
        """
        Update the price volatility parameter.
        
        
        Args:
            new_volatility (float): New volatility value
        """
        self.price_volatility = new_volatility
        logger.info(f"Updated mock exchange volatility to {new_volatility:.6f}")
    
    def _update_price(self):
        """Update the current price with more realistic movement."""
        # Add mean-reversion component
        mean_reversion_factor = 0.05
        mean_reversion = mean_reversion_factor * (self.initial_price - self.current_price)
        
        # Add momentum component based on recent direction
        if hasattr(self, 'price_history'):
            if len(self.price_history) > 5:
                recent_returns = [(self.price_history[i] / self.price_history[i-1]) - 1 
                                for i in range(1, len(self.price_history))]
                momentum = sum(recent_returns[-5:]) / 5 * 0.3  # 30% weight to momentum
            else:
                momentum = 0
        else:
            self.price_history = [self.current_price]
            momentum = 0
            
        # Add fat-tailed noise (t-distribution instead of normal)
        degrees_freedom = 3  # Lower means fatter tails
        noise_scale = self.price_volatility * self.current_price
        noise = np.random.standard_t(degrees_freedom) * noise_scale / np.sqrt(degrees_freedom/(degrees_freedom-2))
        
        # Combine components
        change = mean_reversion + momentum + noise
        
        # Update price
        self.current_price = max(0.0001, self.current_price + change)
        
        # Store in history
        self.price_history.append(self.current_price)
        if len(self.price_history) > 100:
            self.price_history.pop(0)
            
        return self.current_price
    
    def _process_fills(self):
        """Process potential order fills based on price movement."""
        price = self._update_price()
        
        # Check if any orders should be filled
        filled_orders = []
        
        for order_id, order in list(self.orders.items()):
            # Check if the price crosses our order price
            if (order['side'] == 'buy' and price <= order['price']) or \
               (order['side'] == 'sell' and price >= order['price']):
                
                # Fill the order
                self._execute_order(order)
                filled_orders.append(order_id)
        
        # Remove filled orders
        for order_id in filled_orders:
            del self.orders[order_id]
    
    def _execute_order(self, order):
        """Execute an order, updating balances with fees."""
        symbol = order['symbol']
        currencies = symbol.split('/')
        base_currency = currencies[0]
        quote_currency = currencies[1]
        
        amount = order['amount']
        price = order['price']
        
        # Apply fees based on aggressive/passive order execution
        # For simplicity, we'll use maker fee for limit orders
        fee_rate = self.maker_fee
        
        if order['side'] == 'buy':
            # Deduct quote currency, add base currency
            cost = amount * price
            fee_amount = cost * fee_rate
            
            # Update balances with fees
            self.balances[quote_currency]['used'] -= cost
            self.balances[quote_currency]['total'] -= (cost + fee_amount)
            self.balances[base_currency]['free'] += amount
            self.balances[base_currency]['total'] += amount
            
            logger.info(f"Executed buy: {amount} @ {price} with fee: {fee_amount:.6f} {quote_currency}")
            
        elif order['side'] == 'sell':
            # Add quote currency, deduct base currency
            proceeds = amount * price
            fee_amount = proceeds * fee_rate
            
            # Update balances with fees
            self.balances[base_currency]['used'] -= amount
            self.balances[quote_currency]['free'] += (proceeds - fee_amount)
            self.balances[quote_currency]['total'] += (proceeds - fee_amount)
            self.balances[base_currency]['total'] -= amount
            
            logger.info(f"Executed sell: {amount} @ {price} with fee: {fee_amount:.6f} {quote_currency}")
        
        # Mark order as filled
        order['status'] = 'filled'
        order['fee'] = {'cost': fee_amount, 'currency': quote_currency}
    
    # Exchange API methods
    def fetch_balance(self):
        """Fetch account balance."""
        self._process_fills()  # Process any potential fills
        return self.balances
    
    def create_limit_buy_order(self, symbol, amount, price):
        """Create a limit buy order."""
        return self.create_limit_order(symbol, 'buy', amount, price)
    
    def create_limit_sell_order(self, symbol, amount, price):
        """Create a limit sell order."""
        return self.create_limit_order(symbol, 'sell', amount, price)
    
    def create_limit_order(self, symbol, side, amount, price):
        """Create a limit order."""
        self._process_fills()  # Process any potential fills
        
        # Get currencies
        currencies = symbol.split('/')
        base_currency = currencies[0]
        quote_currency = currencies[1]
        
        # Check if we have sufficient balance
        if side == 'buy':
            cost = amount * price
            if self.balances[quote_currency]['free'] < cost:
                raise Exception(f"Insufficient {quote_currency} balance")
            
            # Reserve the funds
            self.balances[quote_currency]['free'] -= cost
            self.balances[quote_currency]['used'] += cost
            
        elif side == 'sell':
            if self.balances[base_currency]['free'] < amount:
                raise Exception(f"Insufficient {base_currency} balance")
            
            # Reserve the funds
            self.balances[base_currency]['free'] -= amount
            self.balances[base_currency]['used'] += amount
        
        # Create order
        order_id = str(self.order_id_counter)
        self.order_id_counter += 1
        
        order = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'amount': amount,
            'price': price,
            'status': 'open',
            'timestamp': time.time()
        }
        
        self.orders[order_id] = order
        
        logger.info(f"Created {side} order {order_id}: {amount} @ {price}")
        return order
    
    def cancel_order(self, order_id, symbol=None):
        """Cancel an order."""
        if order_id in self.orders:
            order = self.orders[order_id]
            
            # Return reserved funds
            if order['side'] == 'buy':
                currencies = order['symbol'].split('/')
                quote_currency = currencies[1]
                cost = order['amount'] * order['price']
                
                self.balances[quote_currency]['free'] += cost
                self.balances[quote_currency]['used'] -= cost
                
            elif order['side'] == 'sell':
                currencies = order['symbol'].split('/')
                base_currency = currencies[0]
                
                self.balances[base_currency]['free'] += order['amount']
                self.balances[base_currency]['used'] -= order['amount']
            
            # Mark as canceled
            order['status'] = 'canceled'
            
            # Remove from active orders
            del self.orders[order_id]
            
            logger.info(f"Canceled order {order_id}")
            return order
        else:
            logger.warning(f"Order {order_id} not found to cancel")
            raise Exception(f"Order {order_id} not found")
    
    def fetch_open_orders(self, symbol=None):
        """Fetch open orders, optionally filtered by symbol."""
        self._process_fills()  # Process any potential fills
        
        if symbol is None:
            return list(self.orders.values())
        else:
            return [order for order in self.orders.values() if order['symbol'] == symbol]
    
    def fetch_ticker(self, symbol):
        """Fetch ticker with dynamic spreads based on volatility."""
        self._process_fills()  # Process any potential fills
        
        # Calculate spread as a function of volatility
        base_spread = 0.0001  # 0.1% minimum spread
        volatility_factor = self.price_volatility * 10
        dynamic_spread = base_spread + volatility_factor
        
        bid = self.current_price * (1 - dynamic_spread/2)
        ask = self.current_price * (1 + dynamic_spread/2)
        
        return {
            'symbol': symbol,
            'bid': bid,
            'ask': ask,
            'last': self.current_price,
            'timestamp': int(time.time() * 1000)
        }
    
    def fetch_ohlcv(self, symbol, timeframe='1m', limit=100):
        """Fetch OHLCV candlestick data."""
        # Return most recent candles
        end_index = len(self.historical_data)
        start_index = max(0, end_index - limit)
        
        return self.historical_data[start_index:end_index]
    
    def fetch_order_book(self, symbol, limit=20):
        """Fetch order book."""
        self._process_fills()  # Process any potential fills
        
        # Generate synthetic order book
        bids = []
        asks = []
        
        current_price = self.current_price
        
        # Generate bids (below current price)
        for i in range(limit):
            price = current_price * (0.995 - 0.001 * i)  # Start 0.5% below current price
            size = abs(np.random.normal(10, 5))
            bids.append([price, size])
        
        # Generate asks (above current price)
        for i in range(limit):
            price = current_price * (1.005 + 0.001 * i)  # Start 0.5% above current price
            size = abs(np.random.normal(10, 5))
            asks.append([price, size])
        
        return {
            'bids': bids,
            'asks': asks,
            'timestamp': int(time.time() * 1000),
            'nonce': int(time.time() * 1000)
        }