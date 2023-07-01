import json
import os

from blackswan.exchanges import Binance as BinanceTrader
from blackswan.exchanges import Bitmex as BitmexTrader
from blackswan.exchanges import Bybit as BybitTrader
from blackswan.exchanges import Kucoin as KucoinTrader

# UNCOMMENT CODE TO TEST

bybit_trader = BybitTrader(
    testnet=True,
    api_key=os.getenv("BYBIT_API_KEY"),
    api_secret=os.getenv("BYBIT_API_SECRET"),
)
binance_trader = BinanceTrader(
    testnet=True,
    api_key=os.getenv("BINANCE_API_KEY"),
    api_secret=os.getenv("BINANCE_API_SECRET"),
)
kucoin_trader = KucoinTrader(
    testnet=True,
    api_key= os.getenv("KUCOIN_API_KEY"),
    api_secret= os.getenv("KUCOIN_API_SECRET"),
    api_pass="7535753")#os.getenv()
bitmex_trader = BitmexTrader(
    testnet=True,
    api_key=os.getenv("BITMEX_API_KEY"),
    api_secret=os.getenv("BITMEX_API_SECRET"),
)


# test bybit
print("VALID BYBIT PAIRS: ")
print(json.dumps(bybit_trader.get_pairs(), indent=2))

# # linear
# bybit_linear_open = bybit_trader.open_trade(
#     "BTCUSDT",
#     250,
#     "linear",
#     "Buy",
#     leverage=5,
#     take_profit_percent=25,
#     stop_loss_percent=5,
#     quantity_type="USD",
# )
# print("BYBIT LINEAR TRADE OPENED: ")
# print(bybit_linear_open)
# bybit_linear_close = bybit_trader.close_trade("BTCUSDT", 0.1, "linear", "Buy")
# print("BYBIT LINEAR TRADE CLSOED: ")
# print(bybit_linear_close)

# # inverse
# bybit_inverse_open = bybit_trader.open_trade(
#     "BTCUSD",
#     125,  # 125 lots, 1 lot = 1 USD
#     "inverse",
#     "Buy",
#     leverage=5,
#     take_profit_percent=25,
#     stop_loss_percent=5,
#     quantity_type="USD",
# )
# print("BYBIT INVERSE TRADE OPENED: ")
# print(bybit_inverse_open)
# bybit_inverse_close = bybit_trader.close_trade("BTCUSD", 0.1, "inverse", "Buy")
# print("BYBIT INVERSE TRADE CLOSED: ")
# print(bybit_inverse_close)


# test binance
print("VALID BINANCE PAIRS: ")
print(json.dumps(binance_trader.get_pairs(), indent=2))

# # linear
# binance_linear_open = binance_trader.open_trade(
#     "BTCUSDT",
#     200,
#     "linear",
#     "Buy",
#     leverage=5,
#     take_profit_percent=25,
#     stop_loss_percent=5,
#     quantity_type="USD",
# )
# print("BINANCE LINEAR TRADE OPENED: ")
# print(binance_linear_open)
# binance_linear_close = binance_trader.close_trade("BTCUSDT", 0.1, "linear", "Buy")
# print("BINANCE LINEAR TRADE CLSOED: ")
# print(binance_linear_close)

# inverse
# binance_inverse_open = binance_trader.open_trade(
#     "BTCUSD_PERP",
#     145,  # will be rounded to 100 USD: 1 count
#     "inverse",
#     "Buy",
#     leverage=5,
#     take_profit_percent=25,
#     stop_loss_percent=25,
#     quantity_type="USD",
# )
# print("BINANCE INVERSE TRADE OPENED: ")
# print(binance_inverse_open)
# binance_inverse_close = binance_trader.close_trade("BTCUSD_PERP", 0.1, "inverse", "Buy")
# print("BINANCE INVERSE TRADE CLOSED: ")
# print(binance_inverse_close)


# test kucoin
print("VALID KUCOIN PAIRS: ")
print(json.dumps(kucoin_trader.get_pairs(), indent=2))

# # linear
# kucoin_linear_open = kucoin_trader.open_trade(
#     "XBTUSDTM",
#     0.01,
#     "linear",
#     "Buy",
#     leverage=5,
#     take_profit_percent=25,
#     stop_loss_percent=5,
#     quantity_type="token",
# )
# print("KUCOIN LINEAR TRADE OPENED: ")
# print(kucoin_linear_open)
# kucoin_linear_close = kucoin_trader.close_trade("XBTUSDTM", 0.1, "linear", "Buy")
# print("KUCOIN LINEAR TRADE CLSOED: ")
# print(kucoin_linear_close)

# inverse
kucoin_inverse_open = kucoin_trader.open_trade(
      "ETHUSDM",
      0.01,
      "inverse",
      "Buy",
      leverage=5,
      take_profit_percent=25,
      stop_loss_percent=5,
      quantity_type="token"
)

print("KUCOIN INVERSE TRADE OPENED: ")
print(kucoin_inverse_open)
kucoin_inverse_close = kucoin_trader.close_trade("XBTUSDM", 0.1, "inverse", "Buy")
print("KUCOIN INVERSE TRADE CLOSED: ")
print(kucoin_inverse_close)


# test bitmex
print("VALID BITMEX PAIRS: ")
print(json.dumps(bitmex_trader.get_pairs(), indent=2))

# # linear
# bitmex_linear_open = bitmex_trader.open_trade(
#     "XBTUSDT",
#     0.001,  # minimum buy size
#     "linear",
#     "Buy",
#     leverage=5,
#     take_profit_percent=25,
#     stop_loss_percent=5,
#     quantity_type="token",
# )
# print("BITMEX LINEAR TRADE OPENED: ")
# print(bitmex_linear_open)
# bitmex_linear_close = bitmex_trader.close_trade("XBTUSDT", 0.001, "linear", "Buy")
# print("BITMEX LINEAR TRADE CLSOED: ")
# print(bitmex_linear_close)

# # inverse
# bitmex_inverse_open = bitmex_trader.open_trade(
#     "XBTUSD",
#     0.004,  # minimum buy is 100 USD this is close
#     "inverse",
#     "Buy",
#     leverage=5,
#     take_profit_percent=25,
#     stop_loss_percent=5,
#     quantity_type="token",
# )
# print("BITMEX INVERSE TRADE OPENED: ")
# print(bitmex_inverse_open)
# bitmex_inverse_close = bitmex_trader.close_trade("XBTUSD", 0.004, "inverse", "Buy")
# print("BITMEX INVERSE TRADE CLOSED: ")
# print(bitmex_inverse_close)
