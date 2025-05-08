


from models_utilities import HermesBaseModel
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

class MarketOrderParams(HermesBaseModel):
    qty         : float
    side        : typing.Literal["BUY", "SELL"]
    tif         : typing.Literal["GTC", "IOC"]


#
# Order return models
#

class BaseOrderResult(HermesBaseModel):
    order_id            : str