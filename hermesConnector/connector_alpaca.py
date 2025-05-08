# Connector library for Alpaca API
# By Anas Arkawi, 2025.


# Load modules
from hermesConnector.hermesExceptions import InsufficientParameters, HandlerNonExistent
from connector_template import ConnectorTemplate

# Alpaca Imports
from alpaca.trading.client import TradingClient
from alpaca.data.live import StockDataStream
from alpaca.data.models.bars import Bar
from alpaca.trading.models import Clock as AlpacaClock

from hermesConnector.models import ClockReturnModel



class Alpaca(ConnectorTemplate):

    def __init__(self):

        # Initialise parent class
        super().__init__()
        
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

    def buy(self):
        pass
    
    def sell(self):
        pass

    def buyCost(self):
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

    def currentOrder(self):
        pass

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
