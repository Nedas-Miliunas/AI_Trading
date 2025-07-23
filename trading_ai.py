import numpy as np
import datetime
import logging
from config import AI_HISTORY_LIMIT, AI_RISK_LEVEL_THRESHOLDS, AI_RISK_POSITION_LIMITS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class TradingAI:
    def __init__(self, risk_level="moderate"):
        self.price_history = {}
        self.volume_history = {}
        self.spread_history = {}
        self.decision_log = []
        self.history_limit = AI_HISTORY_LIMIT
        self.thresholds = AI_RISK_LEVEL_THRESHOLDS
        self.risk_position_limits = AI_RISK_POSITION_LIMITS
        self.current_params = {}
        self.set_risk_level(risk_level)

    def set_risk_level(self, level):
        self.risk = level.lower()
        self.threshold = self.thresholds.get(self.risk, self.thresholds["moderate"])
        self.max_position_size = self.risk_position_limits.get(self.risk, self.risk_position_limits["moderate"])
        self.current_params = {
            "buy": self.threshold,
            "sell": self.threshold,
            "max_pos": self.max_position_size
        }
        logging.info(f"AI risk level set to '{self.risk}'. Threshold: {self.threshold}, Max Position: {self.max_position_size}")

    def update_history(self, symbol, price, volume, spread):
        self.price_history.setdefault(symbol, []).append(price)
        self.volume_history.setdefault(symbol, []).append(volume)
        self.spread_history.setdefault(symbol, []).append(spread)
        for history in [self.price_history, self.volume_history, self.spread_history]:
            if len(history[symbol]) > self.history_limit:
                history[symbol].pop(0)

    def calculate_ema(self, data, span=5):
        if len(data) < span:
            return None
        return np.mean(data[-span:])

    def calculate_rsi(self, prices, period=14):
        if len(prices) < period:
            return None
        deltas = np.diff(prices[-period:])
        gains = deltas[deltas > 0].sum()
        losses = -deltas[deltas < 0].sum()
        if losses == 0:
            return 100
        rs = gains / losses
        return 100 - (100 / (1 + rs))

    def log_decision(self, symbol, action, price, pos_size, reason=""):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.decision_log.append({
            "time": timestamp,
            "symbol": symbol,
            "action": action,
            "price": price,
            "position_size_fraction": pos_size,
            "reason": reason
        })
        if action in ("BUY", "SELL"):
            logging.info(f"[{timestamp}] AI {action} {symbol} @ ${price:.2f}, pos={pos_size:.2f} - {reason}")
        else:
            logging.debug(f"[{timestamp}] AI {action} {symbol} @ ${price:.2f} - {reason}")

    def decide(self, symbol, current_price, current_volume, current_spread, avg_buy_price=None):
        if current_price <= 0 or current_volume <= 0:
            self.log_decision(symbol, "HOLD", current_price, 0, "Invalid price/volume")
            return "HOLD", 0

        self.update_history(symbol, current_price, current_volume, current_spread)
        prices = self.price_history.get(symbol, [])
        volumes = self.volume_history.get(symbol, [])

        if len(prices) < self.history_limit:
            self.log_decision(symbol, "HOLD", current_price, 0, "Insufficient history")
            return "HOLD", 0

        ema = self.calculate_ema(prices)
        rsi = self.calculate_rsi(prices)
        momentum = prices[-1] - prices[0]
        volatility = np.std(prices)
        avg_volume = np.mean(volumes)

        position_adjustment = 1.0 / (1.0 + volatility * 10 + 1e-9)
        dynamic_position_size = min(self.current_params["max_pos"], position_adjustment)

        decision = "HOLD"
        pos_size = 0
        reason = "No strong signal."

        if avg_buy_price and avg_buy_price > 0:
            stop_loss_price = avg_buy_price * 0.95
            take_profit_price = avg_buy_price * 1.10
            if current_price <= stop_loss_price:
                return "SELL", 1.0
            elif current_price >= take_profit_price:
                return "SELL", 1.0

        if ema and rsi:
            if rsi < 35 and current_price > ema:
                decision = "BUY"
                pos_size = dynamic_position_size
                reason = f"RSI={rsi:.1f} (<35), price > EMA"
            elif rsi > 65 and current_price < ema:
                decision = "SELL"
                pos_size = dynamic_position_size
                reason = f"RSI={rsi:.1f} (>65), price < EMA"

        self.log_decision(symbol, decision, current_price, pos_size, reason)
        return decision, pos_size