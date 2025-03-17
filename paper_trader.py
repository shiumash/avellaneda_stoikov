"""
Paper trading simulation for the market making bot.
"""
import time
import logging
from datetime import datetime

# Import configuration
from config import setup_logging
from config.settings import (
    SYMBOL, TIMEFRAME, CYCLE_TIME, VOLATILITY_WINDOW
)

# Import modules
from models.avellaneda_stoikov import AvellanedaStoikov
from risk.circuit_breakers import CircuitBreakers
from risk.inventory_manager import InventoryManager
from trading.order_manager import OrderManager
from trading.position_tracker import PositionTracker
from utils.volatility import get_realized_volatility
from utils.clear_dir import clear_dir
from tests.mocks.MockExchange import MockExchange
from visualize import create_result_visualizations
import pandas as pd
from main import market_making_cycle
from utils.volatility import get_realized_volatility

# Setup logging
logger = setup_logging()

class MockExchangeData:
    """Mock implementation of ExchangeData that uses MockExchange."""
    
    def __init__(self):
        """Initialize with mock exchange."""
        self.exchange_id = 'mock'
        
        # Extract the base and quote currencies
        base_currency = SYMBOL.split('/')[0]
        quote_currency = SYMBOL.split('/')[1]
        
        # Choose appropriate initial price and volatility based on pair type
        is_stablecoin = base_currency in ['USDT', 'USDC', 'DAI', 'BUSD']
        initial_price = 1.0 if is_stablecoin else 10000.0
        
        # Use much lower volatility for stablecoins
        price_volatility = 0.001 if is_stablecoin else 0.01
        
        self.exchange = MockExchange(
            initial_balances={
                base_currency: {'free': 1000.0, 'used': 0.0, 'total': 1000.0},
                quote_currency: {'free': 10000.0, 'used': 0.0, 'total': 10000.0}
            },
            initial_price=initial_price,
            price_volatility=price_volatility
        )
        logger.info(f"Initialized mock exchange with price: {initial_price}, volatility: {price_volatility}")
    
    def fetch_ohlcv(self, symbol, timeframe='1m', limit=60):
        """Fetch OHLCV data from the mock exchange."""
        try:
            bars = self.exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
            
            # Convert to DataFrame
            import pandas as pd
            df = pd.DataFrame(bars, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
        except Exception as e:
            logger.error(f"Error fetching mock OHLCV data: {e}")
            return None
    
    def fetch_ticker(self, symbol):
        """Fetch ticker information from the mock exchange."""
        try:
            return self.exchange.fetch_ticker(symbol)
        except Exception as e:
            logger.error(f"Error fetching mock ticker: {e}")
            return None
    
    def fetch_order_book(self, symbol, limit=20):
        """Fetch order book from the mock exchange."""
        try:
            return self.exchange.fetch_order_book(symbol, limit)
        except Exception as e:
            logger.error(f"Error fetching mock order book: {e}")
            return None

def initialize_paper_trading():
    """Initialize the bot components for paper trading."""
    logger.info("Starting market making bot in paper trading mode")

    # Initialize exchange connection
    exchange_data = MockExchangeData()
    
    # Initialize trading components
    order_manager = OrderManager(exchange_data.exchange, SYMBOL)
    position_tracker = PositionTracker()
    
    # Initialize risk management components
    circuit_breakers = CircuitBreakers(price_change_threshold=0.2)
    
    inventory_manager = InventoryManager()
    
    # Initialize pricing model
    model = AvellanedaStoikov()
    return {
        'logger': logger,
        'exchange_data': exchange_data,
        'order_manager': order_manager,
        'position_tracker': position_tracker,
        'circuit_breakers': circuit_breakers,
        'inventory_manager': inventory_manager,
        'model': model
    }

def run_paper_trading(cycles=100):
    """
    Run paper trading simulation for a specified number of cycles.
    
    Args:
        cycles (int): Number of cycles to run
    """
    clear_dir('results')
    
    # Initialize bot components
    components = initialize_paper_trading()
    logger = components['logger']
    exchange_data = components['exchange_data']
    
    logger.info(f"Starting paper trading for {cycles} cycles")
    
    # Keep track of collected market data for better volatility estimation
    all_market_data = None
    volatility_update_frequency = 10  # Update volatility every 10 cycles
    
    try:
        # Main loop
        for i in range(cycles):
            logger.info(f"=== Paper Trading Cycle {i+1}/{cycles} ===")
            
            try:
                # Fetch latest market data
                market_data = exchange_data.fetch_ohlcv(SYMBOL, timeframe=TIMEFRAME, limit=60)
                
                # Accumulate market data for better volatility estimation
                if all_market_data is None and market_data is not None:
                    all_market_data = market_data
                elif market_data is not None:
                    all_market_data = pd.concat([all_market_data, market_data]).drop_duplicates()
                
                # Update volatility periodically once we have enough data
                if i % volatility_update_frequency == 0 and all_market_data is not None and len(all_market_data) > 20:
                    try:
                        # Calculate new volatility
                        new_volatility = get_realized_volatility(all_market_data)
                        
                        # Update the mock exchange's volatility
                        logger.info(f"Updating mock exchange volatility: {new_volatility:.6f}")
                        exchange_data.exchange.update_volatility(new_volatility)
                    except Exception as e:
                        logger.warning(f"Could not update volatility: {e}")
                
                # Execute market making cycle
                success = market_making_cycle(components)
                
                # Sleep briefly to simulate time passing
                time.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Error in paper trading cycle: {e}", exc_info=True)
                time.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Paper trading stopped by user")
    
    finally:
        # Print final results
        position_tracker = components['position_tracker']
        position_history = position_tracker.get_position_history()
        trade_history = position_tracker.get_trade_history()
        
        logger.info("=== Paper Trading Results ===")
        
        if not position_history.empty:

            try:
                logger.info("Creating performance visualizations...")
                create_result_visualizations(position_history, trade_history)
                logger.info("Visualizations created successfully")
            except Exception as e:
                logger.error(f"Error creating visualizations: {e}", exc_info=True)

            initial_value = position_history.iloc[0]['total_value']
            final_value = position_history.iloc[-1]['total_value']
            pnl_pct = ((final_value - initial_value) / initial_value) * 100
            
            logger.info(f"Initial Portfolio Value: {initial_value:.2f}")
            logger.info(f"Final Portfolio Value: {final_value:.2f}")
            logger.info(f"P&L: {final_value - initial_value:.2f} ({pnl_pct:.2f}%)")
        
        logger.info(f"Completed {len(position_history)} position records")
        logger.info(f"Executed {len(trade_history)} trades")

if __name__ == "__main__":
    run_paper_trading(cycles=1000)