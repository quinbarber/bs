import json
import os
import sys

script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path.append(script_dir)

from blackswan.exchanges import Kucoin as KucoinTrader


parent_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, parent_dir)

import config


kucoin_trader = KucoinTrader(
    testnet=False,
    api_key=config.kucoin_api_key, #os.getenv("KUCOIN_API_KEY"),
    api_secret= config.kucoin_api_secret,# os.getenv("KUCOIN_API_SECRET"),
    api_pass=config.kucoin_api_pass#os.getenv(),
)
def kucoin_open_perpetual(buysell, rotation, symbol, amount, leverage,take_profit_percent, stop_loss_percent):
    try:
        kucoin_trader.open_trade(
        symbol,
        amount,
        rotation,
        buysell,
        leverage,
        take_profit_percent,
        stop_loss_percent,
        quantity_type="token",
    )
    except Exception as e:
        print(f"Error making KuCoin Trade: {e}")


if __name__ == "__main__":
    kucoin_open_perpetual("Buy", "linear", "DOGEUSDTM", 5000, 20, 1, None)
