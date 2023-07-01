import json
import os
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)

from blackswan.exchanges import Bitmex as BitmexTrader

parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parent_dir)

import config

bitmex_trader = BitmexTrader(
    testnet=False,
    api_key=config.bitmex_api_key, #os.getenv("KUCOIN_API_KEY"),
    api_secret= config.bitmex_api_secret,# os.getenv("KUCOIN_API_SECRET"),
)

def bitmex_open_perpetual(buysell, rotation, symbol, amount, leverage, take_profit_percent, stop_loss_percent):
    bitmex_trader.open_trade(
        symbol,
        amount,  # minimum buy size
        rotation,
        buysell,
        leverage,
        take_profit_percent,
        stop_loss_percent,
        quantity_type="token",
        )
