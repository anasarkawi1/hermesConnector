# Connector library for Alpaca API
# By Anas Arkawi, 2025.


# Load modules
from .hermesExceptions import InsufficientParameters, HandlerNonExistent, UnknownGenericHermesException
from .connector_template import ConnectorTemplate

# Alpaca Imports
from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from alpaca.data.models.bars import Bar
from alpaca.trading.models import Clock as AlpacaClock, Order as AlpacaOrder
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading import enums as AlpacaTradingEnums
from alpaca.common.exceptions import APIError

from .models import BaseOrderResult, ClockReturnModel, LimitOrderBaseParams, LimitOrderResult, OrderBaseParams, MarketOrderNotionalParams, MarketOrderQtyParams, MarketOrderResult

# TODO: Tidy this up. Put all the imports inside a single reference instead of individual imports
from .hermes_enums import TimeInForce as HermesTIF, OrderSide as HermesOrderSide, OrderStatus as HermesOrderStatus



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

    def _orderParamConstructor(
            self,
            orderParams: OrderBaseParams) -> list[AlpacaTradingEnums.OrderSide, AlpacaTradingEnums.TimeInForce]:
        
        """
            Returns an array containing the exchange specific "Order Side" and "Time in Force" parameters of an order.

            Parameters
            ----------
                orderParams: OrderBaseParams
                    Hermes order parameters

            Returns
            -------
                list[AlpacaTradingEnums.OrderSide, AlpacaTradingEnums.TimeInForce]
        """

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

    def _orderSideMatcher(self, orderSide: AlpacaTradingEnums.OrderSide):
        orderSideResult = None
        match orderSide:
            case AlpacaTradingEnums.OrderSide.BUY:
                orderSideResult = HermesOrderSide.BUY
            case AlpacaTradingEnums.OrderSide.SELL:
                orderSideResult = HermesOrderSide.SELL
            case _:
                raise UnknownGenericHermesException
        return orderSideResult

    def _marketOrderSubmit(
            self,
            reqModel: MarketOrderRequest):
        
        # Submit order
        try:
            orderResult = self.clients["trading"].submit_order(order_data=reqModel)
            # Generate JSON string of the exchange response
            jsonStr = orderResult.model_dump_json()

            # Match order side to its Hermes enum
            orderSideResult = self._orderSideMatcher(orderResult.side)

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
                # Enums
                side                = orderSideResult,
                type                = orderResult.type,
                time_in_force       = orderResult.time_in_force,
                status              = orderResult.status,
                # Raw response as a json string
                raw                 = jsonStr)
            
            # Return output
            return output
        except APIError as err:
            raise err


    def marketOrderQty(
            self,
            orderParams: MarketOrderQtyParams) -> MarketOrderResult:
        
        orderSide, tifEnum = self._orderParamConstructor(orderParams=orderParams)

        # Consturct API request model
        reqModel = MarketOrderRequest(
            symbol=self.options.tradingPair,
            qty=orderParams.qty,
            side=orderSide,
            time_in_force=tifEnum)
        
        return self._marketOrderSubmit(reqModel=reqModel)
    
    def marketOrderCost(
            self,
            orderParams: MarketOrderNotionalParams) -> MarketOrderResult:
        
        orderSide, tifEnum = self._orderParamConstructor(orderParams=orderParams)

        # Consturct API request model
        reqModel = MarketOrderRequest(
            symbol=self.options.tradingPair,
            notional=orderParams.cost,
            side=orderSide,
            time_in_force=tifEnum)
        
        return self._marketOrderSubmit(reqModel=reqModel)

    def _limitOrderSubmit(self, reqModel: LimitOrderRequest) -> LimitOrderResult:
        # Submit order
        try:
            orderResult = self.clients["trading"].submit_order(reqModel)

            # Generate JSON string from exchange response
            jsonStr = orderResult.model_dump_json()

            # Match order side to its hermes enum
            orderSideResult = self._orderSideMatcher(orderResult.side)

            # TODO: Make the result for the order (probably similar to the market order.)
            output = LimitOrderResult(
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
                # Enums
                side                = orderSideResult,
                type                = orderResult.type,
                time_in_force       = orderResult.time_in_force,
                status              = orderResult.status,
                # Limit order specific
                limit_price         = orderResult.limit_price,
                # Raw response as a json string
                raw                 = jsonStr)
            return output
        except APIError as err:
            raise err

    def limitOrder(
            self,
            orderParams: LimitOrderBaseParams):
        
        orderSideEnum, tifEnum = self._orderParamConstructor(orderParams=orderParams)

        # Construct API request model
        reqModel = LimitOrderRequest(
            symbol=self.options.tradingPair,
            qty=orderParams.qty,
            side=orderSideEnum,
            time_in_force=tifEnum)
        
        return self._limitOrderSubmit(reqModel=reqModel)

    def queryOrder(self, orderId: str) -> BaseOrderResult:
        # Query order
        queriedOrder = self.clients["trading"].get_order_by_id(order_id=orderId)

        # Convert to JSON string
        jsonStr = queriedOrder.model_dump_json()

        # Convert enums
        orderSideResult = self._orderSideMatcher(queriedOrder.side)

        # Format order data into a model
        outputModel = BaseOrderResult(
                order_id                = str(queriedOrder.id),
                created_at          = queriedOrder.created_at,
                updated_at          = queriedOrder.updated_at,
                submitted_at        = queriedOrder.submitted_at,
                filled_at           = queriedOrder.filled_at,
                expired_at          = queriedOrder.expired_at,
                expires_at          = queriedOrder.expires_at,
                canceled_at         = queriedOrder.canceled_at,
                failed_at           = queriedOrder.failed_at,
                asset_id            = str(queriedOrder.asset_id),
                symbol              = queriedOrder.symbol,
                notional            = queriedOrder.notional,
                qty                 = queriedOrder.qty,
                filled_qty          = queriedOrder.filled_qty,
                filled_avg_price    = queriedOrder.filled_avg_price,
                # Enums
                side                = orderSideResult,
                type                = queriedOrder.type,
                time_in_force       = queriedOrder.time_in_force,
                status              = queriedOrder.status,
                # Raw response as a json string
                raw                 = jsonStr)
        
        # Return model
        return outputModel

    def cancelOrder(self, orderId: str) -> bool:
        # Query order
        targetOrder = self.queryOrder(orderId=orderId)

        # Get order status and check against dissalowed states
        disallowedStates = [
            HermesOrderStatus.FILLED,
            HermesOrderStatus.CANCELED,
            HermesOrderStatus.EXPIRED]
        
        orderStatus = targetOrder.status
        for dState in disallowedStates:
            if (orderStatus == dState):
                return False
        
        # The loop terminated without returning, continue with cancellation
        self.clients["trading"].cancel_order_by_id(order_id=orderId)
        return True
    
    def _orderToModel(self, order: AlpacaOrder) -> BaseOrderResult:
        # Convert AlpacaOrder to JSON string
        jsonStr = order.model_dump_json()

        # Convert enums
        orderSideResult = self._orderSideMatcher(order.side)

        # Format order data into a model
        return BaseOrderResult(
                order_id                = str(order.id),
                created_at          = order.created_at,
                updated_at          = order.updated_at,
                submitted_at        = order.submitted_at,
                filled_at           = order.filled_at,
                expired_at          = order.expired_at,
                expires_at          = order.expires_at,
                canceled_at         = order.canceled_at,
                failed_at           = order.failed_at,
                asset_id            = str(order.asset_id),
                symbol              = order.symbol,
                notional            = order.notional,
                qty                 = order.qty,
                filled_qty          = order.filled_qty,
                filled_avg_price    = order.filled_avg_price,
                # Enums
                side                = orderSideResult,
                type                = order.type,
                time_in_force       = order.time_in_force,
                status              = order.status,
                # Raw response as a json string
                raw                 = jsonStr)

    def currentOrder(self) -> list[BaseOrderResult]:
        # Filter for open orders only
        queryFilters = GetOrdersRequest(status=AlpacaTradingEnums.QueryOrderStatus.OPEN)
        # Execute query
        ordersList: list[AlpacaOrder] = self.clients["trading"].get_orders(filter=queryFilters)
        # Iterate through and format them into models
        output: list[BaseOrderResult] = [self._orderToModel(currentOrder) for currentOrder in ordersList]
        # Return formatted list
        return output

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
