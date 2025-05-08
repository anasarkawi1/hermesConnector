


from abc import ABC, abstractmethod
from hermesConnector.hermesExceptions import InsufficientParameters
from pydantic import BaseModel
from datetime import datetime

from hermesConnector.models import ClockReturnModel


class ConnectorOptions(BaseModel):
    tradingPair         : str
    interval            : str
    limit               : str
    mode                : str
    columns             : any | None
    dataHandler         : callable | None


class ConnectorTemplate(ABC):

    def __init__(
            self,
            tradingPair,
            interval,
            mode='live',
            limit=75,
            credentials=["", ""],
            columns=None,
            wshandler=None):
        
        # Check if the credentials were provided
        if (credentials[0] == "" or credentials[1] == ""):
            raise InsufficientParameters
        
        # Make paramters available to the instance
        self.options: ConnectorOptions = ConnectorOptions(
            tradingPair=tradingPair,
            interval=interval,
            limit=limit,
            mode=mode,
            columns=columns,
            dataHandler=wshandler)

    @abstractmethod
    def exchangeClock(self) -> ClockReturnModel:
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def buy(self):
        pass
    
    @abstractmethod
    def sell(self):
        pass

    @abstractmethod
    def buyCost(self):
        pass

    @abstractmethod
    def sellCost(self):
        pass
    
    @abstractmethod
    def buyLimit(self):
        pass

    @abstractmethod
    def sellLimit(self):
        pass

    @abstractmethod
    def queryOrder(self):
        pass
    
    @abstractmethod
    def cancelOrder(self):
        pass
    
    @abstractmethod
    def currentOrder(self):
        pass
    
    @abstractmethod
    def getAllOrders(self):
        pass
    
    @abstractmethod
    def historicData(self):
        pass
    
    @abstractmethod
    def initiateLiveData(self):
        pass

    @abstractmethod
    def wsHandlerInternal(self):
        pass
