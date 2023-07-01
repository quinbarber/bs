import math
from typing import Any, Literal, Optional

from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures

from blackswan.exchanges.exchange import Exchange, Position, exchange_logger

log = exchange_logger.getChild("binance")


class BinanceException(Exception):
    pass


# https://binance-docs.github.io/apidocs/delivery/en/#new-order-trade
class Binance(Exchange):
    def __init__(self, testnet: bool = True, **kwargs):
        """
        connect to Binance. Requires: `api_key` and `api_secret`
        conn = Binance(testnet=False, api_key='', api_secret='')
        # access connection for inverse pairs directly
        conn.cm_session.do_thing()
        # access connection for linear pairs directly
        conn.um_session.do_thing()
        """
        for key in ["api_key", "api_secret"]:
            if not kwargs.get(key):
                raise BinanceException(f"Missing required parameter {key}")

        if testnet:
            self.cm_session = CMFutures(
                kwargs.get("api_key"),
                kwargs.get("api_secret"),
                base_url="https://testnet.binancefuture.com",
            )
            self.um_session = UMFutures(
                kwargs.get("api_key"),
                kwargs.get("api_secret"),
                base_url="https://testnet.binancefuture.com",
            )
        else:
            self.cm_session = CMFutures(
                kwargs.get("api_key"),
                kwargs.get("api_secret"),
            )
            self.um_session = UMFutures(
                kwargs.get("api_key"),
                kwargs.get("api_secret"),
            )

        self.INVERSE_PAIRS = [
            ticker["symbol"] for ticker in self.cm_session.book_ticker()
        ]
        self.LINEAR_PAIRS = [
            ticker["symbol"] for ticker in self.um_session.book_ticker()
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
        """
        Binance inverse pairs expect `quantity` to be a contract count where each contract = 100 USD. We assume `quantity`
        passed in is the token amount for consistency and then convert it
        TP/SL is set by creating additional orders as StopOrders, after the initial purchase has been placed
        """
        self.validate_trade(symbol, category)
        if leverage < 1 or leverage > 125:
            log.error("Leverage must be between 1 and 125")
            raise BinanceException(
                f"Unsupported leverage amount: {leverage}. Must be between 1 and 125"
            )

        session = self.um_session if category == "linear" else self.cm_session
        if category == "linear":
            if side == "Buy":
                entry_price = float(session.book_ticker(symbol)["askPrice"])
            else:  # sell / SHORT
                entry_price = float(session.book_ticker(symbol)["bidPrice"])
            # if `quantity_type` is `USD` determine the amount of tokens to buy
            if quantity_type == "USD":
                quantity = round(quantity / entry_price, 3)
        else:  # inverse pair
            if side == "Buy":
                entry_price = float(session.book_ticker(symbol)[0]["askPrice"])
            else:  # sell / SHORT
                entry_price = float(session.book_ticker(symbol)[0]["bidPrice"])
            # purchase size is in lots where 1 lot = 100 USD
            # if `quantity_type` is `tokens` covert with entry price
            if quantity_type == "token":
                quantity = entry_price * quantity
            # MUST be a whole number, divide by 100 to get lots
            quantity = math.floor(quantity / 100)

        log.debug(
            f"Opening {side.upper()} position on {symbol} at price: {entry_price}"
        )

        take_profit = None
        stop_loss = None

        session.change_leverage(
            symbol=symbol,
            leverage=leverage,
        )
        open_order = session.new_order(
            symbol=symbol,
            side=side.upper(),
            type="MARKET",
            quantity=quantity,
        )
        if take_profit_percent:
            if side == "Buy":
                take_profit_price = round(
                    entry_price + (entry_price * (take_profit_percent / 100)), 2
                )
            else:  # sell / SHORT
                take_profit_price = round(
                    entry_price - (entry_price * (take_profit_percent / 100)), 2
                )

            log.debug(
                f"Creating take profit position for {side.upper()} at price: {take_profit_price}"
            )

            take_profit = session.new_order(
                symbol=symbol,
                side="BUY" if side == "Sell" else "SELL",
                type="TAKE_PROFIT_MARKET",
                quantity=0,
                stopPrice=take_profit_price,
                closePosition="true",
                workingType="MARK_PRICE",
            )
        if stop_loss_percent:
            if side == "Buy":
                stop_loss_price = round(
                    entry_price - (entry_price * (stop_loss_percent / 100)), 2
                )
            else:  # sell / SHORT
                stop_loss_price = round(
                    entry_price + (entry_price * (stop_loss_percent / 100)), 2
                )

            log.debug(
                f"Creating stop loss position for {side.upper()} at price: {stop_loss_price}"
            )

            stop_loss = session.new_order(
                symbol=symbol,
                side="BUY" if side == "Sell" else "SELL",
                type="STOP_MARKET",
                quantity=0,
                stopPrice=stop_loss_price,
                closePosition="true",
                workingType="MARK_PRICE",
            )
        return Position(
            side=side, position=open_order, take_profit=take_profit, stop_loss=stop_loss
        )

    def close_trade(
        self,
        symbol: str,
        quantity: float,
        category: Literal["linear", "inverse"],
        side: Literal["Buy", "Sell"],
    ) -> Any:
        self.validate_trade(symbol, category)
        session = self.um_session if category == "linear" else self.cm_session
        return session.new_order(
            symbol=symbol,
            side="BUY" if side == "Sell" else "SELL",
            type="MARKET",
            quantity=quantity,
        )
