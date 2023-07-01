from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional

from blackswan import bs_logger

exchange_logger = bs_logger.getChild("exchange")


class ExchangeException(Exception):
    pass


@dataclass
class Position:
    """Result from opening a trade"""

    side: str
    position: Any
    take_profit: Optional[Any]  # can be a position or a price
    stop_loss: Optional[Any]  # can be a position or a price


class Exchange:
    INVERSE_PAIRS = []
    LINEAR_PAIRS = []

    def __init__(self, testnet: bool = True, **kwargs):
        """create the initial connection to the exchange. Note: required parameters differ between exchanges"""
        raise NotImplementedError

    def get_pairs(self) -> Dict[str, List[str]]:
        """utilitiy function if you want to know all valid pairs for an exchange"""
        return {"inverse": self.INVERSE_PAIRS, "linear": self.LINEAR_PAIRS}

    def validate_trade(self, symbol: str, category: Literal["linear", "inverse"]):
        """ensures that the symbol/pair exists for the given exchange"""
        if category == "inverse" and symbol not in self.INVERSE_PAIRS:
            exchange_logger.error(f"Invalid pair for inverse: {symbol}")
            raise ExchangeException(
                f"Invalid pair for inverse {symbol}. Must be one of: {self.INVERSE_PAIRS}"
            )
        if category == "linear" and symbol not in self.LINEAR_PAIRS:
            exchange_logger.error(f"Invalid pair for linear: {symbol}")
            raise ExchangeException(
                f"Invalid pair for linear {symbol}. Must be one of: {self.LINEAR_PAIRS}"
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
        places a market order on `symbol` pair for `quantity` in tokens. Category specifies whether the trade is on the inverse or linear pair
        while side determines buy LONG / sell SHORT. Optional parameters `take_profit_percent` and `stop_loss_percent` denote the TP/SL in percent
        difference from the market purchase price. These should be between 1 and 100. The actual values for TP/SL are calculated just before placing
        the market buy, and use the last trading price

        `leverage` is exchange specific, each one having different max leverage. `leverage` of 1 means no leverage
        Note: some exchanges require trader experience to use max leverage, ensure your account has access to the attempted leverage value

        `quantity_type` allows you to specify the root symbol or the trading symbol (XBTUSD -> XBT: token, USD: USD)
        """
        raise NotImplementedError

    def close_trade(
        self,
        symbol: str,
        quantity: float,
        category: Literal["linear", "inverse"],
        side: Literal["Buy", "Sell"],
    ) -> Any:
        """
        closes open positions on the provided symbol. Note: some exchanges close both longs and shorts, others let you specify
        which side to close on
        """
        raise NotImplementedError
