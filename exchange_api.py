import ccxt
import logging
from config import BINANCE_MARKET_RULES

exchange = ccxt.binance({
    'enableRateLimit': True,
})

def get_prices(symbols=None):
    data = {}
    for symbol in symbols:
        try:
            ticker = exchange.fetch_ticker(symbol)
            price = ticker['last']
            volume = ticker['quoteVolume']
            bid = ticker['bid']
            ask = ticker['ask']
            data[symbol] = {
                "price": price,
                "volume": volume,
                "bid": bid,
                "ask": ask
            }
        except Exception as e:
            logging.warning(f"Failed to fetch ticker for {symbol}: {e}")
    return data

def get_symbol_info(symbol):
    return BINANCE_MARKET_RULES.get(symbol, {
        "price": {"precision": 4},
        "amount": {"precision": 6, "min": 0.00001},
        "notional": {"min": 10.0}
    })

def quantize_quantity(symbol, quantity):
    rules = get_symbol_info(symbol)
    precision = rules["amount"].get("precision", 6)
    min_qty = rules["amount"].get("min", 0.0)
    quantized = round(quantity, precision)
    return max(quantized, min_qty)

def quantize_price(symbol, price):
    rules = get_symbol_info(symbol)
    precision = rules["price"].get("precision", 2)
    return round(price, precision)

def check_min_notional(symbol, price, quantity):
    rules = get_symbol_info(symbol)
    min_notional = rules["notional"].get("min", 10.0)
    return (price * quantity) >= min_notional