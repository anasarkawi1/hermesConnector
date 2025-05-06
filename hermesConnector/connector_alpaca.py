# Connector library for Alpaca API
# By Anas Arkawi, 2025.


# Load modules
from hermesConnector.hermesExceptions import InsufficientParameters, HandlerNonExistent

# Alpaca Imports
from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from alpaca.data.models.bars import Bar



class Alpaca:

    def __init__(
            self,
            mode='live',
            tradingPair=None,
            interval=None,
            limit=75,
            credentials=["", ""],
            columns=None,
            wshandler=None):
        
        # Check if the credentials were provided
        if (credentials[0] == "" or credentials[1] == ""):
            raise InsufficientParameters
        
        # Initialise live or paper trading client
        client = None
        if mode == 'live':
            client = TradingClient(credentials[0], credentials[1])
        elif mode == 'test':
            client = TradingClient(credentials[0], credentials[1], paper=True)
        
        # Clients dictionary
        self.clients: dict[str, TradingClient | StockDataStream] = {
            "trading"       : client,
            "ws"            : None
        }

        # Initialise WS client
        if wshandler != None:
            self.clients["ws"] = StockDataStream(credentials[0], credentials[1])
        
        # Store options
        self.options = {
            "tradingPair": tradingPair,
            "interval": interval,
            "limit": limit,
            "mode": mode,
            "handler": wshandler,
            "columns": columns,
            "dataHandler": wshandler
        }


    def stop(self):
        pass

    def account(self):
        pass

    def apiRestriction(self):
        pass

    def buy():
        pass
    
    def sell():
        pass

    def buyCost():
        pass

    def sellCost(self):
        pass

    def buyLimit(self):
        pass

    def sellLimit(self):
        pass

    def queryOrder(self):
        pass

    def cancelOrder(self):
        pass

    def currentOrder():
        pass

    def getAllOrders():
        pass

    def historicData():
        pass

    def initiateLiveData(self):
        # Check if an handler was provided
        if (self.clients["ws"] == None):
            # Handler not found, raise an exception
            raise HandlerNonExistent
        
        # Configure WS client
        self.clients["ws"].subscribe_bars(
            self.wsHandlerInternal,
            self.options["tradingPair"])
        
        # Start WS client
        self.clients["ws"].run()

    def wsHandlerInternal():
        pass
