


from abc import ABC, abstractmethod
from hermesConnector.hermesExceptions import InsufficientParameters
from datetime import datetime
import typing_extensions as typing
from typing import Optional, Any, Callable, Union

from hermesConnector.models import BaseOrderResult, ClockReturnModel, MarketOrderQtyParams, MarketOrderResult
from hermesConnector.models_utilities import HermesBaseModel
from hermes_enums import Timeframe


class ConnectorOptions(HermesBaseModel):
    tradingPair         : str
    interval            : Timeframe
    limit               : Union[str, int]
    mode                : str
    columns             : Optional[Any]
    dataHandler         : Optional[Callable]
    credentials         : list


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
            dataHandler=wshandler,
            credentials=credentials)

    @abstractmethod
    def exchangeClock(self) -> ClockReturnModel:
        """
            Returns the current clock and exchagne clock.
            
            Parameters
            ----------
                None
            
            Returns
            -------
                ClockReturnModel
                    Clock information about the exchange as a HermesBaseModel.
        """
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def marketOrderQty(
        self,
        orderParams: MarketOrderQtyParams) -> MarketOrderResult:
        """
            Submits a market order based on the quantity of the base asset.
            
            Parameters
            ----------
            orderParams: MarketOrderQtyParams
                Order parameters and input as a HermesBaseModel.

            Returns
            -------
            MarketOrderReturn
                Return of the exchange response, standardised as a HermesBaseModel.
        """
        pass

    @abstractmethod
    def marketOrderCost(self):
        pass
    
    @abstractmethod
    def limitOrder(self):
        pass

    # TODO: Determine the outpur type
    @abstractmethod
    def queryOrder(self, orderId: str) -> BaseOrderResult:
        """
            Queries a submitted order by the order ID.

            Parameters
            ----------
            orderId: str
                ID string for the order
            
            Returns
            -------
        """
        
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
        """
            Handles the raw data of the order and passes
        """
        pass
