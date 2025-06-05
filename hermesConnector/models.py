


from .hermes_enums import OrderSide, OrderStatus, OrderType, TimeInForce
from .models_utilities import HermesBaseModel
from datetime import datetime
from typing import Optional, Union


class ClockReturnModel(HermesBaseModel):
    isOpen                  : bool
    nextOpen                : datetime
    nextClose               : datetime
    currentTimestamp        : datetime


#
# Order input models
#

class OrderBaseParams(HermesBaseModel):
    side        : OrderSide
    tif         : TimeInForce


class MarketOrderQtyParams(OrderBaseParams):
    qty         : float

class MarketOrderNotionalParams(OrderBaseParams):
    cost        : float


class LimitOrderBaseParams(OrderBaseParams):
    qty         : int

#
# Order return models
#

class BaseOrderResult(HermesBaseModel):
    order_id                    : str
    created_at                  : datetime
    updated_at                  : datetime
    submitted_at                : datetime
    filled_at                   : Optional[datetime]
    expired_at                  : Optional[datetime]
    expires_at                  : Optional[datetime]
    canceled_at                 : Optional[datetime]
    failed_at                   : Optional[datetime]
    asset_id                    : Optional[str]
    symbol                      : Optional[str]
    notional                    : Optional[float]
    qty                         : Optional[float]
    filled_qty                  : Optional[float]
    filled_avg_price            : Optional[float]
    type                        : Optional[OrderType]
    side                        : Optional[OrderSide]
    time_in_force               : Optional[TimeInForce]
    status                      : Optional[OrderStatus]

    # Raw exchange response as a JSON string. Used for archival and redundancy reasons.
    raw                         : str


class MarketOrderResult(BaseOrderResult):
    pass

class LimitOrderResult(BaseOrderResult):
    limit_price                 : Optional[float] = None


#
# Market Data Models
#

class BaseMarketData(HermesBaseModel):

    """

        Base market data model containing all the fields of a market candlestick.

            Attributes:
            ----------
                openTime        (float)   : Open time for the candlestick in epoch milliseconds.
                openPrice       (float) : Open price for the candlestick.
                highPrice       (float) : High price for the candlestick.
                lowPrice        (float) : Low price for the candlestick.
                closePrice      (float) : Close price for the candlestick.
                closeTime       (float)   : Close time for the candlestick in epoch milliseconds.
                volume          (float) : Trade volume for the candlestick.
    """

    openTime        : float
    openPrice       : float
    highPrice       : float
    lowPrice        : float
    closePrice      : float
    closeTime       : float
    volume          : float

class LiveMarketData(BaseMarketData):
    pass