


from .hermes_enums import OrderSide, OrderStatus, OrderType, TimeInForce
from .models_utilities import HermesBaseModel
from datetime import datetime
import typing_extensions as typing


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
    filled_at                   : typing.Optional[datetime]
    expired_at                  : typing.Optional[datetime]
    expires_at                  : typing.Optional[datetime]
    canceled_at                 : typing.Optional[datetime]
    failed_at                   : typing.Optional[datetime]
    asset_id                    : typing.Optional[str]
    symbol                      : typing.Optional[str]
    notional                    : typing.Optional[str]
    qty                         : typing.Optional[float]
    filled_qty                  : typing.Optional[float]
    filled_avg_price            : typing.Optional[float]
    type                        : typing.Optional[OrderType]
    side                        : typing.Optional[OrderSide]
    time_in_force               : TimeInForce
    status                      : OrderStatus

    # Raw exchange response as a JSON string. Used for archival and redundancy reasons.
    raw                         : typing.Union[str, any]


class MarketOrderResult(BaseOrderResult):
    pass

class LimitOrderResult(BaseOrderResult):
    limit_price                 : typing.Optional[float] = None
    pass