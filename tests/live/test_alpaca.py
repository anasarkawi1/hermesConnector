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
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide as AlpacaOrderSide, TimeInForce as AlpacaTIF, OrderStatus as AlpacaOrderStatus

# Import libraries
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import warnings
import json
from pprint import pprint


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
limit = "100"


@pytest.fixture
def exchange():
    exchange = Connector(
    exchange='alpaca',
    credentials=credentials,
    options={
        "mode": mode,
        "tradingPair": tradingPair,
        "interval": tf,
        "limit": limit,
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
    

def test_currentOrder():
    pass

def test_getAllOrders():
    pass

def test_historicData():
    pass

def test_initiateLiveData():
    '''
        Note: Live data tests are currently done by hand.
    '''
    pass

def test_wsHandlerInternal():
    '''
        Note: Live data tests are currently done by hand.
    '''
    pass
