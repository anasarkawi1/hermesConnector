


from enum import Enum


class OrderType(str, Enum):
    MARKET                  = "market"
    LIMIT                   = "limit"
    STOP                    = "stop"
    STOP_LIMIT              = "stop_limit"

class OrderSide(str, Enum):
    BUY                     = "BUY"
    SELL                    = "SELL"

class TimeInForce(str, Enum):
    GTC                     = "gtc"
    IOC                     = "ioc"
    DAY                     = "day"

class OrderStatus(str, Enum):
    NEW                     = "new"
    PARTIALLY_FILLED        = "partially_filled"
    FILLED                  = "filled"
    DONE_FOR_DAY            = "done_for_day"
    CANCELED                = "canceled"
    EXPIRED                 = "expired"
    REPLACED                = "replaced"
    PENDING_CANCEL          = "pending_cancel"
    PENDING_REPLACE         = "pending_replace"
    PENDING_REVIEW          = "pending_review"
    ACCEPTED                = "accepted"
    PENDING_NEW             = "pending_new"
    ACCEPTED_FOR_BIDDING    = "accepted_for_bidding"
    STOPPED                 = "stopped"
    REJECTED                = "rejected"
    SUSPENDED               = "suspended"
    CALCULATED              = "calculated"
    HELD                    = "held"

class Timeframe(str, Enum):
    WEEK                    = "week"
    DAY                     = "day"
    HOUR                    = "hour"
    MINUTE                  = "minute"