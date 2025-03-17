"""
Management of inventory positions and adjustments for risk.
"""
import logging
from config.settings import MAX_INVENTORY_PCT, INVENTORY_SKEW_THRESHOLD

logger = logging.getLogger('market_maker')

class InventoryManager:
    """
    Class for managing inventory and adjusting spreads based on inventory skew.
    """
    
    def __init__(self, max_inventory_pct=MAX_INVENTORY_PCT, skew_threshold=INVENTORY_SKEW_THRESHOLD):
        """
        Initialize the inventory manager.
        
        Args:
            max_inventory_pct (float): Maximum allowed inventory as a percentage
            skew_threshold (float): Threshold percentage for inventory adjustment
        """
        self.max_inventory_pct = max_inventory_pct
        self.skew_threshold = skew_threshold
        self.current_inventory = 0
        self.base_balance = 0
        logger.info(f"Initialized inventory manager with max pct: {max_inventory_pct}, threshold: {skew_threshold}")
        
    def update_inventory(self, base_balance, quote_balance, mid_price):
        """
        Update the current inventory position.
        
        Args:
            base_balance (float): Current base currency balance
            quote_balance (float): Current quote currency balance
            mid_price (float): Current mid-price
            
        Returns:
            float: Current inventory as a percentage (-1.0 to 1.0)
        """
        # Calculate total portfolio value in quote currency
        portfolio_value = base_balance * mid_price + quote_balance
        
        # Calculate inventory percentage (-1.0 to 1.0)
        if portfolio_value > 0:
            base_value = base_balance * mid_price
            self.current_inventory = (2 * base_value / portfolio_value) - 1
        else:
            self.current_inventory = 0
            
        self.base_balance = base_balance
        
        logger.info(f"Updated inventory: {self.current_inventory:.4f} (base: {base_balance}, quote: {quote_balance})")
        return self.current_inventory
        
    def adjust_spreads(self, base_spread, inventory_pct=None):
        """
        Adjust spreads based on inventory skew to actively correct imbalances.
        
        Args:
            base_spread (tuple): Base (bid_spread, ask_spread) before adjustment
            inventory_pct (float, optional): Current inventory percentage or use stored value
            
        Returns:
            tuple: Adjusted (bid_spread, ask_spread)
        """
        if inventory_pct is None:
            inventory_pct = self.current_inventory
            
        bid_spread, ask_spread = base_spread
        
        # No adjustment needed if inventory is balanced
        if abs(inventory_pct) <= self.skew_threshold:
            return bid_spread, ask_spread
            
        # Calculate adjustment factor based on inventory skew
        adjustment_factor = max(0, (abs(inventory_pct) - self.skew_threshold) / 
                               (self.max_inventory_pct - self.skew_threshold))
        adjustment_factor = min(adjustment_factor, 0.8)  # Cap at 0.8 to maintain some spread
        
        # Apply adjustments based on inventory direction
        if inventory_pct > 0:  # Too much base currency
            # Make ask more aggressive (lower) to sell base, make bid less aggressive (higher)
            adjusted_bid = bid_spread * (1 + adjustment_factor * 0.5)  # Moderate widening of bid
            adjusted_ask = ask_spread * max(0.2, 1 - adjustment_factor)  # More aggressive narrowing of ask
        else:  # Too little base currency
            # Make bid more aggressive (lower) to buy base, make ask less aggressive (higher)
            adjusted_bid = bid_spread * max(0.2, 1 - adjustment_factor)  # More aggressive narrowing of bid
            adjusted_ask = ask_spread * (1 + adjustment_factor * 0.5)  # Moderate widening of ask
        
        # Ensure minimum spread is maintained
        min_spread = min(bid_spread, ask_spread) * 0.1  # 10% of original spread as minimum
        adjusted_bid = max(adjusted_bid, min_spread)
        adjusted_ask = max(adjusted_ask, min_spread)
            
        logger.info(f"Spread adjustment: inventory={inventory_pct:.4f}, factor={adjustment_factor:.4f}")
        logger.info(f"Spreads before: bid={bid_spread:.6f}, ask={ask_spread:.6f}")
        logger.info(f"Spreads after: bid={adjusted_bid:.6f}, ask={adjusted_ask:.6f}")
        
        return adjusted_bid, adjusted_ask
        
    def is_inventory_balanced(self):
        """
        Check if
         inventory is within acceptable limits.
        
        Returns:
            bool: True if inventory is balanced, False otherwise
        """
        return abs(self.current_inventory) <= self.max_inventory_pct
        
    def get_rebalance_amount(self, mid_price):
        """
        Calculate the amount needed to rebalance inventory.
        
        Args:
            mid_price (float): Current mid-price
            
        Returns:
            tuple: (side, amount) where side is 'buy' or 'sell'
        """
        if abs(self.current_inventory) <= self.skew_threshold:
            return None, 0
            
        # Calculate the excess inventory in the base currency
        excess_pct = abs(self.current_inventory) - self.skew_threshold
        excess_amount = excess_pct * self.base_balance
        
        # Determine side
        side = 'sell' if self.current_inventory > 0 else 'buy'
        
        logger.info(f"Rebalance suggested: {side} {excess_amount:.6f} units")
        return side, excess_amount