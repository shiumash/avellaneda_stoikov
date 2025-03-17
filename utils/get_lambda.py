import os
import logging
import requests
import time
import json

logger = logging.getLogger('market_maker')

def get_lambdas_from_order_book(symbol, num_samples=3, interval=5):
    """
    Estimate lambda values (order arrival rates) from order book data.
    
    Args:
        symbol: Trading pair (e.g., "USDT/USD")
        num_samples: Number of order book snapshots to take
        interval: Time between snapshots in seconds
        
    Returns:
        tuple: Estimated (lambda_b, lambda_a)
    """
    # Convert symbol format for Kraken (e.g., USDT/USD -> USDTZUSD)
    formatted_symbol = symbol.replace("/", "")
    if formatted_symbol in ["USDTUSD", "USDCUSD"]:
        formatted_symbol = formatted_symbol[0:4] + "Z" + formatted_symbol[4:]
    elif formatted_symbol in ["BTCUSD", "ETHUSD"]:
        formatted_symbol = "X" + formatted_symbol[0:3] + "Z" + formatted_symbol[3:]
    
    url = f"https://api.kraken.com/0/public/Depth"
    params = {"pair": formatted_symbol, "count": 100}
    
    logger.info(f"Estimating lambda values for {symbol} from order book data...")
    
    # Take multiple samples of the order book
    snapshots = []
    for i in range(num_samples):
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'error' in data and data['error']:
                logger.error(f"Kraken API error: {data['error']}")
                continue
                
            if 'result' in data:
                # Extract the first key from results (this is the pair)
                pair_key = list(data['result'].keys())[0]
                order_book = data['result'][pair_key]
                
                # Calculate total volume and number of price levels on each side
                bid_volume = sum(float(bid[1]) for bid in order_book['bids'])
                ask_volume = sum(float(ask[1]) for ask in order_book['asks'])
                bid_levels = len(order_book['bids'])
                ask_levels = len(order_book['asks'])
                
                snapshots.append({
                    'timestamp': time.time(),
                    'bid_volume': bid_volume,
                    'ask_volume': ask_volume,
                    'bid_levels': bid_levels,
                    'ask_levels': ask_levels
                })
                
                logger.debug(f"Sample {i+1}: Bid volume={bid_volume}, Ask volume={ask_volume}")
                
            # Sleep before next sample
            if i < num_samples - 1:
                time.sleep(interval)
                
        except Exception as e:
            logger.error(f"Error fetching order book: {str(e)}")
    
    # Analyze order book depth and changes
    if len(snapshots) < 2:
        logger.warning("Not enough samples to calculate lambda values, using defaults")
        return get_default_lambdas(symbol)
    
    # Calculate average order book metrics
    avg_bid_levels = sum(s['bid_levels'] for s in snapshots) / len(snapshots)
    avg_ask_levels = sum(s['ask_levels'] for s in snapshots) / len(snapshots)
    avg_bid_volume = sum(s['bid_volume'] for s in snapshots) / len(snapshots)
    avg_ask_volume = sum(s['ask_volume'] for s in snapshots) / len(snapshots)
    
    # Calculate average rate of volume change between snapshots
    bid_rates = []
    ask_rates = []
    
    for i in range(1, len(snapshots)):
        time_diff = snapshots[i]['timestamp'] - snapshots[i-1]['timestamp']
        if time_diff > 0:
            bid_change = abs(snapshots[i]['bid_volume'] - snapshots[i-1]['bid_volume'])
            ask_change = abs(snapshots[i]['ask_volume'] - snapshots[i-1]['ask_volume'])
            
            bid_rates.append(bid_change / time_diff)
            ask_rates.append(ask_change / time_diff)
    
    # Calculate average volume change rates
    avg_bid_rate = sum(bid_rates) / len(bid_rates) if bid_rates else 1.0
    avg_ask_rate = sum(ask_rates) / len(ask_rates) if ask_rates else 1.0
    
    # Apply market-specific scaling factors
    # For stablecoins, we need higher lambda values for tighter spreads
    '''
    if symbol in ['USDT/USD', 'USDC/USD', 'BUSD/USD']:
        scale_factor = 10.0
    elif symbol in ['BTC/USD', 'ETH/USD']:
        scale_factor = 5.0
    else:
        scale_factor = 2.0
    '''
    
    scale_factor = 1.0
    
    # Combine depth and rate information for final lambda values
    # The formula balances order book depth with observed change rates
    lambda_b = (avg_bid_levels * 0.5 + avg_bid_rate * 2) * scale_factor
    lambda_a = (avg_ask_levels * 0.5 + avg_ask_rate * 2) * scale_factor
    
    # Ensure minimum values
    lambda_b = max(lambda_b, 5.0)
    lambda_a = max(lambda_a, 5.0)
    
    logger.info(f"Estimated lambda values for {symbol}: lambda_b={lambda_b:.2f}, lambda_a={lambda_a:.2f}")
    
    return lambda_b, lambda_a

def get_default_lambdas(symbol):
    """
    Get default lambda values based on the trading pair type.
    
    Args:
        symbol (str): The trading pair (e.g., "USDT/USD", "BTC/USD").
        
    Returns:
        tuple: (lambda_b, lambda_a)
    """
    symbol = symbol.upper()
    
    # Categorize the trading pair
    stable_pairs = {'USDT/USD', 'USDC/USD', 'BUSD/USD', 'DAI/USD'}
    major_cryptos = {'BTC/USD', 'ETH/USD', 'XRP/USD', 'BNB/USD', 'ADA/USD'}
    mid_cryptos = {'SOL/USD', 'DOT/USD', 'DOGE/USD', 'AVAX/USD', 'LINK/USD'}
    
    # Assign lambda values based on category
    if symbol in stable_pairs:
        lambda_b = float(os.getenv('AS_LAMBDA_B_STABLE', '50.0'))
        lambda_a = float(os.getenv('AS_LAMBDA_A_STABLE', '50.0'))
        logger.info(f"Using default stable pair lambdas for {symbol}: ({lambda_b}, {lambda_a})")
    elif symbol in major_cryptos:
        lambda_b = float(os.getenv('AS_LAMBDA_B_MAJOR', '15.0'))
        lambda_a = float(os.getenv('AS_LAMBDA_A_MAJOR', '15.0'))
        logger.info(f"Using default major crypto lambdas for {symbol}: ({lambda_b}, {lambda_a})")
    elif symbol in mid_cryptos:
        lambda_b = float(os.getenv('AS_LAMBDA_B_MID', '7.5'))
        lambda_a = float(os.getenv('AS_LAMBDA_A_MID', '7.5'))
        logger.info(f"Using default mid-cap crypto lambdas for {symbol}: ({lambda_b}, {lambda_a})")
    else:
        lambda_b = float(os.getenv('AS_LAMBDA_B_DEFAULT', '5.0'))
        lambda_a = float(os.getenv('AS_LAMBDA_A_DEFAULT', '5.0'))
        logger.info(f"Using default lambdas for {symbol}: ({lambda_b}, {lambda_a})")
    
    return lambda_b, lambda_a

def get_lambdas(symbol, use_order_book=True):
    """
    Get lambda_b and lambda_a values based on the trading pair.
    First tries to estimate from order book data if use_order_book=True.
    Falls back to default values if estimation fails or use_order_book=False.
    
    Args:
        symbol (str): The trading pair (e.g., "USDT/USD", "BTC/USD").
        use_order_book (bool): Whether to use order book data for estimation.
        
    Returns:
        tuple: (lambda_b, lambda_a)
    """
    if use_order_book:
        try:
            return get_lambdas_from_order_book(symbol)
        except Exception as e:
            logger.warning(f"Failed to estimate lambdas from order book: {e}")
            logger.warning("Falling back to default lambda values.")
    
    return get_default_lambdas(symbol)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # Example test runs
    pairs = ['USDT/USD', 'BTC/USD', 'ETH/USD']
    for pair in pairs:
        print(f"\nEstimating lambdas for {pair}...")
        lb, la = get_lambdas(pair)
        print(f"{pair}: Lambda_b = {lb:.2f}, Lambda_a = {la:.2f}")