"""
Utilities for calculating market volatility.
"""
import numpy as np
import pandas as pd
import logging
from config.settings import VOLATILITY_WINDOW, VOLATILITY_STD_DEV, TIMEFRAME

logger = logging.getLogger('market_maker')

def calculate_standard_deviation(prices, window=VOLATILITY_WINDOW):
    """
    Calculate rolling standard deviation of prices.
    
    Args:
        prices (array-like): Price series
        window (int): Window size for calculation
        
    Returns:
        float: Standard deviation of prices over the window
    """
    if len(prices) < window:
        logger.warning(f"Not enough data for volatility calculation. Need {window}, have {len(prices)}")
        return None
        
    # Calculate standard deviation over the window
    std_dev = np.std(prices[-window:])
    logger.debug(f"Calculated std dev: {std_dev:.6f} over {window} periods")
    return std_dev
    
def calculate_bollinger_bands(df, column='close', window=VOLATILITY_WINDOW, num_std=VOLATILITY_STD_DEV):
    """
    Calculate Bollinger Bands for a price series.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        column (str): Column name to use for calculations
        window (int): Window size for moving average
        num_std (float): Number of standard deviations
        
    Returns:
        pd.DataFrame: DataFrame with Bollinger Bands
    """
    if len(df) < window:
        logger.warning(f"Not enough data for Bollinger Bands. Need {window}, have {len(df)}")
        return None
        
    # Make a copy to avoid modifying the original
    result = df.copy()
    
    # Calculate rolling mean and standard deviation
    result['bb_middle'] = result[column].rolling(window=window).mean()
    result['bb_std'] = result[column].rolling(window=window).std()
    
    # Calculate upper and lower bands
    result['bb_upper'] = result['bb_middle'] + (result['bb_std'] * num_std)
    result['bb_lower'] = result['bb_middle'] - (result['bb_std'] * num_std)
    
    # Calculate bandwidth and %B
    result['bb_bandwidth'] = (result['bb_upper'] - result['bb_lower']) / result['bb_middle']
    result['bb_percent_b'] = (result[column] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'])
    
    logger.debug(f"Calculated Bollinger Bands with window={window}, num_std={num_std}")
    return result
    
def get_volatility_from_bollinger(df, window=VOLATILITY_WINDOW, num_std=VOLATILITY_STD_DEV):
    """
    Extract volatility estimate from Bollinger Bands.
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        window (int): Window size for calculation
        num_std (float): Number of standard deviations
        
    Returns:
        float: Volatility estimate
    """
    bb_df = calculate_bollinger_bands(df, window=window, num_std=num_std)
    
    if bb_df is None or bb_df.empty:
        return None
        
    # Get the most recent standard deviation
    volatility = bb_df['bb_std'].iloc[-1]
    
    # Annualize the volatility (adjust based on your timeframe)
    # For example, if using minute data: sqrt(365 * 24 * 60)
    # For daily data: sqrt(365)
    # annualized_vol = volatility * np.sqrt(365 * 24 * 60)
    
    logger.info(f"Current volatility estimate: {volatility:.6f}")
    return volatility
    
def detect_volatility_regime(df, column='close', window=VOLATILITY_WINDOW, lookback=100):
    """
    Detect the current volatility regime (high/medium/low).
    
    Args:
        df (pd.DataFrame): DataFrame with price data
        column (str): Column name to use for calculations
        window (int): Window size for volatility calculation
        lookback (int): Lookback period for regime detection
        
    Returns:
        str: Current volatility regime ('high', 'medium', or 'low')
    """
    if len(df) < lookback:
        logger.warning(f"Not enough data for regime detection. Need {lookback}, have {len(df)}")
        return "medium"
        
    # Calculate rolling volatility
    rolling_vol = df[column].rolling(window=window).std()
    
    if len(rolling_vol) < lookback:
        return "medium"
        
    # Get recent volatility
    current_vol = rolling_vol.iloc[-1]
    
    # Calculate percentiles for the historical volatility
    vol_history = rolling_vol.iloc[-lookback:]
    low_threshold = vol_history.quantile(0.25)
    high_threshold = vol_history.quantile(0.75)
    
    # Determine regime
    if current_vol < low_threshold:
        regime = "low"
    elif current_vol > high_threshold:
        regime = "high"
    else:
        regime = "medium"
        
    logger.info(f"Current volatility regime: {regime} (vol: {current_vol:.6f})")
    return regime

def get_realized_volatility(market_data: pd.DataFrame, window: int = 20) -> float:
    """
    Calculate realized volatility from high-frequency returns.
    
    Args:
        market_data: DataFrame with OHLCV data
        window: Number of periods to include
    
    Returns:
        float: Realized volatility as a decimal
    """
    # Calculate log returns
    market_data['log_returns'] = np.log(market_data['close'] / market_data['close'].shift(1))
    
    # Square the returns
    market_data['squared_returns'] = market_data['log_returns'] ** 2
    
    # Sum the squared returns over the window
    realized_variance = market_data['squared_returns'].rolling(window=window).sum()
    
    # Take the square root to get volatility (annualize if needed)
    # For 1-minute data, annualization factor would be sqrt(365*24*60)
    # For daily data, it would be sqrt(365)
    annualization_factor = np.sqrt(365) if TIMEFRAME == '1d' else 1
    realized_vol = np.sqrt(realized_variance.iloc[-1]) * annualization_factor
    
    return float(realized_vol)