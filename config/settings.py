"""
Configuration settings for the market making bot.
Load sensitive information from environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Configuration
API_KEY = os.getenv('KRAKEN_API_KEY')
API_SECRET = os.getenv('KRAKEN_API_SECRET')

# Trading Configuration
SYMBOL = os.getenv('TRADING_SYMBOL', 'USDT/USD')  # Default to USDT/USD
TIMEFRAME = os.getenv('TIMEFRAME', '1m')          # Default to 1-minute intervals

# Order Configuration
BASE_ORDER_SIZE = float(os.getenv('BASE_ORDER_SIZE', '5'))  # Size of orders in base currency

# Risk Configuration
MAX_INVENTORY_PCT = float(os.getenv('MAX_INVENTORY_PCT', '0.35'))  # Maximum inventory as percentage
CIRCUIT_BREAKER_PCT = float(os.getenv('CIRCUIT_BREAKER_PCT', '0.2'))  # Price change to trigger circuit breaker
INVENTORY_SKEW_THRESHOLD = float(os.getenv('INVENTORY_SKEW_THRESHOLD', '0.20'))  # Threshold for inventory adjustment

# Volatility Configuration
VOLATILITY_WINDOW = int(os.getenv('VOLATILITY_WINDOW', '20'))  # Window for volatility calculation
VOLATILITY_STD_DEV = float(os.getenv('VOLATILITY_STD_DEV', '2.0'))  # Number of standard deviations

# Avellaneda-Stoikov Parameters
GAMMA = float(os.getenv('AS_GAMMA', '0.001'))  # Risk aversion parameter - higher it, the more risk-averse

# Handle empty lambda values properly
lambda_b_env = os.getenv('AS_LAMBDA_B')
LAMBDA_B = float(lambda_b_env) if lambda_b_env else 397.57  # Arrival rate of buy orders

lambda_a_env = os.getenv('AS_LAMBDA_A') 
LAMBDA_A = float(lambda_a_env) if lambda_a_env else 1442.46  # Arrival rate of sell orders

# Execution Configuration
if (SYMBOL.split('/')[0] in ['USDT', 'USDC', 'DAI', 'BUSD']):
    TIMEFRAME = os.getenv('TIMEFRAME', '5m')
    CYCLE_TIME = int(os.getenv('CYCLE_TIME', '300'))  # Seconds between trading cycles
else:
    TIMEFRAME = os.getenv('TIMEFRAME', '1m')
    CYCLE_TIME = int(os.getenv('CYCLE_TIME', '60'))