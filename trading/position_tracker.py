"""
Tracking of positions and inventory over time.
"""
import pandas as pd
import logging
import time

logger = logging.getLogger('market_maker')

class PositionTracker:
    """
    Class for tracking trading positions and performance over time.
    """
    
    def __init__(self):
        """Initialize the position tracker."""
        self.positions = []  # List to store position snapshots
        self.trades = []     # List to store executed trades
        
    def record_position(self, base_balance, quote_balance, mid_price):
        """
        Record a position snapshot.
        
        Args:
            base_balance (float): Current base currency balance
            quote_balance (float): Current quote currency balance
            mid_price (float): Current mid-price
        """
        timestamp = time.time()
        
        # Calculate portfolio value
        base_value = base_balance * mid_price
        total_value = base_value + quote_balance
        
        # Create position record
        position = {
            'timestamp': timestamp,
            'base_balance': base_balance,
            'quote_balance': quote_balance,
            'mid_price': mid_price,
            'base_value': base_value,
            'total_value': total_value,
            'inventory_pct': (base_value / total_value if total_value > 0 else 0)
        }
        
        self.positions.append(position)
        logger.debug(f"Recorded position: base={base_balance}, quote={quote_balance}, value={total_value:.2f}")
        
    def record_trade(self, order_info, executed_price, executed_amount):
        """
        Record an executed trade.
        
        Args:
            order_info (dict): Order information
            executed_price (float): Execution price
            executed_amount (float): Execution amount
        """
        timestamp = time.time()
        
        # Create trade record
        trade = {
            'timestamp': timestamp,
            'order_id': order_info.get('id', 'unknown'),
            'side': order_info.get('side', 'unknown'),
            'price': executed_price,
            'amount': executed_amount,
            'value': executed_price * executed_amount
        }
        
        self.trades.append(trade)
        logger.info(f"Recorded trade: {trade['side']} {trade['amount']} @ {trade['price']:.6f}")
        
    def get_position_history(self):
        """
        Get position history as a DataFrame.
        
        Returns:
            pd.DataFrame: Position history
        """
        if not self.positions:
            return pd.DataFrame()
            
        df = pd.DataFrame(self.positions)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        return df
        
    def get_trade_history(self):
        """
        Get trade history as a DataFrame.
        
        Returns:
            pd.DataFrame: Trade history
        """
        if not self.trades:
            return pd.DataFrame()
            
        df = pd.DataFrame(self.trades)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
        df.set_index('timestamp', inplace=True)
        return df
        
    def calculate_pnl(self, initial_base, initial_quote, initial_price, 
                     current_base, current_quote, current_price):
        """
        Calculate profit and loss.
        
        Args:
            initial_base (float): Initial base currency balance
            initial_quote (float): Initial quote currency balance
            initial_price (float): Initial price
            current_base (float): Current base currency balance
            current_quote (float): Current quote currency balance
            current_price (float): Current price
            
        Returns:
            dict: PnL information
        """
        # Calculate current portfolio value in quote currency
        current_value = current_base * current_price + current_quote
        
        # Calculate absolute and percentage PnL
        absolute_pnl = current_value - initial_value
        percentage_pnl = (absolute_pnl / initial_value) * 100 if initial_value > 0 else 0
        
        # Create PnL record
        pnl_info = {
            'initial_value': initial_value,
            'current_value': current_value,
            'absolute_pnl': absolute_pnl,
            'percentage_pnl': percentage_pnl,
            'timestamp': time.time()
        }
        
        logger.info(f"PnL: {absolute_pnl:.2f} ({percentage_pnl:.2f}%)")
        return pnl_info
        
    def get_daily_summary(self):
        """
        Get a summary of daily trading activity.
        
        Returns:
            dict: Daily summary
        """
        if not self.trades:
            return {}
            
        trades_df = self.get_trade_history()
        
        # Resample to daily frequency
        daily_trades = trades_df.resample('D').agg({
            'value': 'sum',
            'amount': 'sum',
            'order_id': 'count'
        })
        
        daily_trades.rename(columns={'order_id': 'num_trades'}, inplace=True)
        
        # Calculate average price per day
        daily_trades['avg_price'] = daily_trades['value'] / daily_trades['amount']
        
        # Convert to dictionary for easy access
        return daily_trades.to_dict(orient='index')