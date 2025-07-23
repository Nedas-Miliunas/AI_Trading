import logging
from config import INITIAL_BALANCE
from exchange_api import quantize_quantity, quantize_price, check_min_notional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class Portfolio:
    def __init__(self, initial_balance=INITIAL_BALANCE):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.holdings = {}
        self.avg_buy_price = {}
        self.trade_log = []

    def buy(self, symbol, price, position_fraction):
        max_investment_usd = self.balance * position_fraction
        
        quantized_price = quantize_price(symbol, price)

        qty_to_buy_raw = max_investment_usd / quantized_price if quantized_price > 0 else 0
        
        qty_to_buy = quantize_quantity(symbol, qty_to_buy_raw)

        cost_of_trade = quantized_price * qty_to_buy

        if not check_min_notional(symbol, quantized_price, qty_to_buy):
            logging.warning(f"SIMULATED BUY {symbol}: Investment of ${cost_of_trade:.2f} (qty={qty_to_buy:.8f}) is below simulated minimum notional. Skipping.")
            return False

        if qty_to_buy <= 0 or cost_of_trade > self.balance:
            logging.warning(f"SIMULATED BUY {symbol}: Insufficient funds or invalid quantity ({qty_to_buy:.8f}) after quantization. Cost: ${cost_of_trade:.2f}, Balance: ${self.balance:,.2f}")
            return False

        current_qty = self.holdings.get(symbol, 0)
        current_avg_price = self.avg_buy_price.get(symbol, 0)

        new_total_qty = current_qty + qty_to_buy
        new_avg_price = (
            (current_avg_price * current_qty + quantized_price * qty_to_buy) / new_total_qty
            if new_total_qty > 0 else 0
        )

        self.holdings[symbol] = new_total_qty
        self.avg_buy_price[symbol] = new_avg_price
        self.balance -= cost_of_trade

        self.trade_log.append({
            "action": "BUY",
            "symbol": symbol,
            "price": quantized_price,
            "quantity": qty_to_buy,
            "cost": cost_of_trade,
            "balance_after": self.balance
        })
        logging.info(f"SIMULATED BUY {symbol}: Bought {qty_to_buy:.8f} at ${quantized_price:,.8f}. Remaining balance: ${self.balance:,.2f}")
        return True

    def sell(self, symbol, price, quantity_to_sell_raw):
        qty_held = self.holdings.get(symbol, 0)
        if qty_held <= 0 or quantity_to_sell_raw <= 0:
            logging.debug(f"SIMULATED SELL {symbol}: No holdings or invalid quantity to sell.")
            return False

        quantized_price = quantize_price(symbol, price)

        quantity_to_sell = quantize_quantity(symbol, min(qty_held, quantity_to_sell_raw))

        if quantity_to_sell <= 0:
            logging.warning(f"SIMULATED SELL {symbol}: Quantized quantity to sell is zero. Skipping.")
            return False
        
        potential_revenue = quantized_price * quantity_to_sell
        if not check_min_notional(symbol, quantized_price, quantity_to_sell):
            logging.warning(f"SIMULATED SELL {symbol}: Sale of {quantity_to_sell:.8f} at ${quantized_price:,.8f} (${potential_revenue:.2f}) is below simulated minimum notional. Skipping.")
            return False
            
        new_qty = qty_held - quantity_to_sell
        if new_qty < 1e-9:
            new_qty = 0
            self.holdings.pop(symbol, None)
            self.avg_buy_price.pop(symbol, None)
        else:
            self.holdings[symbol] = new_qty
        
        self.balance += potential_revenue

        self.trade_log.append({
            "action": "SELL",
            "symbol": symbol,
            "price": quantized_price,
            "quantity": quantity_to_sell,
            "revenue": potential_revenue,
            "balance_after": self.balance
        })
        logging.info(f"SIMULATED SELL {symbol}: Sold {quantity_to_sell:.8f} at ${quantized_price:,.8f}. Current balance: ${self.balance:,.2f}")
        return True

    def get_holdings_detail(self, current_prices):
        details = []
        for symbol, qty in self.holdings.items():
            if qty <= 0:
                continue
            price_data = current_prices.get(symbol, {})
            price = price_data.get('price', 0)
            avg_price = self.avg_buy_price.get(symbol, 0)
            value = qty * price
            profit_loss = (price - avg_price) * qty if avg_price > 0 else 0
            details.append((symbol, qty, value, profit_loss))
        return details

    def get_profit_loss(self, current_prices):
        holdings_value = sum(
            current_prices.get(sym, {}).get('price', 0) * qty
            for sym, qty in self.holdings.items()
        )
        total_value = self.balance + holdings_value
        return total_value - self.initial_balance

    def get_trade_log(self):
        return self.trade_log

    def reset(self):
        self.balance = self.initial_balance
        self.holdings.clear()
        self.avg_buy_price.clear()
        self.trade_log.clear()
        logging.info("Portfolio reset.")