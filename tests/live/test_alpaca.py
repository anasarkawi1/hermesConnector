# Hermes Test Scripts
# By Anas Arkawi, 2025.


# Import Hermes Library
from hermesConnector import Connector
from hermesConnector.timeframe import TimeFrame
from hermesConnector.hermes_enums import TimeframeUnit


# Import libraries
import os
import sys
from dotenv import load_dotenv
from datetime import datetime
import warnings


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

def getClient():
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

def test_exchangeClock():
    exchange = getClient()
    clock = exchange.exchangeClock()

    # Check for the property types
    assert ((clock.isOpen == True) or (clock.isOpen == False))
    assert isinstance(clock.nextOpen, datetime)
    assert isinstance(clock.nextClose, datetime)
    assert isinstance(clock.currentTimestamp, datetime)

def test_marketOrderQty():
    pass

def test_marketOrderCost():
    pass

def test_limitOrder():
    pass

def test_queryOrder()    :
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
    pass

def test_wsHandlerInternal():
    pass
