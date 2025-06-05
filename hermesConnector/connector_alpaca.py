# Connector library for Alpaca API
# By Anas Arkawi, 2025.


# Load modules
from datetime import datetime, timedelta
import warnings
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import timezone
from typing import Union, Dict, Tuple

from .hermes_exceptions import InsufficientParameters, HandlerNonExistent, NonStandardInput, TargetClientInitiationError, UnexpectedInput, UnexpectedOutputType, UnknownGenericHermesException, UnsupportedFeature, UnsupportedParameterValue
from .connector_template import ConnectorTemplate

# Alpaca Imports
from alpaca.trading.client import TradingClient
from alpaca.data.models.bars import Bar
from alpaca.trading.models import Clock as AlpacaClock, Order as AlpacaOrder, Asset as AlpacaAsset
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading import enums as AlpacaTradingEnums
from alpaca.common.exceptions import APIError
# Data Clients
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
# Live Data Clients
from alpaca.data.live import StockDataStream, OptionDataStream, CryptoDataStream
# Historical data request models
from alpaca.data import StockBarsRequest, OptionBarsRequest, CryptoBarsRequest, TimeFrame as AlpacaTimeFrame, TimeFrameUnit as AlpacaTimeFrameUnit, BarSet as AlpacaBarSet, RawData as AlpacaRawData

from .models import BaseOrderResult, ClockReturnModel, LimitOrderBaseParams, LimitOrderResult, LiveMarketData, OrderBaseParams, MarketOrderNotionalParams, MarketOrderQtyParams, MarketOrderResult

# TODO: Tidy this up. Put all the imports inside a single reference instead of individual imports
from .hermes_enums import OrderType, TimeInForce as HermesTIF, OrderSide as HermesOrderSide, OrderStatus as HermesOrderStatus, TimeframeUnit as HermesTimeframeUnit
from .timeframe import TimeFrame as HermesTimeFrame



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
        # The "ws" and "historical" elements hold the real-time and historical data streams respectively. Since Alpaca's Python SDK seperates each asset class into its own data class, these elements are populated later.
        # TODO: The type hinting here is obnoxious...
        self.clients: dict[str, None | TradingClient | StockDataStream | OptionDataStream | CryptoDataStream | StockHistoricalDataClient | OptionHistoricalDataClient | CryptoHistoricalDataClient] = {
            "trading"       : client,
            "ws"            : None,
            "historical"    : None
        }

        if (client != None):
            self._tradingClient: TradingClient = client
        else:
            raise TargetClientInitiationError

        # TODO: Implement Stream and HistoricDataClient selection here
        # Get asset info
        assetInfo = self._getAssetInfo(assetNameOrId=self.options.tradingPair)
        self._assetClass = assetInfo.asset_class
        historicDataClient = None
        realTimeDataClient = None

        # Also assign a standard model for requests
        historicalDataRequestModel = None

        # Determine if the target asset is a stock, options contract, or a cryptocurrency
        match self._assetClass:
            case AlpacaTradingEnums.AssetClass.US_EQUITY:
                historicDataClient = StockHistoricalDataClient(
                    api_key=self.options.credentials[0],
                    secret_key=self.options.credentials[1])
                realTimeDataClient = StockDataStream(
                    api_key=self.options.credentials[0],
                    secret_key=self.options.credentials[1])
                historicalDataRequestModel = StockBarsRequest
            case AlpacaTradingEnums.AssetClass.US_OPTION:
                historicDataClient = OptionHistoricalDataClient(
                    api_key=self.options.credentials[0],
                    secret_key=self.options.credentials[1])
                realTimeDataClient = OptionDataStream(
                    api_key=self.options.credentials[0],
                    secret_key=self.options.credentials[1])
                print("[HermesConnector - INFO]: Currently, options trading is yet to be completely implemented. Usage of Hermes methods for options trading could lead to undefined behaviour.")
                historicalDataRequestModel = OptionBarsRequest
            case AlpacaTradingEnums.AssetClass.CRYPTO:
                historicDataClient = CryptoHistoricalDataClient()
                realTimeDataClient = CryptoDataStream(
                    api_key=self.options.credentials[0],
                    secret_key=self.options.credentials[1])
                historicalDataRequestModel = CryptoBarsRequest
            case _:
                raise NonStandardInput
        
        # Populate the clients dictionary and request data model fields
        self.clients["historical"] = historicDataClient
        self._historicalDataClient = historicDataClient
        self.historicalDataRequestModel = historicalDataRequestModel
        # Check if a data handler was supplied. Else, don't assign the real time client
        if self.options.dataHandler != None:
            self.clients["ws"] = realTimeDataClient
            self._wsClient = realTimeDataClient
        
        # Declare a start date for historical data
        # The date is way back in the past (30 years by default) to allow for the limit parameter to take priority
        self._historicalDataStartDate = datetime.now() - timedelta(weeks=(52 * 30))

        # Convert Hermes timeframe to Alpaca timeframe
        self._requestAlpacaTimeFrame = self._convertTimeFrame(self.options.interval)

    @staticmethod
    def generalErrorHandlerDecorator(func):
        def wrapper_generalErrorHandlerDecorator(self, *args, **kwargs):
            '''
                Decorator used for 
            '''
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                raise e
        return wrapper_generalErrorHandlerDecorator
    
    def _exchangeClock_request(self) -> Union[AlpacaClock, AlpacaRawData]:
        return self._tradingClient.get_clock()
    
    def _exchangeClock_internal(self, input) -> ClockReturnModel:
        # To appease the Pylance, check if the type is of Dict, the base type for Alpaca's RawData type.
        if (isinstance(input, Dict)):
            raise UnexpectedOutputType
        else:
            return ClockReturnModel(
                isOpen=input.is_open,
                nextOpen=input.next_open,
                nextClose=input.next_close,
                currentTimestamp=input.timestamp)
    
    @generalErrorHandlerDecorator
    def exchangeClock(self) -> ClockReturnModel:
        input = self._exchangeClock_request()
        return self._exchangeClock_internal(input=input)

    def stop(self) -> None:
        self._wsClient.stop()

    def account(self):
        pass

    def _orderParamConstructor(
            self,
            orderParams: OrderBaseParams) -> Tuple[AlpacaTradingEnums.OrderSide, AlpacaTradingEnums.TimeInForce]:
        
        """
            Returns an array containing the exchange specific "Order Side" and "Time in Force" parameters of an order.

            Parameters
            ----------
                orderParams: OrderBaseParams
                    Hermes order parameters

            Returns
            -------
                Tuple[AlpacaTradingEnums.OrderSide, AlpacaTradingEnums.TimeInForce]
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

        return (orderSide, tifEnum)

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
            orderResult = self._tradingClient.submit_order(order_data=reqModel)
            if(isinstance(orderResult, Dict)):
                raise UnexpectedOutputType
            
            # Generate JSON string of the exchange response
            jsonStr = orderResult.model_dump_json()

            # Match order side to its Hermes enum
            if (orderResult.side == None):
                raise UnexpectedInput
            orderSideResult = self._orderSideMatcher(orderResult.side)

            # Generate output
            # TODO: Are these checks even remotely needed?
            if (
                orderResult.type                    == None or
                orderResult.time_in_force           == None or
                orderResult.status                  == None
                ):
                raise UnexpectedOutputType
            
            filled_qty          = None
            filled_avg_price    = None
            if (
                orderResult.filled_qty          != None and
                orderResult.filled_avg_price    != None
            ):
                filled_qty          = float(orderResult.filled_qty)
                filled_avg_price    = float(orderResult.filled_avg_price)
            
            qty = None
            if (orderResult.qty != None):
                qty = float(orderResult.qty)
            
            notional = None
            if (orderResult.notional != None):
                notional = float(orderResult.notional)

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
                notional            = notional,
                qty                 = qty,
                filled_qty          = filled_qty,
                filled_avg_price    = filled_avg_price,
                # Enums
                side                = orderSideResult,
                type                = OrderType(orderResult.type),
                time_in_force       = HermesTIF(orderResult.time_in_force),
                status              = HermesOrderStatus(orderResult.status),
                # Raw response as a json string
                raw                 = jsonStr)
            
            # Return output
            return output
        except APIError as err:
            raise err
    

    @generalErrorHandlerDecorator
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
    
    @generalErrorHandlerDecorator
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
            orderResult = self._tradingClient.submit_order(reqModel)
            if(isinstance(orderResult, Dict)):
                raise UnexpectedOutputType

            # Generate JSON string from exchange response
            jsonStr = orderResult.model_dump_json()

            # Match order side to its hermes enum
            if (orderResult.side == None):
                raise UnexpectedInput
            orderSideResult = self._orderSideMatcher(orderResult.side)

            # TODO: Make the result for the order (probably similar to the market order.)
            if (
                orderResult.qty                     == None or
                orderResult.type                    == None or
                orderResult.time_in_force           == None or
                orderResult.status                  == None or
                orderResult.limit_price             == None
                ):
                raise UnexpectedOutputType
            

            # Check if there's any fill data, if so process accordingly
            filled_qty          = None
            filled_avg_price    = None
            if (
                orderResult.filled_qty          != None and
                orderResult.filled_avg_price    != None):
                filled_qty          = float(orderResult.filled_qty)
                filled_avg_price    = float(orderResult.filled_avg_price)
            
            # Process notional and quantity fields
            notional = None
            if (orderResult.notional != None):
                notional = float(orderResult.notional)
            qty = None
            if (orderResult.qty != None):
                qty = float(orderResult.qty)


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
                notional            = notional,
                qty                 = qty,
                filled_qty          = filled_qty,
                filled_avg_price    = filled_avg_price,
                # Enums
                side                = orderSideResult,
                type                = OrderType(orderResult.type),
                time_in_force       = HermesTIF(orderResult.time_in_force),
                status              = HermesOrderStatus(orderResult.status),
                # Limit order specific
                limit_price         = float(orderResult.limit_price),
                # Raw response as a json string
                raw                 = jsonStr)
            return output
        except APIError as err:
            raise err
    
    @generalErrorHandlerDecorator
    def limitOrder(
            self,
            orderParams: LimitOrderBaseParams):
        
        orderSideEnum, tifEnum = self._orderParamConstructor(orderParams=orderParams)

        # Construct API request model
        reqModel = LimitOrderRequest(
            symbol=self.options.tradingPair,
            qty=orderParams.qty,
            limit_price=orderParams.limitPrice,
            side=orderSideEnum,
            time_in_force=tifEnum)
        
        return self._limitOrderSubmit(reqModel=reqModel)

    def queryOrder(self, orderId: str) -> BaseOrderResult:
        # Query order
        queriedOrder = self._tradingClient.get_order_by_id(order_id=orderId)
        if(isinstance(queriedOrder, Dict)):
                raise UnexpectedOutputType

        # Convert to JSON string
        jsonStr = queriedOrder.model_dump_json()

        # Convert enums
        if (queriedOrder.side == None):
                raise UnexpectedInput
        orderSideResult = self._orderSideMatcher(queriedOrder.side)

        # Format order data into a model
        if (
                queriedOrder.type                    == None or
                queriedOrder.time_in_force           == None or
                queriedOrder.status                  == None
                ):
                raise UnexpectedOutputType
        
        filled_qty          = None
        filled_avg_price    = None
        if(
            queriedOrder.filled_qty         != None and
            queriedOrder.filled_avg_price   != None
        ):
            filled_qty          = float(queriedOrder.filled_qty)
            filled_avg_price    = float(queriedOrder.filled_avg_price)
        
        notional = None
        if (queriedOrder.notional != None):
            notional = float(queriedOrder.notional)
        qty = None
        if (queriedOrder.qty != None):
            qty = float(queriedOrder.qty)

        outputModel = BaseOrderResult(
                order_id            = str(queriedOrder.id),
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
                notional            = notional,
                qty                 = qty,
                filled_qty          = filled_qty,
                filled_avg_price    = filled_avg_price,
                # Enums
                side                = orderSideResult,
                type                = OrderType(queriedOrder.type),
                time_in_force       = HermesTIF(queriedOrder.time_in_force),
                status              = HermesOrderStatus(queriedOrder.status),
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
        self._tradingClient.cancel_order_by_id(order_id=orderId)
        return True
    
    def _orderToModel(self, order: AlpacaOrder) -> BaseOrderResult:
        # Convert AlpacaOrder to JSON string
        jsonStr = order.model_dump_json()

        # Convert enums
        if (order.side == None):
            raise UnexpectedOutputType
        orderSideResult = self._orderSideMatcher(order.side)

        # Format order data into a model
        if (
                order.qty                     == None or
                order.filled_qty              == None or
                order.filled_avg_price        == None or
                order.type                    == None or
                order.time_in_force           == None or
                order.status                  == None or
                order.limit_price             == None
                ):
                raise UnexpectedOutputType
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
                qty                 = float(order.qty),
                filled_qty          = float(order.filled_qty),
                filled_avg_price    = float(order.filled_avg_price),
                # Enums
                side                = orderSideResult,
                type                = OrderType(order.type),
                time_in_force       = HermesTIF(order.time_in_force),
                status              = HermesOrderStatus(order.status),
                # Raw response as a json string
                raw                 = jsonStr)
    
    def _formattedOrderListGenerator(self, currentOrder: Union[AlpacaOrder, AlpacaRawData, str]) -> BaseOrderResult:
        if (isinstance(currentOrder, Dict) or isinstance(currentOrder, str)):
            raise UnexpectedOutputType
        return self._orderToModel(currentOrder)

    def currentOrder(self) -> list[BaseOrderResult]:
        # Filter for open orders and orders of the current symbol only
        queryFilters = GetOrdersRequest(
            status=AlpacaTradingEnums.QueryOrderStatus.OPEN,
            symbols=[self.options.tradingPair])

        # Execute query
        ordersList: Union[list[AlpacaOrder], AlpacaRawData] = self._tradingClient.get_orders(filter=queryFilters)

        # Iterate through and format them into models
        output: list[BaseOrderResult] = [self._formattedOrderListGenerator(currentOrder=currentOrder) for currentOrder in ordersList]

        # Return formatted list
        return output

    def getAllOrders(self) -> list[BaseOrderResult]:
        # Filter for open orders and orders of the current symbol only
        queryFilters = GetOrdersRequest(
            status=AlpacaTradingEnums.QueryOrderStatus.ALL,
            symbols=[self.options.tradingPair])

        # Execute query
        ordersList: Union[list[AlpacaOrder], AlpacaRawData] = self._tradingClient.get_orders(filter=queryFilters)

        # Iterate through and format them into models
        output: list[BaseOrderResult] = [self._formattedOrderListGenerator(currentOrder=currentOrder) for currentOrder in ordersList]

        # Return formatted list
        return output
    
    # TODO: Should this be a standard method for all connectors, instead of a private utility method?
    @generalErrorHandlerDecorator
    def _getAssetInfo(self, assetNameOrId) -> AlpacaAsset:
        output = self._tradingClient.get_asset(symbol_or_asset_id=assetNameOrId)
        if (isinstance(output, Dict)):
            raise UnexpectedOutputType
        return output
    
    def _convertTimeFrame(
            self,
            timeframe: HermesTimeFrame) -> AlpacaTimeFrame:
        # TODO: Completely wrong, needs to be fixed. Currently, it tries to give the unit only, but also it retrieves that though the Alpaca's TimeFrame class, which by default yields an amount of 1 unit.
        tf = None
        match timeframe.unit:
            case HermesTimeframeUnit.WEEK:
                tf = AlpacaTimeFrame(
                    amount=timeframe.amount,
                    unit=AlpacaTimeFrameUnit.Week)
            case HermesTimeframeUnit.DAY:
                tf = AlpacaTimeFrame(
                    amount=timeframe.amount,
                    unit=AlpacaTimeFrameUnit.Day)
            case HermesTimeframeUnit.HOUR:
                tf = AlpacaTimeFrame(
                    amount=timeframe.amount,
                    unit=AlpacaTimeFrameUnit.Hour)
            case HermesTimeframeUnit.MINUTE:
                tf = AlpacaTimeFrame(
                    amount=timeframe.amount,
                    unit=AlpacaTimeFrameUnit.Minute)
            case _:
                raise NonStandardInput
        
        return tf

    def _endDateConverter(self, startDate: datetime, tf: AlpacaTimeFrame):
        endDate = None
        offsetDelta = None
        match tf.unit:
            case AlpacaTimeFrameUnit.Hour:
                offsetDelta = relativedelta(hours=tf.amount)
            case AlpacaTimeFrameUnit.Minute:
                offsetDelta = relativedelta(minutes=tf.amount)
            case AlpacaTimeFrameUnit.Day:
                offsetDelta = relativedelta(days=tf.amount)
            case AlpacaTimeFrameUnit.Week:
                offsetDelta = relativedelta(weeks=tf.amount)
            case AlpacaTimeFrameUnit.Month:
                offsetDelta = relativedelta(months=tf.amount)
            case _:
                raise UnsupportedParameterValue
        
        endDate = startDate + offsetDelta
        if endDate != None:
            return endDate
        else:
            raise UnexpectedOutputType
    
    def _rollingFuncCloseTimeConverter(self, startDate):
        return self._endDateConverter(
            startDate=startDate,
            tf=self._requestAlpacaTimeFrame)

    def historicData(self):
        rawBarsResponse: None | AlpacaBarSet | AlpacaRawData = None
        reqStartDate = self._historicalDataStartDate

        # Construct and initiate data request
        # The asset classes are cheked through the match-case, so the type checker warning are suppressed.
        match self._assetClass:
            case AlpacaTradingEnums.AssetClass.US_EQUITY:
                reqModel = StockBarsRequest(
                    symbol_or_symbols=self.options.tradingPair,
                    timeframe=self._requestAlpacaTimeFrame,
                    start=reqStartDate,
                    limit=int(self.options.limit))
                rawBarsResponse = self._historicalDataClient.get_stock_bars(reqModel) # type: ignore
                # Do something here
            case AlpacaTradingEnums.AssetClass.US_OPTION:
                reqModel = OptionBarsRequest(
                    symbol_or_symbols=self.options.tradingPair,
                    timeframe=self._requestAlpacaTimeFrame,
                    start=reqStartDate,
                    limit=int(self.options.limit))
                rawBarsResponse = self._historicalDataClient.get_option_bars(reqModel) # type: ignore
            case AlpacaTradingEnums.AssetClass.CRYPTO:
                reqModel = CryptoBarsRequest(
                    symbol_or_symbols=self.options.tradingPair,
                    timeframe=self._requestAlpacaTimeFrame,
                    start=reqStartDate,
                    limit=int(self.options.limit))
                rawBarsResponse = self._historicalDataClient.get_crypto_bars(reqModel) # type: ignore
            case _:
                raise NonStandardInput
        
        # Process the recieved data
        if (isinstance(rawBarsResponse, AlpacaBarSet) != True) or (isinstance(rawBarsResponse, Dict)):
            raise UnexpectedOutputType
        
        # Convert BarSet to a pandas DataFrame and process it
        rawDataFrame: pd.DataFrame = rawBarsResponse.df
        # Reset the `symbol` index
        rawDataFrame.reset_index("symbol", inplace=True)
        # Drop the `symbol` column
        rawDataFrame.drop("symbol", axis=1, inplace=True)

        # TODO: Convert into the usual hermes format DataFrame
        # Since we already have a DataFrame at hand, it would be pointless to create a new one.
        # Instead, all the extra columns can be dropped, missing ones can be added, and the existing ones can be named properly.
        # It seems like most of the columns are already there and named correctly anyways, with only the pChange column missing.

        # Drop the extra columns
        rawDataFrame.drop(["trade_count", "vwap"], axis=1, inplace=True)
        # Rename columns
        rawDataFrame.rename(columns={
            "timestamp": "openTime"
        }, inplace=True)
        # Calculate percent change of the close prices
        rawDataFrame["pChange"] = (rawDataFrame["close"].pct_change()) * 100

        # Generate closing times through the open times
        # Problem: Alpaca doesn't return closing times. Thus, we need to take the opening times and add the offset of the candlestick
        # The question: How should we infer the offset? We can either take the Timeframe parameter from the original request directly, or get the offset through the already existing data points (n, n-1).
        # The n, n+1 appraoch fails in the edgecase when only a single candlestick is available
        # Better solution: Instead of relying on other candlesticks, inputting the Timeframe directly and then using that to generate a `relativedelta` seems to be the most sensible option.
        rawDataFrame["closeTime"] = rawDataFrame["openTime"].apply(self._rollingFuncCloseTimeConverter)


    def initiateLiveData(self):
        # Check if an handler was provided
        if (self._wsClient == None):
            # Handler not found, raise an exception
            raise HandlerNonExistent
        
        # Configure WS client
        if (self._assetClass == AlpacaTradingEnums.AssetClass.US_OPTION):
            raise UnsupportedFeature
        
        self._wsClient.subscribe_bars( # type: ignore
            self.wsHandlerInternal, # type: ignore      # TODO: Raw data is not being recieved, the input type should be fine. However, the edge case should be handled in any case.
            self.options.tradingPair)
        
        # Start WS client
        self._wsClient.run()

    def wsHandlerInternal(self, data: Bar) -> None:
        # Calculate epoch for the open time
        openTimeEpoch = (data.timestamp.replace(tzinfo=timezone.utc).timestamp() * 1000)

        # Calculate epoch for the close time        
        closeTime = self._endDateConverter(
            startDate=data.timestamp,
            tf=self._requestAlpacaTimeFrame)
        closeTimeEpoch = (closeTime.replace(tzinfo=timezone.utc).timestamp() * 1000)
        
        formattedBar: LiveMarketData = LiveMarketData(
            openTime=openTimeEpoch,
            openPrice=data.open,
            highPrice=data.high,
            lowPrice=data.low,
            closePrice=data.close,
            closeTime=closeTimeEpoch,
            volume=data.volume)
        
        # TODO: Determine if the current candlestick is new
        # Check the last recorded timestamp against the newly recieved one. If the newly recieved one is higher, a new candlestick had opened.
        candlestickOpened = False
        if (self._lastLiveTimestamp < openTimeEpoch):
            candlestickOpened = True
        self._lastLiveTimestamp = openTimeEpoch
        
        if self.options.dataHandler != None:
            self.options.dataHandler(data=formattedBar, closed=candlestickOpened)