DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]

AI_RISK_LEVEL_THRESHOLDS = {
    "aggressive": 0.00005,
    "moderate": 0.0005,
    "conservative": 0.001
}
AI_RISK_POSITION_LIMITS = {
    "aggressive": 0.6,
    "moderate": 0.4,
    "conservative": 0.2
}
AI_HISTORY_LIMIT = 14

INITIAL_BALANCE = 1000.0

BINANCE_MARKET_RULES = {
    "BTC/USDT": {
        "price": {"precision": 2},
        "amount": {"precision": 6, "min": 0.00001},
        "notional": {"min": 10.0}
    },
    "ETH/USDT": {
        "price": {"precision": 2},
        "amount": {"precision": 5, "min": 0.0001},
        "notional": {"min": 10.0}
    },
    "BNB/USDT": {
        "price": {"precision": 2},
        "amount": {"precision": 3, "min": 0.01},
        "notional": {"min": 10.0}
    },
    "ADA/USDT": {
        "price": {"precision": 4},
        "amount": {"precision": 0, "min": 1.0},
        "notional": {"min": 10.0}
    },
    "SOL/USDT": {
        "price": {"precision": 2},
        "amount": {"precision": 3, "min": 0.01},
        "notional": {"min": 10.0}
    }
}

LOG_LEVEL = "INFO"
LOG_FILE = "trade_log.log"