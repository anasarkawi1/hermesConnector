# Connector library for Alpaca API
# By Anas Arkawi, 2025.


# Load modules
from .hermesExceptions import InsufficientParameters, HandlerNonExistent, UnknownGenericHermesException
from .connector_template import ConnectorTemplate

# Alpaca Imports
from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from alpaca.data.models.bars import Bar
from alpaca.trading.models import Clock as AlpacaClock
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading import enums as AlpacaTradingEnums
from alpaca.common.exceptions import APIError

from .models import ClockReturnModel, MarketOrderBaseParams, MarketOrderNotionalParams, MarketOrderQtyParams, MarketOrderResult
from .hermes_enums import TimeInForce as HermesTIF, OrderSide as HermesOrderSide



class Alpaca(ConnectorTemplate):

    def __init__(
            self,
            tradingPair,
            interval,
            mode='live',
            limit=75,
            credentials=["", ""],
            columns=None,
            wshandler=None):

        # Initialise parent class
        super().__init__(
            tradingPair,
            interval,
            mode,
            limit,
            credentials,
            columns,
            wshandler)
        
        # Initialise live or paper trading client
        client = None
        if self.options.mode == 'live':
            client = TradingClient(self.options.credentials[0], self.options.credentials[1])
        elif self.options.mode == 'test':
            client = TradingClient(self.options.credentials[0], self.options.credentials[1], paper=True)
        
        # Clients dictionary
        self.clients: dict[str, TradingClient | StockDataStream] = {
            "trading"       : client,
            "ws"            : None
        }

        # Initialise WS client
        if self.options.dataHandler != None:
            self.clients["ws"] = StockDataStream(
                self.options.credentials[0],
                self.options.credentials[1])
    
    def exchangeClock(self) -> ClockReturnModel:
        currentTime: AlpacaClock = self.clients["trading"].get_clock()
        return ClockReturnModel(
            isOpen=currentTime.is_open,
            nextOpen=currentTime.next_open,
            nextClose=currentTime.next_close,
            currentTimestamp=currentTime.timestamp)

    def stop(self) -> None:
        self.clients["trading"].stop()

    def account(self):
        pass

    def _marketOrderParamConstructor(
            self,
            orderParams: MarketOrderBaseParams) -> list[AlpacaTradingEnums.OrderSide, AlpacaTradingEnums.TimeInForce]:
        
        orderSide       = None
        tifEnum         = None

        # Determine the order side
        if orderParams.side == "BUY":
            orderSide = AlpacaTradingEnums.OrderSide.BUY
        elif orderParams.side == "SELL":
            orderSide = AlpacaTradingEnums.OrderSide.SELL
        else:
            raise InsufficientParameters
        
        # Determine the time in force
        match orderParams.tif:
            case HermesTIF.GTC:
                tifEnum = AlpacaTradingEnums.TimeInForce.GTC
            case HermesTIF.IOC:
                tifEnum = AlpacaTradingEnums.TimeInForce.IOC
            case HermesTIF.DAY:
                tifEnum = AlpacaTradingEnums.TimeInForce.DAY
            case _:
                raise InsufficientParameters

        return [orderSide, tifEnum]

    def _marketOrderSubmit(
            self,
            reqModel: MarketOrderRequest):
        # Submit order
        orderResult = self.clients["trading"].submit_order(order_data=reqModel)

        # Generate JSON string of the exchange response
        jsonStr = orderResult.model_dump_json()

        orderSideResult = None
        match orderResult.side:
            case AlpacaTradingEnums.OrderSide.BUY:
                orderSideResult = 'BUY'
            case AlpacaTradingEnums.OrderSide.SELL:
                orderSideResult = 'SELL'
            case _:
                raise UnknownGenericHermesException

        # Generate output
        output = MarketOrderResult(
            order_id            = str(orderResult.id),
            created_at          = orderResult.created_at,
            updated_at          = orderResult.updated_at,
            submitted_at        = orderResult.submitted_at,
            filled_at           = orderResult.filled_at,
            expired_at          = orderResult.expired_at,
            expires_at          = orderResult.expires_at,
            canceled_at         = orderResult.canceled_at,
            failed_at           = orderResult.failed_at,
            asset_id            = str(orderResult.asset_id),
            symbol              = orderResult.symbol,
            notional            = orderResult.notional,
            qty                 = orderResult.qty,
            filled_qty          = orderResult.filled_qty,
            filled_avg_price    = orderResult.filled_avg_price,
            type                = orderResult.type,
            side                = orderSideResult,
            time_in_force       = orderResult.time_in_force,
            status              = orderResult.status,
            raw                 = jsonStr)
        
        # Return output
        return output

    def marketOrderQty(
            self,
            orderParams: MarketOrderQtyParams) -> MarketOrderResult:
        
        orderSide, tifEnum = self._marketOrderParamConstructor(orderParams=orderParams)

        # Consturct API request model
        reqModel = None
        try:
            reqModel = MarketOrderRequest(
                symbol=self.options.tradingPair,
                qty=orderParams.qty,
                side=orderSide,
                time_in_force=tifEnum)
        except APIError as err:
            raise err
        
        return self._marketOrderSubmit(reqModel=reqModel)
    
    def marketOrderCost(
            self,
            orderParams: MarketOrderNotionalParams) -> MarketOrderResult:
        
        orderSide, tifEnum = self._marketOrderParamConstructor(orderParams=orderParams)

        # Consturct API request model
        reqModel = None
        try:
            reqModel = MarketOrderRequest(
                symbol=self.options.tradingPair,
                notional=orderParams.cost,
                side=orderSide,
                time_in_force=tifEnum)
        except APIError as err:
            raise err
        
        return self._marketOrderSubmit(reqModel=reqModel)

    def limitOrder(self):
        pass

    def queryOrder(self):
        pass

    def cancelOrder(self):
        pass

    def currentOrder(self):
        pass

    def getAllOrders(self):
        pass

    def historicData(self):
        pass

    def initiateLiveData(self):
        # Check if an handler was provided
        if (self.clients["ws"] == None):
            # Handler not found, raise an exception
            raise HandlerNonExistent
        
        # Configure WS client
        self.clients["ws"].subscribe_bars(
            self.wsHandlerInternal,
            self.options.tradingPair)
        
        # Start WS client
        self.clients["ws"].run()

    def wsHandlerInternal():
        pass
