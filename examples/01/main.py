# Import packages
from portunusConnector import Connector


# Workaround for asyncio supression of KeyboardInterrupt on Windows.
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


# Configuration
exchangeName = 'binance'
credentials = ['', '']
mode = 'live'
tradingPair = 'ETHUSDT'
interval = '1h'
limit = 100


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


a = exchange.account()

print(a)