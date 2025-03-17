"""
Main entry point for the market making bot.
"""
import time
import logging
from datetime import datetime

# Import configuration
from config import setup_logging
from config.settings import (
    SYMBOL, TIMEFRAME, CYCLE_TIME, VOLATILITY_WINDOW, 
    GAMMA, LAMBDA_B, LAMBDA_A 
)

# Import modules
from data.exchange_data import ExchangeData
from models.avellaneda_stoikov import AvellanedaStoikov
from risk.circuit_breakers import CircuitBreakers
from risk.inventory_manager import InventoryManager
from trading.order_manager import OrderManager
from trading.position_tracker import PositionTracker
from utils.volatility import get_realized_volatility
from utils.get_lambda import get_lambdas
from dotenv import load_dotenv, set_key
import os

def initialize():
    """Initialize the bot components."""
    logger = setup_logging()
    logger.info("Starting market making bot")

    lambda_values = update_lambda_values()
    
    # Initialize exchange connection
    exchange_data = ExchangeData()
    
    # Initialize trading components
    order_manager = OrderManager(exchange_data.exchange, SYMBOL)
    position_tracker = PositionTracker()
    
    # Initialize risk management components
    circuit_breakers = CircuitBreakers()
    inventory_manager = InventoryManager()
    
    # Initialize pricing model, using the freshly calculated lambda values if available
    if lambda_values:
        lambda_b, lambda_a = lambda_values
        model = AvellanedaStoikov(gamma=GAMMA, lambda_b=lambda_b, lambda_a=lambda_a)
    else:
        model = AvellanedaStoikov(gamma=GAMMA, lambda_b=LAMBDA_B, lambda_a=LAMBDA_A)
    
    logger.info(f"Avellaneda-Stoikov model initialized with: γ={GAMMA}, λ_b={model.lambda_b:.2f}, λ_a={model.lambda_a:.2f}")
    
    return {
        'logger': logger,
        'exchange_data': exchange_data,
        'order_manager': order_manager,
        'position_tracker': position_tracker,
        'circuit_breakers': circuit_breakers,
        'inventory_manager': inventory_manager,
        'model': model
    }

def update_lambda_values():
    """
    Calculate optimal lambda values from market data and update .env file.
    After updating .env, reload environment variables.
    
    Returns:
        tuple: (lambda_b, lambda_a) The calculated lambda values
    """
    logger = logging.getLogger('market_maker')
    logger.info(f"Calculating updated lambda values for {SYMBOL}...")
    
    try:
        # Get lambda values from order book data
        lambda_b, lambda_a = get_lambdas(SYMBOL, use_order_book=True)
        
        logger.info(f"Latest λ values: λ_b = {lambda_b:.2f}, λ_a = {lambda_a:.2f}")
        
        # Update .env file
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        set_key(env_path, 'AS_LAMBDA_B', str(lambda_b))
        set_key(env_path, 'AS_LAMBDA_A', str(lambda_a))
        
        # Reload environment variables
        load_dotenv(override=True)
        
        return lambda_b, lambda_a
        
    except Exception as e:
        logger.error(f"Error updating lambda values: {e}")
        # Return None so we'll use the values from .env or defaults
        return None

def market_making_cycle(components):
    """
    Execute a single market making cycle.
    
    Args:
        components (dict): Bot components
    
    Returns:
        bool: True if successful, False otherwise
    """
    logger = components['logger']
    exchange_data = components['exchange_data']
    order_manager = components['order_manager']
    position_tracker = components['position_tracker']
    circuit_breakers = components['circuit_breakers']
    inventory_manager = components['inventory_manager']
    model = components['model']
    
    logger.info(f"=== Market Making Cycle: {datetime.now()} ===")
    
    # 1. Fetch market data
    market_data = exchange_data.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=VOLATILITY_WINDOW*2)
    if market_data is None or market_data.empty:
        logger.warning("Failed to fetch market data")
        return False
    
    # 2. Check circuit breakers
    if circuit_breakers.check_all_circuit_breakers(market_data):
        logger.warning("Circuit breaker triggered, cancelling all orders")
        order_manager.cancel_all_orders()
        return False
    
    # 3. Calculate volatility
    volatility = get_realized_volatility(market_data)
    if volatility is None:
        logger.warning("Failed to calculate volatility")
        return False
    
    # 4. Fetch current balances
    base_balance, quote_balance = order_manager.fetch_balances()
    if base_balance is None or quote_balance is None:
        logger.warning("Failed to fetch balances")
        return False
    
    # 5. Get current mid price
    ticker = exchange_data.fetch_ticker(SYMBOL)
    if ticker is None:
        logger.warning("Failed to fetch ticker")
        return False
    
    mid_price = (ticker['bid'] + ticker['ask']) / 2 if 'bid' in ticker and 'ask' in ticker else ticker['last']
    
    # 6. Update inventory position
    inventory_pct = inventory_manager.update_inventory(base_balance, quote_balance, mid_price)
    
    # 7. Record position
    position_tracker.record_position(base_balance, quote_balance, mid_price)
    
    # 8. Calculate base spreads using the model
    bid_price, ask_price = model.calculate_spreads(mid_price, volatility, inventory_pct)
    
    # 9. Adjust spreads based on inventory
    bid_spread = mid_price - bid_price
    ask_spread = ask_price - mid_price
    adjusted_bid_spread, adjusted_ask_spread = inventory_manager.adjust_spreads((bid_spread, ask_spread), inventory_pct)
    
    # 10. Calculate final prices
    final_bid_price = mid_price - adjusted_bid_spread
    final_ask_price = mid_price + adjusted_ask_spread
    
    logger.info(f"Prices - Mid: {mid_price:.6f}, Bid: {final_bid_price:.6f}, Ask: {final_ask_price:.6f}")
    
    # 11. Update orders
    bid_order, ask_order = order_manager.update_orders(final_bid_price, final_ask_price)
    
    # 12. Log cycle summary
    logger.info(f"Cycle completed - Vol: {volatility:.6f}, Inv: {inventory_pct:.4f}")
    
    return True

def main():
    """Main function to run the market making bot."""
    # Initialize bot components
    components = initialize()
    logger = components['logger']
    
    try:
        # Main loop
        while True:
            try:
                # Execute market making cycle
                success = market_making_cycle(components)
                
                # Sleep until next cycle
                logger.debug(f"Sleeping for {CYCLE_TIME} seconds")
                time.sleep(CYCLE_TIME)
                
            except Exception as e:
                logger.error(f"Error in market making cycle: {e}", exc_info=True)
                time.sleep(CYCLE_TIME)
    
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        # Cancel all open orders
        components['order_manager'].cancel_all_orders()
    
    except Exception as e:
        logger.critical(f"Critical error: {e}", exc_info=True)
    
    finally:
        # Clean up
        logger.info("Bot shutting down")
        try:
            # Cancel all open orders on exit
            components['order_manager'].cancel_all_orders()
        except:
            pass

if __name__ == "__main__":
    main()