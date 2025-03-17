"""
Implementation of circuit breakers for risk management.
"""
import numpy as np
import logging
from config.settings import CIRCUIT_BREAKER_PCT

logger = logging.getLogger('market_maker')

class CircuitBreakers:
    """
    Class for implementing various circuit breakers to halt trading during adverse conditions.
    """
    
    def __init__(self, price_change_threshold=CIRCUIT_BREAKER_PCT):
        """
        Initialize circuit breakers.
        
        Args:
            price_change_threshold (float): Percentage change that triggers the circuit breaker
        """
        self.price_change_threshold = price_change_threshold
        logger.info(f"Initialized circuit breakers with price change threshold: {price_change_threshold}")
        
    def check_flash_crash(self, recent_prices, window=5):
        """
        Check for a flash crash condition.
        
        Args:
            recent_prices (array-like): Recent price data
            window (int): Window size to check for crash
            
        Returns:
            bool: True if flash crash detected, False otherwise
        """
        if len(recent_prices) < window:
            return False
            
        # Calculate percentage change over the window
        start_price = recent_prices[-window]
        current_price = recent_prices[-1]
        percent_change = (current_price - start_price) / start_price
        
        # Check if price drop exceeds threshold
        if percent_change < -self.price_change_threshold:
            logger.warning(f"Flash crash detected! Price dropped {percent_change*100:.2f}% in {window} periods")
            return True
            
        return False
        
    def check_stablecoin_depeg(self, price, peg_value=1.0, threshold=0.05):
        """
        Check if a stablecoin has depegged.
        
        Args:
            price (float): Current price
            peg_value (float): Expected peg value (default: 1.0)
            threshold (float): Deviation threshold to consider depegged
            
        Returns:
            bool: True if depegged, False otherwise
        """
        deviation = abs(price - peg_value) / peg_value
        
        if deviation > threshold:
            logger.warning(f"Stablecoin depeg detected! Price: {price:.6f}, deviation: {deviation*100:.2f}%")
            return True
            
        return False
        
    def check_abnormal_volume(self, recent_volumes, z_score_threshold=3.0):
        """
        Check for abnormally high trading volume.
        
        Args:
            recent_volumes (array-like): Recent volume data
            z_score_threshold (float): Z-score threshold for abnormal volume
            
        Returns:
            bool: True if abnormal volume detected, False otherwise
        """
        if len(recent_volumes) < 10:  # Need enough data for meaningful statistics
            return False
            
        # Calculate z-score of most recent volume
        mean_volume = np.mean(recent_volumes[:-1])
        std_volume = np.std(recent_volumes[:-1])
        
        if std_volume == 0:  # Avoid division by zero
            return False
            
        current_volume = recent_volumes[-1]
        z_score = (current_volume - mean_volume) / std_volume
        
        if z_score > z_score_threshold:
            logger.warning(f"Abnormal volume detected! Z-score: {z_score:.2f}")
            return True
            
        return False
        
    def check_all_circuit_breakers(self, recent_data):
        """
        Check all circuit breaker conditions.
        
        Args:
            recent_data (pd.DataFrame): Recent market data
            
        Returns:
            bool: True if any circuit breaker triggered, False otherwise
        """
        if recent_data is None or len(recent_data) < 10:
            logger.warning("Not enough data to check circuit breakers")
            return False
            
        # Extract relevant data
        prices = recent_data['close'].values
        volumes = recent_data['volume'].values
        current_price = prices[-1]
        
        # Check each circuit breaker
        flash_crash = self.check_flash_crash(prices)
        depeg = self.check_stablecoin_depeg(current_price)
        abnormal_volume = self.check_abnormal_volume(volumes)
        
        # Return True if any breaker is triggered
        return flash_crash or depeg or abnormal_volume