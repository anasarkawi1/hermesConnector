# Import packages
from hermesConnector import Connector


# Workaround for asyncio supression of KeyboardInterrupt on Windows.
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)


# CREDNTIALS!!!
credentials = ['', '']

# Configuration
exchangeName = 'binance'
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


acc = exchange.account()

print(acc)

exit()