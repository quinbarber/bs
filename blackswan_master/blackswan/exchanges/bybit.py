import math
from typing import Any, Literal, Optional

from pybit.unified_trading import HTTP

from blackswan.exchanges.exchange import Exchange, Position, exchange_logger

log = exchange_logger.getChild("binance")


class BybitException(Exception):
    pass


# https://bybit-exchange.github.io/docs/v5/order/create-order
class Bybit(Exchange):
    def __init__(self, testnet: bool = True, **kwargs):
        """
        connect to Bybit. Requires: `api_key` and `api_secret`
        conn = Bybit(testnet=False, api_key='', api_secret='')
        # access connection directly
        conn.session.do_thing()
        """
        for key in ["api_key", "api_secret"]:
            if not kwargs.get(key):
                raise BybitException(f"Missing required parameter {key}")

        self.session = HTTP(
            testnet=testnet,
            api_key=kwargs.get("api_key"),
            api_secret=kwargs.get("api_secret"),
        )
        inverse_ticker_data: Any = self.session.get_tickers(category="inverse")
        self.INVERSE_PAIRS = [
            ticker["symbol"] for ticker in inverse_ticker_data["result"]["list"]
        ]
        linear_ticker_data: Any = self.session.get_tickers(category="linear")
        self.LINEAR_PAIRS = [
            ticker["symbol"] for ticker in linear_ticker_data["result"]["list"]
        ]

    def open_trade(
        self,
        symbol: str,
        quantity: float,
        category: Literal["linear", "inverse"],
        side: Literal["Buy", "Sell"],
        leverage: int,
        take_profit_percent: Optional[int] = None,
        stop_loss_percent: Optional[int] = None,
        quantity_type: Literal["token", "USD"] = "token",
    ) -> Any:
        self.validate_trade(symbol, category)
        if leverage < 1 or leverage > 100:
            log.error("Leverage must be between 1 and 100")
            raise BybitException(
                f"Unsupported leverage amount: {leverage}. Must be between 1 and 100"
            )

        ticker_info: Any = self.session.get_tickers(category=category, symbol=symbol)
        entry_price = float(ticker_info["result"]["list"][0]["lastPrice"])
        if category == "linear":
            # if `quantity_type` is `USD` determine the amount of tokens to buy
            if quantity_type == "USD":
                quantity = round(quantity / entry_price, 3)
        else:  # inverse pair
            # if `quantity_type` is `token` we need the USD amount
            if quantity_type == "token":
                quantity = entry_price * quantity
            # must be a whole number
            quantity = math.floor(quantity)

        log.debug(
            f"Opening {side.upper()} position on {symbol} at price: {entry_price}"
        )

        take_profit_price = None
        stop_loss_price = None

        # calculate TP/SL price from the percent change requested
        if take_profit_percent:
            if side == "Buy":
                # calculate price for take profit based on entry price
                take_profit_price = str(
                    round(entry_price + (entry_price * (take_profit_percent / 100)), 2)
                )
            else:  # sell / SHORT
                # calculate price for take profit based on entry price
                take_profit_price = str(
                    round(entry_price - (entry_price * (take_profit_percent / 100)), 2)
                )

            log.debug(
                f"Creating take profit position for {side.upper()} at price: {take_profit_price}"
            )

        if stop_loss_percent:
            if side == "Buy":
                # calculate price for stop loss based on entry price
                stop_loss_price = str(
                    round(entry_price - (entry_price * (stop_loss_percent / 100)), 2)
                )
            else:  # sell / SHORT
                # calculate price for stop loss based on entry price
                stop_loss_price = str(
                    round(entry_price + (entry_price * (stop_loss_percent / 100)), 2)
                )

            log.debug(
                f"Creating stop loss position for {side.upper()} at price: {stop_loss_price}"
            )

        if leverage != 1:
            # TODO: only set leverage for trade direction?
            # hard to know as both params are required
            try:
                self.session.set_leverage(
                    category=category,
                    symbol=symbol,
                    buyLeverage=str(leverage),
                    sellLeverage=str(leverage),
                )
            except:  # leverage already set
                pass
            open_order = self.session.place_order(
                category=category,
                symbol=symbol,
                side=side,
                isLeverage=1,
                qty=str(quantity),
                orderType="Market",
                takeProfit=take_profit_price,
                stopLoss=stop_loss_price,
            )
        else:
            open_order = self.session.place_order(
                category=category,
                symbol=symbol,
                side=side,
                isLeverage=0,
                qty=str(quantity),
                orderType="Market",
                takeProfit=take_profit_price,
                stopLoss=stop_loss_price,
            )

        # TP/SL is included in the open_order
        return Position(
            side=side, position=open_order, take_profit=None, stop_loss=None
        )

    def close_trade(
        self,
        symbol: str,
        quantity: float,
        category: Literal["linear", "inverse"],
        side: Literal["Buy", "Sell"],
    ) -> Any:
        """
        Bybit closes are done by creating an opposite position as `reduce_only` and `close_on_trigger`
        """
        self.validate_trade(symbol, category)
        return self.session.place_order(
            category=category,
            symbol=symbol,
            side="Sell" if side == "Buy" else "Buy",
            qty=str(quantity),
            order_type="Market",
            reduce_only=True,
            close_on_trigger=True,
        )
