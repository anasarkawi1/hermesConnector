# Hermes Test Scripts
# By Anas Arkawi, 2025.

# Import Hermes Library
import pytest
from hermesConnector import Connector
from hermesConnector.models import BaseOrderResult, LimitOrderBaseParams, MarketOrderNotionalParams, MarketOrderQtyParams
from hermesConnector.timeframe import TimeFrame
from hermesConnector.hermes_enums import OrderStatus, OrderType, TimeframeUnit, OrderSide, TimeInForce
from hermesConnector.connector_alpaca import Alpaca

# Import Alpaca Modules
from alpaca.data.requests import StockLatestQuoteRequest

# Import libraries
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import warnings
import json


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

    orderParams = LimitOrderBaseParams(
        side=OrderSide.BUY,
        tif=TimeInForce.DAY,
        qty=1,
        limitPrice=limitPrice)
    
    # Submit order
    order = exchange.limitOrder(orderParams=orderParams)

    # test order
    orderFieldsCommonTests(order=order)

def test_queryOrder():
    pass

def test_cancelOrder():
    pass

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
