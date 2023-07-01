import json
import os
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)

from blackswan.exchanges import Bybit as BybitTrader


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parent_dir)

import config

bybit_trader = BybitTrader(
    testnet=False,
    api_key=config.bybit_api_key, #os.getenv("KUCOIN_API_KEY"),
    api_secret= config.bybit_api_secret,# os.getenv("KUCOIN_API_SECRET"),
)

def bybit_open_perpetual(buysell, rotation, symbol, amount, leverage,take_profit_percent, stop_loss_percent):
    try:
        bybit_trader.open_trade(
            symbol,
            amount,
            rotation,
            buysell,
            leverage,
            take_profit_percent,
            stop_loss_percent,
            quantity_type="USD",
        )
    except Exception as e:
        print(f"Error making KuCoin Trade: {e}")
