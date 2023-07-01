import math
from typing import Any, Literal, Optional
from uuid import uuid4

from kucoin_futures.client import Market, Trade

from blackswan.exchanges.exchange import Exchange, Position, exchange_logger

log = exchange_logger.getChild("binance")


class KucoinException(Exception):
    pass


# https://docs.kucoin.com/futures/#place-an-order
class Kucoin(Exchange):
    def __init__(self, testnet: bool = True, **kwargs):
        """
        connect to Kucoin. Requires: `api_key`, `api_secret` and `api_pass
        conn = Kucoin(testnet=False, api_key='', api_secret='', api_pass='')
        # access connection directly
        conn.session.do_thing()
        # access market api endpoints
        conn.market.do_thing()
        """

        for key in ["api_key", "api_secret", "api_pass"]:
            if not kwargs.get(key):
                raise KucoinException(f"Missing required parameter {key}")

        self.market = Market(
            key=kwargs.get("api_key", ""),
            secret=kwargs.get("api_secret", ""),
            passphrase=kwargs.get("api_pass", ""),
            is_sandbox=testnet,
        )
        valid_contracts: Any = self.market.get_contracts_list()
        self.INVERSE_PAIRS = [
            contract["symbol"] for contract in valid_contracts if contract["isInverse"]
        ]
        self.inverse_multiplier = {
            contract["symbol"]: contract["multiplier"]
            for contract in valid_contracts
            if contract["isInverse"]
        }
        self.LINEAR_PAIRS = [
            contract["symbol"]
            for contract in valid_contracts
            if not contract["isInverse"]
        ]
        self.linear_multiplier = {
            contract["symbol"]: contract["multiplier"]
            for contract in valid_contracts
            if not contract["isInverse"]
        }

        self.session = Trade(
            key=kwargs.get("api_key", ""),
            secret=kwargs.get("api_secret", ""),
            passphrase=kwargs.get("api_pass", ""),
            is_sandbox=testnet,
        )

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
        Kucoin contracts are specified not in token quantities but in number of lots. Lot amounts
        are specific per pair and must be determined ahead of the purchase. In order to simplify use,
        these are calculated based off of the `quantity` passed in using `quantity * lot_multiplier`

        TP/SL is set by creating additional orders as StopOrders, after the initial purchase has been placed
        """
        self.validate_trade(symbol, category)
        if leverage < 1 or leverage > 100:
            log.error("Leverage must be between 1 and 100")
            raise KucoinException(
                f"Unsupported leverage amount: {leverage}. Must be between 1 and 100"
            )

        cid = str(uuid4())
        ticker_info: Any = self.market.get_ticker(symbol)
        entry_price = float(ticker_info["price"])

        # kucoin specifies amount of lots instead of number of tokens to purchase
        # so we divide the quantity by the multiplier
        # E.g. 1 lot of XBTUSDTM is 0.001 Bitcoin, while 1 lot of XBTUSDM is 1 USD.
        # so if you want to buy 0.2 BTC (quantity = 0.2) you need 200 lots
        if category == "linear":
            if quantity_type == "USD":
                quantity = round(quantity / entry_price, 3)
            size = math.floor(quantity / self.linear_multiplier[symbol])
        else:  # inverse
            # if `quantity_type` is `token` get the whole number of USD to buy
            if quantity_type == "token":
                quantity = math.floor(quantity * entry_price)
            size = math.floor(quantity * abs(self.inverse_multiplier[symbol]))

        log.debug(
            f"Opening {side.upper()} position on {symbol} at price: {entry_price}"
        )

        take_profit = None
        stop_loss = None

        open_order: Any = self.session.create_market_order(
            symbol,
            side.lower(),
            str(leverage),
            clientOid=cid,
            size=str(size),
            type="market",
        )

        # to set TP/SL we open subsequent positions as Stop Orders
        if take_profit_percent:
            if side == "Buy":
                # take profit in the correct direction
                stop_direction = "up"
                # calculate price for take profit based on entry price
                take_profit_price = str(
                    math.floor(
                        entry_price + (entry_price * (take_profit_percent / 100))
                    )
                )
            else:  # sell / SHORT
                # take profit in the correct direction
                stop_direction = "down"
                # calculate price for take profit based on entry price
                take_profit_price = str(
                    math.floor(
                        entry_price - (entry_price * (take_profit_percent / 100))
                    )
                )
            log.debug(
                f"Creating take profit position for {side.upper()} at price: {take_profit_price}"
            )

            # stopPriceType is either Trade Price (last closed trade), Index Price or Mark Price (aggregated price data)
            take_profit: Any = self.session.create_market_order(
                symbol,
                side.lower(),
                str(leverage),
                clientOid=cid,
                size=str(size),
                stop=stop_direction,
                stopPriceType="TP",
                stopPrice=take_profit_price,
            )
        if stop_loss_percent:
            if side == "Buy":
                # take profit in the correct direction
                stop_direction = "down"
                # calculate price for stop loss based on entry price
                stop_loss_price = str(
                    math.floor(entry_price - (entry_price * (stop_loss_percent / 100)))
                )
            else:  # sell / SHORT
                # take profit in the correct direction
                stop_direction = "up"
                # calculate price for stop loss based on entry price
                stop_loss_price = str(
                    math.floor(entry_price + (entry_price * (stop_loss_percent / 100)))
                )

            log.debug(
                f"Creating stop loss position for {side.upper()} at price: {stop_loss_price}"
            )

            # stopPriceType is either Trade Price (last closed trade), Index Price or Mark Price (aggregated price data)
            stop_loss: Any = self.session.create_market_order(
                symbol,
                side.lower(),
                str(leverage),
                clientOid=cid,
                size=str(size),
                stop=stop_direction,
                stopPriceType="TP",
                stopPrice=stop_loss_price,
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
        # only the symbol is necessary when closing a trade
        return self.session.create_market_order(
            symbol, side=side.lower(), lever=0, closeTrade=True
        )
