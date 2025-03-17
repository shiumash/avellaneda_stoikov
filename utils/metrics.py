"""
Utilities for calculating trading performance metrics.
"""
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger('market_maker')

def calculate_sharpe_ratio(returns, risk_free_rate=0.0):
    """
    Calculate the Sharpe ratio of a return series.
    
    Args:
        returns (array-like): Series of returns
        risk_free_rate (float): Risk-free rate
        
    Returns:
        float: Sharpe ratio
    """
    if len(returns) < 2:
        return None
        
    # Calculate excess returns
    excess_returns = returns - risk_free_rate
    
    # Calculate Sharpe ratio
    sharpe = np.mean(excess_returns) / np.std(excess_returns, ddof=1)
    
    # Annualize (assuming daily returns)
    annualized_sharpe = sharpe * np.sqrt(365)
    
    logger.info(f"Calculated Sharpe ratio: {annualized_sharpe:.4f}")
    return annualized_sharpe
    
def calculate_drawdown(values):
    """
    Calculate the maximum drawdown of a value series.
    
    Args:
        values (array-like): Series of portfolio values
        
    Returns:
        float: Maximum drawdown as a percentage
    """
    if len(values) < 2:
        return 0.0
        
    # Calculate drawdown series
    peak = values.expanding().max()
    drawdown = (values / peak) - 1.0
    
    # Get maximum drawdown
    max_drawdown = drawdown.min()
    
    logger.info(f"Calculated maximum drawdown: {max_drawdown*100:.2f}%")
    return max_drawdown
    
def calculate_win_rate(trades_df):
    """
    Calculate the win rate from trade history.
    
    Args:
        trades_df (pd.DataFrame): DataFrame of trade history
        
    Returns:
        float: Win rate as a percentage
    """
    if trades_df.empty:
        return 0.0
        
    # Classify trades as wins or losses
    # This assumes you have a 'pnl' column in your trades DataFrame
    if 'pnl' not in trades_df.columns:
        logger.warning("Cannot calculate win rate: 'pnl' column missing from trades DataFrame")
        return None
        
    # Count wins and total trades
    wins = (trades_df['pnl'] > 0).sum()
    total_trades = len(trades_df)
    
    # Calculate win rate
    win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0.0
    
    logger.info(f"Calculated win rate: {win_rate:.2f}% ({wins}/{total_trades})")
    return win_rate
    
def calculate_daily_returns(position_history):
    """
    Calculate daily returns from position history.
    
    Args:
        position_history (pd.DataFrame): DataFrame of position history
        
    Returns:
        pd.Series: Daily returns
    """
    if position_history.empty or 'total_value' not in position_history.columns:
        return pd.Series()
        
    # Resample to daily frequency
    daily_values = position_history['total_value'].resample('D').last()
    
    # Calculate daily returns
    daily_returns = daily_values.pct_change().dropna()
    
    logger.debug(f"Calculated {len(daily_returns)} daily returns")
    return daily_returns
    
def calculate_performance_metrics(position_history, trade_history):
    """
    Calculate comprehensive performance metrics.
    
    Args:
        position_history (pd.DataFrame): DataFrame of position history
        trade_history (pd.DataFrame): DataFrame of trade history
        
    Returns:
        dict: Performance metrics
    """
    metrics = {}
    
    if position_history.empty:
        logger.warning("Cannot calculate performance metrics: position history is empty")
        return metrics
        
    # Calculate daily returns
    daily_returns = calculate_daily_returns(position_history)
    
    if not daily_returns.empty:
        # Calculate return metrics
        metrics['total_return'] = ((position_history['total_value'].iloc[-1] / 
                                  position_history['total_value'].iloc[0]) - 1) * 100
        metrics['annualized_return'] = ((1 + metrics['total_return']/100) ** 
                                      (365 / len(daily_returns))) - 1
        metrics['volatility'] = daily_returns.std() * np.sqrt(365)
        metrics['sharpe_ratio'] = calculate_sharpe_ratio(daily_returns)
        metrics['max_drawdown'] = calculate_drawdown(position_history['total_value'])
        
    # Calculate trade metrics
    if not trade_history.empty and 'side' in trade_history.columns:
        metrics['total_trades'] = len(trade_history)
        metrics['buy_trades'] = (trade_history['side'] == 'buy').sum()
        metrics['sell_trades'] = (trade_history['side'] == 'sell').sum()
        
        # Add win rate if PnL is available
        if 'pnl' in trade_history.columns:
            metrics['win_rate'] = calculate_win_rate(trade_history)
        
    logger.info(f"Calculated performance metrics: {metrics}")
    return metrics