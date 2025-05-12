# Import packages
import os
from dotenv import load_dotenv
from pprint import pprint

# Hermes imports
from hermesConnector import Connector
from hermesConnector.connector_template import ConnectorOptions


# Workaround for asyncio supression of KeyboardInterrupt on Windows.
import signal
from hermesConnector.hermes_enums import OrderSide, TimeInForce

from hermesConnector.models import MarketOrderQtyParams, MarketOrderResult
signal.signal(signal.SIGINT, signal.SIG_DFL)


# Load envirnoment
load_dotenv()

# Initialise Alpaca client for historical data
alpacaCreds = {
    "key": os.getenv('ALPACA_PAPER_KEY'),
    "secret": os.getenv('ALPACA_PAPER_SECRET')
}

# CREDNTIALS!!!
credentials = [alpacaCreds["key"], alpacaCreds["secret"]]

# Configuration
exchangeName = 'alpaca'
mode = 'live'
tradingPair = 'AAPL'
interval = '1h'
limit = "100"


exchange = Connector(
    exchange=exchangeName,
    credentials=credentials,
    options={
        "mode": mode,
        "tradingPair": tradingPair,
        "interval": interval,
        "limit": limit,
        "columns": None,
        "dataHandler": lambda _, x, y: None,
    }).exchange


# acc = exchange.account()
clock = exchange.exchangeClock()
pprint(clock)
print('\n\n\n')

print('Submitting Order')
print('****************')

# Construct order
orderReq: MarketOrderQtyParams = MarketOrderQtyParams(
    qty=200.0,
    side=OrderSide.BUY,
    tif=TimeInForce.GTC)

orderResult: MarketOrderResult = exchange.marketOrderQty(orderParams=orderReq)

pprint(orderResult)

exit()