# Hermes Test Scripts
# By Anas Arkawi, 2025.

# Import Hermes Library
from typing import Dict
import pytest
from hermesConnector import Connector
from hermesConnector.models import BaseOrderResult, LimitOrderBaseParams, MarketOrderNotionalParams, MarketOrderQtyParams
from hermesConnector.timeframe import TimeFrame
from hermesConnector.hermes_enums import OrderStatus, OrderType, TimeframeUnit, OrderSide, TimeInForce
from hermesConnector.connector_alpaca import Alpaca

# Import Alpaca Modules
from alpaca.data.requests import StockLatestQuoteRequest
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest, GetOrdersRequest
from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce as AlpacaTIF, OrderStatus as AlpacaOrderStatus, QueryOrderStatus as AlpacaQueryOrderStatus
from alpaca.trading.models import Order as AlpacaOrder

# Import libraries
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import warnings
import json
from pprint import pprint
from pandas import DataFrame


# Add Hermes source into sys.path to be access later on
cwd = os.getcwd()
sys.path.append(cwd)


# Load envirnoment
load_dotenv()

# Client configuration
credentials = [os.getenv('ALPACA_PAPER_KEY'), os.getenv('ALPACA_PAPER_SECRET')]
mode = 'live'
tradingPair = 'AAPL'
tf = TimeFrame(1, TimeframeUnit.DAY)
dataPointsLimit = "100"


@pytest.fixture
def exchange():
    exchange = Connector(
    exchange='alpaca',
    credentials=credentials,
    options={
        "mode": mode,
        "tradingPair": tradingPair,
        "interval": tf,
        "limit": dataPointsLimit,
        "columns": None,
        "dataHandler": lambda _, x, y: None,
    }).exchange

    return exchange


#
# Utilities
#

def cleanUpOrder(exchange, testOrderId, testOrderSide):
    currentOrder = exchange._tradingClient.get_order_by_id(order_id=testOrderId)
    if (isinstance(currentOrder, Dict)):
        raise TypeError
    
    # Check if the order was partially filled, if so, submit an order against the filled amount
    if (currentOrder.status == AlpacaOrderStatus.FILLED) or (currentOrder.status == AlpacaOrderStatus.PARTIALLY_FILLED):
        # Process the quantity of filled portion of the test order
        filledQty = None
        if (currentOrder.filled_qty == None):
            raise ValueError
        else:
            filledQty = float(currentOrder.filled_qty)

        # Determine the opposite side of the trade
        cleanUpOrderSide = None
        if (testOrderSide == AlpacaOrderSide.BUY):
            cleanUpOrderSide = AlpacaOrderSide.SELL
        elif (testOrderSide == AlpacaOrderSide.SELL):
            cleanUpOrderSide = AlpacaOrderSide.BUY
        else:
            raise ValueError
        

        # Construct and submit the order
        cleanUpOrderReq = MarketOrderRequest(
            symbol=tradingPair,
            qty=filledQty,
            side=cleanUpOrderSide,
            time_in_force=AlpacaTIF.DAY)
        cleanUpOrder = exchange._tradingClient.submit_order(cleanUpOrderReq)
    
    # The order was not filled, try to cancel it.
    else:
        exchange._tradingClient.cancel_order_by_id(testOrderId)


def orderFieldsCommonTests(order: BaseOrderResult):
    # Check Hermes Enum fields
    assert isinstance(order.side, OrderSide)
    assert isinstance(order.type, OrderType)
    assert isinstance(order.status, OrderStatus)
    
    rawJSON = order.raw

    # Check if the field is even populated at all
    assert len(rawJSON) > 0

    # Check if the JSON is valid, if not raise AssertionError
    try:
        json.loads(rawJSON)
    except json.JSONDecodeError:
        raise AssertionError
    except UnicodeDecodeError:
        raise AssertionError


#
# Tests
#

def test_generalTest():
    warnings.warn("There are no general tests implemented yet. General tests meant to test cases common to all methods should be looked into (None inputs etc.)")


def test_exchangeClock(exchange):
    clock = exchange.exchangeClock()

    # Check for the property types
    assert ((clock.isOpen == True) or (clock.isOpen == False))
    assert isinstance(clock.nextOpen, datetime)
    assert isinstance(clock.nextClose, datetime)
    assert isinstance(clock.currentTimestamp, datetime)


def test_marketOrderQty(exchange: Alpaca):
    '''
        Tests for the desired behaviour of `marketOrderQty` method, with the assumption that a correct input was given.
    '''

    # TODO: add cases for other `OrderSide` and `TimeInForce` parameters

    orderParams = MarketOrderQtyParams(
        side=OrderSide.BUY,
        tif=TimeInForce.DAY,
        qty=1)
    
    # Submit order
    order = exchange.marketOrderQty(orderParams=orderParams)

    # Test order return
    orderFieldsCommonTests(order=order)

    # Clean up order
    cleanUpOrder(
        exchange=exchange,
        testOrderId=order.order_id,
        testOrderSide=AlpacaOrderSide.BUY)


def test_marketOrderCost(exchange: Alpaca):
    
    # TODO: The cost here could lead to fractional orders, which could be rejected. Elaborate on testing here, for now, this is sufficient.
    orderParams = MarketOrderNotionalParams(
        side=OrderSide.BUY,
        tif=TimeInForce.DAY,
        cost=2000)
    
    # Submit order
    order = exchange.marketOrderCost(orderParams=orderParams)

    # Test order result
    orderFieldsCommonTests(order=order)

    # Clean up order
    cleanUpOrder(
        exchange=exchange,
        testOrderId=order.order_id,
        testOrderSide=AlpacaOrderSide.BUY)


def test_limitOrder(exchange: Alpaca):

    # For testing purposes retrieve the latest price directly
    quoteReqParams = StockLatestQuoteRequest(
        symbol_or_symbols=tradingPair)
    latestQuote = exchange._historicalDataClient.get_stock_latest_quote(quoteReqParams) # type: ignore

    latestAskPrice = float(latestQuote[tradingPair].ask_price)
    limitPrice = latestAskPrice - 10
    testOrderSide = OrderSide.BUY

    orderParams = LimitOrderBaseParams(
        side=testOrderSide,
        tif=TimeInForce.DAY,
        qty=1,
        limitPrice=limitPrice)
    
    # Submit order
    order = exchange.limitOrder(orderParams=orderParams)

    # test order
    orderFieldsCommonTests(order=order)

    # Clean up order
    cleanUpOrder(
        exchange=exchange,
        testOrderId=order.order_id,
        testOrderSide=testOrderSide)


def test_queryOrder(exchange: Alpaca):
    
    # For testing pruposes, place an order directly
    testOrderSide = AlpacaOrderSide.BUY
    testOrderReq = MarketOrderRequest(
       symbol=tradingPair,
       qty=1,
       side=testOrderSide,
       time_in_force=AlpacaTIF.DAY)
    
    order = exchange._tradingClient.submit_order(testOrderReq)

    # Check if raw data was returned
    if (isinstance(order, Dict)):
        raise TypeError

    testOrderId = str(order.id)
    order = exchange.queryOrder(orderId=testOrderId)

    orderFieldsCommonTests(order=order)

    # Cleanup, cancel order or resell asset
    cleanUpOrder(
        exchange=exchange,
        testOrderId=testOrderId,
        testOrderSide=testOrderSide)


def test_cancelOrder(exchange: Alpaca):
    # 1. Create a test order.
    # 2. Cancel the order through Hermes.
    # 3. Check the order status through the Alpaca API directly.

    # Create and submit test order
    testOrderSide = AlpacaOrderSide.BUY
    testOrderReq = MarketOrderRequest(
        symbol=tradingPair,
        qty=1,
        side=testOrderSide,
        time_in_force=AlpacaTIF.DAY)
    
    testOrder = exchange._tradingClient.submit_order(testOrderReq)
    if (isinstance(testOrder, Dict)):
        raise ValueError


    # Attempt to cancel the order through Hermes
    testOrderId = str(testOrder.id)
    result = exchange.cancelOrder(testOrderId)

    # Order cancellation failed due to the order status. Confirm the status and continue
    if (result == False):
        assert testOrder.status == AlpacaOrderStatus.CANCELED
        assert testOrder.status == AlpacaOrderStatus.FILLED
        assert testOrder.status == AlpacaOrderStatus.EXPIRED
    else:
        # Confirm order details
        queriedOrder = exchange._tradingClient.get_order_by_id(testOrderId)
        if (isinstance(queriedOrder, Dict)):
            raise ValueError
        
        # Check if the order is in fact cancelled
        assert queriedOrder.status == AlpacaOrderStatus.CANCELED
    

def test_currentOrders(exchange: Alpaca):

    # For testing purposes retrieve the latest price directly
    quoteReqParams = StockLatestQuoteRequest(
        symbol_or_symbols=tradingPair)
    latestQuote = exchange._historicalDataClient.get_stock_latest_quote(quoteReqParams) # type: ignore

    latestAskPrice = float(latestQuote[tradingPair].ask_price)

    testOrdersSide = AlpacaOrderSide.BUY
    limitPrices = [
        (latestAskPrice - 40),
        (latestAskPrice - 30),
        (latestAskPrice - 20),
        ]
    
    while (limitPrices[0] <= 0):
        limitPrices.pop(0)

    # Get the current number of open orders before proceeding
    alreadyOpenOrders = exchange._tradingClient.get_orders()
    alreadyOpenOrdersNum = len(alreadyOpenOrders)
    
    submittedOrders: list[AlpacaOrder] = []
    for price in limitPrices:
        orderReq = LimitOrderRequest(
            symbol=tradingPair,
            qty=1,
            limit_price=price,
            side=testOrdersSide,
            time_in_force=AlpacaTIF.DAY)
        order = exchange._tradingClient.submit_order(orderReq)
        if (isinstance(order, Dict)):
            raise TypeError
        submittedOrders.append(order)
    
    # currentPositions = exchange._tradingClient.get_orders()
    currentPositions = exchange.currentOrders()

    # Print diagnostic information
    print(f"Already Open Orders: {alreadyOpenOrdersNum}")
    print(f"Created Open Orders: {len(limitPrices)}")
    print(f"Recieved Open Orders: {len(currentPositions)}")

    # Perform tests on the request itself
    assert (len(limitPrices) + alreadyOpenOrdersNum) == len(currentPositions)

    # Perform tests on the individual orders
    for recvOrder in currentPositions:
        orderFieldsCommonTests(recvOrder)
    
    # Clean up orders
    for order in submittedOrders:
        orderId = order.id
        orderSide = order.side
        cleanUpOrder(exchange, orderId, orderSide)

def test_getAllOrders(exchange: Alpaca):
    # TODO: Implement the same tests as the `currentOrders` in addition to orders that would be filled, etc.

    # For testing purposes retrieve the latest price directly
    quoteReqParams = StockLatestQuoteRequest(
        symbol_or_symbols=tradingPair)
    latestQuote = exchange._historicalDataClient.get_stock_latest_quote(quoteReqParams) # type: ignore

    latestAskPrice = float(latestQuote[tradingPair].ask_price)
    testOrdersSide = AlpacaOrderSide.BUY
    submittedOrders: list[AlpacaOrder] = []

    # Get the current number of orders before proceeding
    existingOrdersReq = GetOrdersRequest(
        status=AlpacaQueryOrderStatus.ALL,
        symbols=[tradingPair])
    existingOrders = exchange._tradingClient.get_orders(filter=existingOrdersReq)

    # This is irrelevant for this test as the max number of orders is 500. Non-open orders can be way past that
    existingOrdersNum = len(existingOrders)

    #
    # Prepare the Market order
    #
    marketOrderReq = MarketOrderRequest(
        symbol=tradingPair,
        qty=1,
        side=AlpacaOrderSide.BUY,
        time_in_force=AlpacaTIF.DAY)
    marketOrder = exchange._tradingClient.submit_order(marketOrderReq)
    if (isinstance(marketOrder, Dict)):
        raise TypeError
    submittedOrders.append(marketOrder)

    #
    # Prepare the limit orders
    #

    limitPrices = [
        (latestAskPrice - 40),
        (latestAskPrice - 30),
        (latestAskPrice - 20)
        ]
    
    # If all prices are invalid, an IndexError will be thrown.
    while (limitPrices[0] <= 0):
        limitPrices.pop(0)

    
    for price in limitPrices:
        orderReq = LimitOrderRequest(
            symbol=tradingPair,
            qty=1,
            limit_price=price,
            side=testOrdersSide,
            time_in_force=AlpacaTIF.DAY)
        order = exchange._tradingClient.submit_order(orderReq)
        if (isinstance(order, Dict)):
            raise TypeError
        submittedOrders.append(order)
    
    # currentPositions = exchange._tradingClient.get_orders()
    currentPositions = exchange.getAllOrders()

    # Print diagnostic information
    orderPairs = [
        (currentPositions[3].order_id, str(submittedOrders[0].id)),
        (currentPositions[2].order_id, str(submittedOrders[1].id)),
        (currentPositions[1].order_id, str(submittedOrders[2].id)),
        (currentPositions[0].order_id, str(submittedOrders[3].id))
        ]

    for pair in orderPairs:
        assert pair[0] == pair[1]

    # Perform tests on the individual orders
    for recvOrder in currentPositions:
        orderFieldsCommonTests(recvOrder)
    
    # Clean up orders
    for order in submittedOrders:
        orderId = order.id
        orderSide = order.side
        cleanUpOrder(exchange, orderId, orderSide)

def test_historicData(exchange: Alpaca):
    # The test checks the following:
    # 1. If the columns are correct
    # 2. The size of the DataFrame
    # 3. Continuity of dates (equal distances apart)
    # 4. Continuity of last date and n-1 date

    df: DataFrame = exchange.historicData()

    #
    # 1. Check if the columns are correct
    # 

    # Define rempalte columns and retrieve the dolumns of the DataFrame
    templateColumns = ['openTime', 'open', 'high', 'low', 'close', 'volume', 'pChange', 'closeTime']
    dataFrameColumns = df.columns

    # Check if the number is correct, raise directly if not, without the rest of the checks.
    if (len(dataFrameColumns) != len(templateColumns)):
        raise KeyError
    
    # Check if the column name is in the template array
    for column in dataFrameColumns:
        if (column not in templateColumns):
            raise KeyError
    
    #
    # 2. Check if the size of the DataFrame is correct
    #

    dfSize = len(df)
    dfInputSize = int(dataPointsLimit)
    if (dfSize != dfInputSize):
        raise IndexError
    
    #
    # 3. Check the continuity of the dates
    #

    nPoint          = df.iloc[0]
    nLeadPoint      = df.iloc[1]
    timeDiffRef     = nPoint["closeTime"] - nLeadPoint["closeTime"]

    for i in range(len(df)):
        leadPointIndex = (i + 1)
        if (leadPointIndex > len(df) - 1):
            pass
        else:
            nPoint          = df.iloc[i]
            nLeadPoint      = df.iloc[leadPointIndex]
            timeDiff        = nPoint["closeTime"] - nLeadPoint["closeTime"]
            if (timeDiff != timeDiffRef):
                # TODO: Testing this is way more complicated than it should be, due to how calendars work...
                # Weekends, public holidays, and other special dates are edge cases that throw off the time difference alignment, and should be taken into account. For now, the currect tests are more than enough.
                warnings.warn("Weekends, public holidays, and other special dates are edge cases that throw off the time difference alignment, and should be taken into account. For now, the currect tests are more than enough.")
                # raise ValueError
    
    #
    # 4. Check the time difference between indicies of -1 and -2
    #
    
    pointOne        = df.iloc[-1]
    pointTwo        = df.iloc[-2]
    pointThree      = df.iloc[-3]

    timeDiffRef     = pointTwo["closeTime"] - pointThree["closeTime"]
    timeDiff        = pointOne["closeTime"] - pointTwo["closeTime"]

    assert timeDiff == timeDiffRef

def test_utility(exchange: Alpaca):
    cancelResult = exchange._tradingClient.cancel_orders()
    print(cancelResult)

    orders = exchange._tradingClient.get_orders()
    if (isinstance(orders, Dict)):
        raise ValueError
    
    for order in orders:
        print(f'Limit Price: {order.limit_price}')

    print(len(orders))
    pass

def test_initiateLiveData(exchange: Alpaca):
    '''
        Note: Live data tests are currently done by hand.
    '''
    result = exchange._tradingClient.cancel_orders()
    print(result)

def test_wsHandlerInternal():
    '''
        Note: Live data tests are currently done by hand.
    '''
    pass
