import json
import math
from typing import Any, Literal, Optional

import bitmex

from blackswan.exchanges.exchange import Exchange, Position, exchange_logger

log = exchange_logger.getChild("binance")


class BitmexException(Exception):
    pass


class Bitmex(Exchange):
    def __init__(self, testnet: bool = True, **kwargs):
        for key in ["api_key", "api_secret"]:
            if not kwargs.get(key):
                raise BitmexException(f"Missing required parameter {key}")

        self.session = bitmex.bitmex(
            test=testnet,
            api_key=kwargs.get("api_key"),
            api_secret=kwargs.get("api_secret"),
            config={
                "use_models": False,
                "validate_responses": False,
                "also_return_response": False,
            },
        )
        valid_contracts = self.session.Instrument.Instrument_get(
            filter=json.dumps({"typ": "FFWCSX"})
        ).result()
        self.INVERSE_PAIRS = [
            contract["symbol"] for contract in valid_contracts if contract["isInverse"]
        ]
        self.inverse_multiplier = {
            contract["symbol"]: contract["lotSize"]
            for contract in valid_contracts
            if contract["isInverse"]
        }
        self.LINEAR_PAIRS = [
            contract["symbol"]
            for contract in valid_contracts
            if not contract["isInverse"]
        ]
        self.linear_multiplier = {
            contract["symbol"]: contract["lotSize"]
            for contract in valid_contracts
            if not contract["isInverse"]
        }

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
            raise BitmexException(
                f"Unsupported leverage amount: {leverage}. Must be between 1 and 100"
            )
        self.session.Position.Position_updateLeverage(
            symbol=symbol, leverage=leverage
        ).result()
        if side == "Buy":
            entry_price = float(
                self.session.Instrument.Instrument_get(
                    filter=json.dumps({"symbol": symbol})
                ).result()[0]["askPrice"]
            )
        else:  # sell / SHORT
            entry_price = float(
                self.session.Instrument.Instrument_get(
                    filter=json.dumps({"symbol": symbol})
                ).result()[0]["bidPrice"]
            )

        log.debug(
            f"Opening {side.upper()} position on {symbol} at price: {entry_price}"
        )
        # bitmex specifies amount of lots instead of number of tokens to purchase
        # so we divide the quantity by the multiplier
        # it also expects `quantity` as USD
        # E.g. 1 lot of XBTUSDT is 1 USD
        # so if you want to buy 0.2 BTC (quantity = 0.2) you need to convert to USD
        # then get the number of lots
        if category == "linear":
            # if `quantity_type` is `USD` determine the amount of tokens to buy
            if quantity_type == "USD":
                quantity = round(quantity / entry_price, 3)
            quantity = (
                math.floor(quantity * self.linear_multiplier[symbol])
                * self.linear_multiplier[symbol]
            )
        else:  # inverse pair
            # if `quantity_type` is `token` get the whole number of USD to buy
            if quantity_type == "token":
                quantity = math.floor(quantity * entry_price)
            # round to nearest lot number: XBTUSD is $100 lots
            quantity = (
                math.floor(quantity / self.inverse_multiplier[symbol])
                * self.inverse_multiplier[symbol]
            )

        take_profit = None
        stop_loss = None

        open_order = self.session.Order.Order_new(
            symbol=symbol, side=side, orderQty=quantity, ordType="Market"
        ).result()
        # to set TP/SL we open subsequent positions as Stop Orders
        if take_profit_percent:
            if side == "Buy":
                # calculate price for take profit based on entry price
                take_profit_price = math.floor(
                    entry_price + (entry_price * (take_profit_percent / 100))
                )
            else:  # sell / SHORT
                # calculate price for take profit based on entry price
                take_profit_price = math.floor(
                    entry_price - (entry_price * (take_profit_percent / 100))
                )

            log.debug(
                f"Creating take profit position for {side.upper()} at price: {take_profit_price}"
            )

            take_profit = self.session.Order.Order_new(
                symbol=symbol,
                side="Sell" if side == "Buy" else "Buy",
                orderQty=quantity,
                ordType="MarketIfTouched",
                execInst="LastPrice",
                stopPx=take_profit_price,
            ).result()
        if stop_loss_percent:
            if side == "Buy":
                # calculate price for stop loss based on entry price
                stop_loss_price = math.floor(
                    entry_price - (entry_price * (stop_loss_percent / 100))
                )

            else:  # sell / SHORT
                # calculate price for stop loss based on entry price
                stop_loss_price = math.floor(
                    entry_price + (entry_price * (stop_loss_percent / 100))
                )

            log.debug(
                f"Creating stop loss position for {side.upper()} at price: {stop_loss_price}"
            )

            stop_loss = self.session.Order.Order_new(
                symbol=symbol,
                side="Sell" if side == "Buy" else "Buy",
                orderQty=quantity,
                ordType="Stop",
                execInst="LastPrice",
                stopPx=stop_loss_price,
            ).result()
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
        self.session.Order.Order_cancelAll(
            symbol=symbol,
            filter=json.dumps({"side": "Sell" if side == "Buy" else "Buy"}),
        ).result()
        return self.session.Order.Order_closePosition(symbol=symbol).result()
