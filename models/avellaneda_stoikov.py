"""
Implementation of the simplified Avellaneda-Stoikov model for market making.
"""
import numpy as np
import logging
from config.settings import GAMMA, LAMBDA_A, LAMBDA_B

logger = logging.getLogger('market_maker')

class AvellanedaStoikov:
    """
    A simplified implementation of the Avellaneda-Stoikov market making model.
    """
    
    def __init__(self, gamma=GAMMA, lambda_b=LAMBDA_B, lambda_a=LAMBDA_A):
        """
        Initialize the Avellaneda-Stoikov model.
        
        Args:
            gamma (float): Risk aversion parameter
            lambda_b (float): Arrival rate of buy orders
            lambda_a (float): Arrival rate of sell orders
        """
        self.gamma = gamma
        self.lambda_b = lambda_b
        self.lambda_a = lambda_a
        logger.info(f"Initialized A-S model with gamma={gamma}, lambda_b={lambda_b}, lambda_a={lambda_a}")
        
    def calculate_bid_spread(self, volatility, inventory):
        """
        Calculate the bid spread using the simplified A-S model.
        
        Args:
            volatility (float): Market volatility
            inventory (float): Current inventory position
            
        Returns:
            float: Bid spread
        """
        # Based on the formula: δ_bid = (1/γ) * ln(1 + (γ/λ_b)) + 0.5 * γ * σ^2 * (q+1)^2
        first_term = (1 / self.gamma) * np.log(1 + (self.gamma / self.lambda_b))
        second_term = 0.5 * self.gamma * (volatility ** 2) * ((inventory + 1) ** 2)
        
        spread = first_term + second_term
        logger.debug(f"Calculated bid spread: {spread} (vol: {volatility}, inv: {inventory})")
        return spread
        
    def calculate_ask_spread(self, volatility, inventory):
        """
        Calculate the ask spread using the simplified A-S model.
        
        Args:
            volatility (float): Market volatility
            inventory (float): Current inventory position
            
        Returns:
            float: Ask spread
        """
        # Based on the formula: δ_ask = (1/γ) * ln(1 + (γ/λ_a)) + 0.5 * γ * σ^2 * (q-1)^2
        first_term = (1 / self.gamma) * np.log(1 + (self.gamma / self.lambda_a))
        second_term = 0.5 * self.gamma * (volatility ** 2) * ((inventory - 1) ** 2)
        
        spread = first_term + second_term
        logger.debug(f"Calculated ask spread: {spread} (vol: {volatility}, inv: {inventory})")
        return spread
        
    def calculate_spreads(self, mid_price, volatility, inventory):
        """
        Calculate the bid and ask prices based on the current market state.
        
        Args:
            mid_price (float): Current mid-price
            volatility (float): Market volatility
            inventory (float): Current inventory position
            
        Returns:
            tuple: (bid_price, ask_price)
        """
        bid_spread = self.calculate_bid_spread(volatility, inventory)
        ask_spread = self.calculate_ask_spread(volatility, inventory)
        
        bid_price = mid_price - bid_spread
        ask_price = mid_price + ask_spread
        
        logger.info(f"A-S Model - Mid: {mid_price:.6f}, Bid: {bid_price:.6f}, Ask: {ask_price:.6f}")
        return bid_price, ask_price