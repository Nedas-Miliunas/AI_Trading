import sys
import os
import csv
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget,
    QHBoxLayout, QComboBox, QPushButton, QFileDialog, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QPalette, QBrush, QColor

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from exchange_api import get_prices
from portfolio import Portfolio
from trading_ai import TradingAI
from pathlib import Path

DEFAULT_SYMBOLS = ["BTC/USDT", "ETH/USDT", "BNB/USDT", "ADA/USDT", "SOL/USDT"]

def resource_path(relative_path):
    """ Get absolute path to resource for PyInstaller or dev """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class PriceFetcherThread(QThread):
    prices_fetched = pyqtSignal(dict)

    def __init__(self, symbols):
        super().__init__()
        self.symbols = symbols
        self.running = True

    def run(self):
        while self.running:
            try:
                prices = get_prices(self.symbols)
                if prices:
                    self.prices_fetched.emit(prices)
            except Exception:
                self.prices_fetched.emit({})
            self.msleep(1000)

    def stop(self):
        self.running = False
        self.wait()

class LiveChart(FigureCanvas):
    def __init__(self, parent=None):
        self.fig = Figure(figsize=(6, 4), dpi=100, facecolor='black')
        self.ax_price = self.fig.add_subplot(211)
        self.ax_balance = self.fig.add_subplot(212)
        super().__init__(self.fig)
        self.x_data = []
        self.price_history = {}
        self.balance_data = []
        self.profit_data = []

    def reset(self, symbols):
        self.x_data.clear()
        self.balance_data.clear()
        self.profit_data.clear()
        self.price_history = {sym: [] for sym in symbols}
        self.draw()

    def update_plot(self, x, prices, portfolio, profit):
        self.x_data.append(x)
        self.balance_data.append(portfolio.balance)
        self.profit_data.append(profit)
        for symbol, data in prices.items():
            self.price_history.setdefault(symbol, []).append(data["price"])

        for history in self.price_history.values():
            while len(history) > 100:
                history.pop(0)

        self.ax_price.clear()
        self.ax_balance.clear()

        for ax in (self.ax_price, self.ax_balance):
            ax.set_facecolor('black')
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['left'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.tick_params(axis='x', colors='white')
            ax.tick_params(axis='y', colors='white')
            ax.title.set_color('white')

        for symbol, prices_list in self.price_history.items():
            if prices_list:
                self.ax_price.plot(range(len(prices_list)), prices_list, label=symbol)

        if self.balance_data:
            self.ax_balance.plot(range(len(self.balance_data)), self.balance_data, label='Balance ($)', color='lime')
        if self.profit_data:
            self.ax_balance.plot(range(len(self.profit_data)), self.profit_data, label='Profit ($)', color='cyan')

        self.ax_price.set_title("Crypto Prices")
        self.ax_balance.set_title("Balance & Profit")
        self.ax_price.legend(loc='upper left', facecolor='black', edgecolor='white', labelcolor='white')
        self.ax_balance.legend(loc='upper left', facecolor='black', edgecolor='white', labelcolor='white')
        self.fig.tight_layout()
        self.draw()

class SciFiUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI Crypto Simulator")
        self.showFullScreen()
        self.setStyleSheet("color: #00ffcc; font-size: 14px;")
        self.set_background("assets/background.jpg")

        self.symbols = DEFAULT_SYMBOLS.copy()
        self.portfolio = Portfolio()
        self.ai = TradingAI("aggressive")

        self.trading_active = False
        self.latest_prices = {}

        self.label_prices = QLabel("Prices: ")
        self.label_balance = QLabel("Balance: ")
        self.label_status = QLabel("AI Decisions: ")
        self.label_profit = QLabel("Profit = $0.00")

        style_common = "background-color: black; color: white; padding: 4px;"
        self.label_prices.setStyleSheet(style_common)
        self.label_balance.setStyleSheet(style_common)
        self.label_status.setStyleSheet(style_common)
        self.label_profit.setStyleSheet(style_common + " font-size: 16px;")

        self.risk_dropdown = QComboBox()
        self.risk_dropdown.addItems(["aggressive", "moderate", "conservative"])
        self.risk_dropdown.currentTextChanged.connect(self.change_risk_level)
        self.risk_dropdown.setStyleSheet("""
            QComboBox { background-color: black; color: #00ffcc; border: 1px solid #00ffcc; }
            QComboBox QAbstractItemView { background-color: black; color: #00ffcc; selection-background-color: #004d40; }
        """)

        self.backtest_mode = False
        self.backtest_data = []
        self.backtest_index = 0

        self.btn_toggle_mode = QPushButton("Switch to Backtest Mode")
        self.btn_toggle_mode.clicked.connect(self.toggle_mode)
        self.btn_toggle_mode.setStyleSheet("background-color: black; color: white;")

        self.btn_load_csv = QPushButton("Load Backtest CSV")
        self.btn_load_csv.clicked.connect(self.load_backtest_csv)
        self.btn_load_csv.setEnabled(False)
        self.btn_load_csv.setStyleSheet("background-color: black; color: white;")

        self.btn_add_crypto = QPushButton("Add Crypto")
        self.btn_add_crypto.clicked.connect(self.add_crypto)
        self.btn_add_crypto.setStyleSheet("background-color: black; color: white;")

        self.btn_remove_crypto = QPushButton("Remove Selected Crypto")
        self.btn_remove_crypto.clicked.connect(self.remove_selected_crypto)
        self.btn_remove_crypto.setStyleSheet("background-color: black; color: white;")

        self.btn_minimize = QPushButton("Minimize")
        self.btn_minimize.clicked.connect(self.showMinimized)
        self.btn_minimize.setStyleSheet("background-color: black; color: white;")

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setStyleSheet("background-color: black; color: white;")

        self.btn_start_continue = QPushButton("Start Trading")
        self.btn_start_continue.clicked.connect(self.start_trading)
        self.btn_start_continue.setStyleSheet("background-color: #006400; color: white; font-weight: bold;")

        self.btn_stop = QPushButton("Stop Trading")
        self.btn_stop.clicked.connect(self.stop_trading)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold;")

        self.btn_sell_all = QPushButton("Sell All Holdings")
        self.btn_sell_all.clicked.connect(self.sell_all_holdings)
        self.btn_sell_all.setStyleSheet("background-color: #00008B; color: white; font-weight: bold;")

        window_controls_layout = QHBoxLayout()
        window_controls_layout.addStretch()
        window_controls_layout.addWidget(self.btn_minimize)
        window_controls_layout.addWidget(self.btn_close)

        self.crypto_list = QListWidget()
        self.update_crypto_list_widget()
        self.crypto_list.setFixedWidth(200)
        self.crypto_list.setStyleSheet("background-color: black; color: #00ffcc;")

        self.trade_log_list = QListWidget()
        self.trade_log_list.setFixedHeight(150)

        bg_path = resource_path("assets/background.jpg")
        bg_url = Path(bg_path).resolve().as_posix()

        self.trade_log_list.setStyleSheet(f"""
            QListWidget {{
                background-image: url("{bg_url}");
                background-repeat: no-repeat;
                background-position: center;
                background-attachment: fixed;
                background-color: transparent;
                color: #00ffcc;
            }}
        """)

        self.chart = LiveChart(self)
        self.chart.reset(self.symbols)

        risk_layout = QHBoxLayout()
        risk_label = QLabel("Risk Level:")
        risk_label.setStyleSheet("background-color: black; color: white;")
        risk_layout.addWidget(risk_label)
        risk_layout.addWidget(self.risk_dropdown)
        risk_layout.addStretch()
        risk_layout.addWidget(self.btn_toggle_mode)
        risk_layout.addWidget(self.btn_load_csv)

        trading_controls_layout = QHBoxLayout()
        trading_controls_layout.addWidget(self.btn_start_continue)
        trading_controls_layout.addWidget(self.btn_stop)
        trading_controls_layout.addWidget(self.btn_sell_all)
        trading_controls_layout.addStretch()

        crypto_manage_layout = QVBoxLayout()
        crypto_manage_layout.addWidget(QLabel("Tracked Cryptos:"))
        crypto_manage_layout.addWidget(self.crypto_list)
        crypto_manage_layout.addWidget(self.btn_add_crypto)
        crypto_manage_layout.addWidget(self.btn_remove_crypto)

        top_right_layout = QVBoxLayout()
        top_right_layout.addLayout(window_controls_layout)
        top_right_layout.addLayout(risk_layout)
        top_right_layout.addLayout(trading_controls_layout)
        top_right_layout.addWidget(self.label_prices)
        top_right_layout.addWidget(self.label_balance)
        top_right_layout.addWidget(self.label_status)
        top_right_layout.addWidget(self.label_profit)
        top_right_layout.addWidget(QLabel("Trade Log:"))
        top_right_layout.addWidget(self.trade_log_list)

        main_top_layout = QHBoxLayout()
        main_top_layout.addLayout(crypto_manage_layout)
        main_top_layout.addLayout(top_right_layout)

        main_layout = QVBoxLayout()
        main_layout.addLayout(main_top_layout)
        main_layout.addWidget(self.chart)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.counter = 0
        self.price_fetcher_thread = PriceFetcherThread(self.symbols)
        self.price_fetcher_thread.prices_fetched.connect(self.process_prices)
        self.price_fetcher_thread.start()
        self.stop_trading()

    def set_background(self, image_path):
        image_path = resource_path(image_path)
        if os.path.exists(image_path):
            self.setAutoFillBackground(True)
            palette = QPalette()
            pixmap = QPixmap(image_path)
            palette.setBrush(QPalette.Window, QBrush(pixmap.scaled(self.size(), aspectRatioMode=Qt.KeepAspectRatio)))
            self.setPalette(palette)

    def change_risk_level(self, level):
        self.ai.set_risk_level(level)

    def start_trading(self):
        if self.backtest_mode: return
        self.trading_active = True
        self.btn_start_continue.setEnabled(False)
        self.btn_start_continue.setText("Continue Trading")
        self.btn_stop.setEnabled(True)
        self.label_status.setText("AI trading is now ACTIVE.")

    def stop_trading(self):
        self.trading_active = False
        self.btn_start_continue.setEnabled(True)
        self.btn_start_continue.setText("Start Trading")
        self.btn_stop.setEnabled(False)
        self.label_status.setText("AI trading PAUSED.")

    def sell_all_holdings(self):
        if self.backtest_mode or not self.latest_prices:
            self.label_status.setText("Cannot sell, waiting for live price data...")
            return

        holdings_to_sell = self.portfolio.holdings.copy()
        sold_anything = False
        for symbol, quantity in holdings_to_sell.items():
            if quantity > 0 and symbol in self.latest_prices:
                current_price = self.latest_prices[symbol]['price']
                if self.portfolio.sell(symbol, current_price, quantity):
                    sold_anything = True

        if sold_anything:
            self.process_prices(self.latest_prices)
            self.label_status.setText("All holdings sold.")
        else:
            self.label_status.setText("No holdings to sell.")

    def toggle_mode(self):
        self.backtest_mode = not self.backtest_mode
        if self.backtest_mode:
            self.price_fetcher_thread.stop()
            self.stop_trading()
            self.btn_toggle_mode.setText("Switch to Live Mode")
            self.btn_load_csv.setEnabled(True)
            self.label_status.setText("Backtest mode. Load CSV to start.")
            self.btn_start_continue.setEnabled(False)
            self.btn_stop.setEnabled(False)
            self.btn_sell_all.setEnabled(False)
        else:
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()
            self.btn_toggle_mode.setText("Switch to Backtest Mode")
            self.btn_load_csv.setEnabled(False)
            self.btn_sell_all.setEnabled(True)
            self.stop_trading()
            self.label_status.setText("Live mode. Trading is paused.")
            self.price_fetcher_thread = PriceFetcherThread(self.symbols)
            self.price_fetcher_thread.prices_fetched.connect(self.process_prices)
            self.price_fetcher_thread.start()

    def load_backtest_csv(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open Backtest CSV", "", "CSV Files (*.csv);;All Files (*)", options=options)
        if filename:
            self.backtest_data = self.parse_backtest_csv(filename)
            self.backtest_index = 0
            self.portfolio.reset()
            self.chart.reset(self.symbols)
            self.label_status.setText(f"Loaded {len(self.backtest_data)} records. Starting backtest.")
            self.run_backtest()

    def parse_backtest_csv(self, filename):
        data, grouped = [], {}
        with open(filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                ts = row.get("timestamp")
                symbol = row.get("symbol")
                if ts not in grouped: grouped[ts] = {}
                grouped[ts][symbol] = {
                    "price": float(row.get("price", 0)),
                    "volume": float(row.get("volume", 0)),
                    "bid": float(row.get("bid", 0)),
                    "ask": float(row.get("ask", 0))
                }
        return [grouped[ts] for ts in sorted(grouped.keys())]

    def run_backtest(self):
        if not self.backtest_data: return
        self.timer = QTimer()
        self.timer.timeout.connect(self.backtest_tick)
        self.timer.start(200)

    def backtest_tick(self):
        if self.backtest_index >= len(self.backtest_data):
            self.label_status.setText("Backtest complete.")
            self.timer.stop()
            return
        prices = self.backtest_data[self.backtest_index]
        self.backtest_index += 1
        self.process_prices(prices)

    def process_prices(self, prices):
        if not prices: return

        self.latest_prices = prices
        decisions = []

        if self.backtest_mode or self.trading_active:
            for symbol in self.symbols:
                if symbol not in prices: continue
                price_data = prices[symbol]
                avg_buy_price = self.portfolio.avg_buy_price.get(symbol)

                decision, pos_size = self.ai.decide(symbol, price_data["price"], price_data["volume"], price_data["ask"] - price_data["bid"], avg_buy_price)

                if decision == "BUY" and pos_size > 0:
                    self.portfolio.buy(symbol, price_data["price"], pos_size)
                elif decision == "SELL" and pos_size > 0:
                    qty_held = self.portfolio.holdings.get(symbol, 0)
                    if qty_held > 0:
                        self.portfolio.sell(symbol, price_data["price"], qty_held * pos_size)
                decisions.append(f"{symbol}={decision}")
            if decisions:
                self.label_status.setText(" | ".join(decisions))

        profit = self.portfolio.get_profit_loss(prices)
        price_texts = []
        for sym, data in prices.items():
            if sym not in self.symbols: continue
            current_price = data['price']
            hist = self.chart.price_history.get(sym, [])
            prev_price = hist[-1] if hist else current_price
            change_pct = ((current_price - prev_price) / prev_price * 100) if prev_price != 0 else 0
            color = "#00ff00" if change_pct >= 0 else "#ff4444"
            price_texts.append(f"{sym}: ${current_price:,.2f} <span style='color:{color}'>({change_pct:+.2f}%)</span>")
        self.label_prices.setText("Prices: " + " | ".join(price_texts))
        self.label_prices.setTextFormat(Qt.RichText)

        holdings_data = self.portfolio.get_holdings_detail(prices)
        holdings_map = {h[0]: h for h in holdings_data}
        holding_strings = []
        for sym, qty, value, gain in holdings_data:
            if qty > 0:
                profit_pct = (gain / (value - gain) * 100) if (value - gain) != 0 else 0
                color = "#00ff00" if gain >= 0 else "#ff4444"
                holding_strings.append(f"<span style='color:{color}'>{sym}: {qty:.4f} (${value:,.2f})</span>")

        self.label_balance.setText(f"Balance: ${self.portfolio.balance:,.2f} | Holdings: {' | '.join(holding_strings) if holding_strings else 'None'}")
        self.label_balance.setTextFormat(Qt.RichText)

        for i in range(self.crypto_list.count()):
            item = self.crypto_list.item(i)
            sym = item.text()
            if sym in holdings_map:
                _, qty, value, gain = holdings_map[sym]
                profit_pct = (gain / (value - gain) * 100) if (value - gain) != 0 else 0
                item.setForeground(QColor("lime") if gain >= 0 else QColor("red"))
                item.setToolTip(f"Status: Held\nQuantity: {qty:.4f}\nValue: ${value:,.2f}\nAvg Buy: ${self.portfolio.avg_buy_price.get(sym,0):,.2f}\nProfit: ${gain:,.2f} ({profit_pct:+.2f}%)")
            else:
                item.setForeground(QColor("#00ffcc"))
                item.setToolTip(f"Status: Tracking (Not Held)")

        self.label_profit.setText(f"Profit = ${profit:,.2f}")

        self.trade_log_list.clear()
        for log in reversed(self.portfolio.get_trade_log()[-50:]):
            self.trade_log_list.addItem(f"{log['action']} {log['symbol']} {log['quantity']:.4f} @ ${log['price']:,.2f} | Bal: ${log['balance_after']:,.2f}")

        self.counter += 1
        self.chart.update_plot(self.counter, prices, self.portfolio, profit)

    def update_crypto_list_widget(self):
        self.crypto_list.clear()
        for sym in self.symbols:
            self.crypto_list.addItem(QListWidgetItem(sym))

    def add_crypto(self):
        text, ok = QInputDialog.getText(self, "Add Crypto Symbol", "Enter symbol (e.g. LTC/USDT):")
        if ok and text and (sym := text.strip().upper()) and sym not in self.symbols:
            self.symbols.append(sym)
            self.update_crypto_list_widget()
            self.chart.reset(self.symbols)
            if not self.backtest_mode:
                self.price_fetcher_thread.stop()
                self.price_fetcher_thread = PriceFetcherThread(self.symbols)
                self.price_fetcher_thread.prices_fetched.connect(self.process_prices)
                self.price_fetcher_thread.start()

    def remove_selected_crypto(self):
        selected_items = self.crypto_list.selectedItems()
        if not selected_items: return
        for item in selected_items:
            sym = item.text()
            if sym in self.symbols:
                self.symbols.remove(sym)
                self.portfolio.holdings.pop(sym, None)
                self.portfolio.avg_buy_price.pop(sym, None)
                for history in [self.ai.price_history, self.ai.volume_history, self.ai.spread_history]:
                    history.pop(sym, None)
        self.update_crypto_list_widget()
        self.chart.reset(self.symbols)
        if not self.backtest_mode:
            self.price_fetcher_thread.stop()
            self.price_fetcher_thread = PriceFetcherThread(self.symbols)
            self.price_fetcher_thread.prices_fetched.connect(self.process_prices)
            self.price_fetcher_thread.start()

def launch_ui():
    app = QApplication(sys.argv)
    window = SciFiUI()
    window.show()
    sys.exit(app.exec_())