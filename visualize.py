"""
Visualization functions for analyzing market maker performance.
"""
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import numpy as np
from datetime import datetime
import os

def create_result_visualizations(position_history, trade_history, output_dir="results"):
    """
    Create performance visualizations based on trading history.
    
    Args:
        position_history (pd.DataFrame): Position history dataframe
        trade_history (pd.DataFrame): Trade history dataframe
        output_dir (str): Directory to save visualization plots
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Generate timestamp for this run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Only proceed if we have position data
    if position_history.empty:
        print("No position history data to visualize")
        return
    
    # Convert timestamp to datetime if it's not already
    if not isinstance(position_history.index, pd.DatetimeIndex):
        position_history['timestamp'] = pd.to_datetime(position_history['timestamp'], unit='s')
        position_history.set_index('timestamp', inplace=True)
    
    # Set plot style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # 1. Portfolio Value Over Time
    plt.figure(figsize=(12, 6))
    plt.plot(position_history.index, position_history['total_value'], linewidth=2)
    plt.title('Portfolio Value Over Time')
    plt.xlabel('Time')
    plt.ylabel('Portfolio Value')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/portfolio_value_{timestamp}.png")
    
    # 2. Base and Quote Currency Balances
    plt.figure(figsize=(12, 6))
    
    # Create two y-axes
    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()
    
    # Plot base balance
    ax1.plot(position_history.index, position_history['base_balance'], 'b-', linewidth=2, label='Base Balance')
    ax1.set_xlabel('Time')
    ax1.set_ylabel('Base Balance', color='b')
    ax1.tick_params(axis='y', labelcolor='b')
    
    # Plot quote balance
    ax2.plot(position_history.index, position_history['quote_balance'], 'r-', linewidth=2, label='Quote Balance')
    ax2.set_ylabel('Quote Balance', color='r')
    ax2.tick_params(axis='y', labelcolor='r')
    
    # Add legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')
    
    plt.title('Currency Balances Over Time')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/currency_balances_{timestamp}.png")
    
    # 3. Inventory Percentage Over Time
    plt.figure(figsize=(12, 6))
    plt.plot(position_history.index, position_history['inventory_pct'] * 100, linewidth=2)
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.title('Inventory Percentage Over Time')
    plt.xlabel('Time')
    plt.ylabel('Inventory %')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/inventory_percentage_{timestamp}.png")
    
    # 4. Price Movement
    plt.figure(figsize=(12, 6))
    plt.plot(position_history.index, position_history['mid_price'], linewidth=2)
    plt.title('Mid Price Over Time')
    plt.xlabel('Time')
    plt.ylabel('Price')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/mid_price_{timestamp}.png")
    
    # 5. Price and Trades Visualization (if we have trade history)
    if not trade_history.empty:
        if not isinstance(trade_history.index, pd.DatetimeIndex):
            trade_history['timestamp'] = pd.to_datetime(trade_history['timestamp'], unit='s')
            trade_history.set_index('timestamp', inplace=True)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot price
        ax.plot(position_history.index, position_history['mid_price'], linewidth=2, label='Mid Price')
        
        # Plot buy trades
        buy_trades = trade_history[trade_history['side'] == 'buy']
        if not buy_trades.empty:
            ax.scatter(buy_trades.index, buy_trades['executed_price'], color='green', s=50, marker='^', label='Buy')
        
        # Plot sell trades
        sell_trades = trade_history[trade_history['side'] == 'sell']
        if not sell_trades.empty:
            ax.scatter(sell_trades.index, sell_trades['executed_price'], color='red', s=50, marker='v', label='Sell')
        
        plt.title('Price Movement and Trades')
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"{output_dir}/price_and_trades_{timestamp}.png")
    
    # 6. Cumulative P&L
    plt.figure(figsize=(12, 6))
    initial_value = position_history['total_value'].iloc[0]
    position_history['pnl'] = position_history['total_value'] - initial_value
    position_history['pnl_pct'] = (position_history['total_value'] / initial_value - 1) * 100
    
    plt.plot(position_history.index, position_history['pnl'], linewidth=2)
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.title('Cumulative P&L')
    plt.xlabel('Time')
    plt.ylabel('P&L')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cumulative_pnl_{timestamp}.png")
    
    # 7. P&L Percentage
    plt.figure(figsize=(12, 6))
    plt.plot(position_history.index, position_history['pnl_pct'], linewidth=2)
    plt.axhline(y=0, color='r', linestyle='-', alpha=0.3)
    plt.title('Cumulative P&L %')
    plt.xlabel('Time')
    plt.ylabel('P&L %')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/cumulative_pnl_pct_{timestamp}.png")
    
    print(f"Visualizations saved to {output_dir} directory")