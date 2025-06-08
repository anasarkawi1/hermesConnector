


from abc import ABC, abstractmethod

from pandas import DataFrame
from hermesConnector.hermes_exceptions import InsufficientParameters
from datetime import datetime
import typing_extensions as typing
from typing import Optional, Any, Callable, Union

from hermesConnector.models import BaseOrderResult, ClockReturnModel, LimitOrderBaseParams, LimitOrderResult, MarketOrderNotionalParams, MarketOrderQtyParams, MarketOrderResult
from hermesConnector.models_utilities import HermesBaseModel
from hermesConnector.timeframe import TimeFrame


class ConnectorOptions(HermesBaseModel):
    tradingPair         : str
    interval            : TimeFrame
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
    def marketOrderCost(
        self,
        orderParams: MarketOrderNotionalParams) -> MarketOrderResult:
        """
            Submits a market order based on the notional value of the order's base asset.
            
            Parameters
            ----------
            orderParams: MarketOrderNotionalParams
                Order parameters and input as a HermesBaseModel.

            Returns
            -------
            MarketOrderReturn
                Return of the exchange response, standardised as a HermesBaseModel.
        """
        pass
    
    @abstractmethod
    def limitOrder(
        self,
        orderParams: LimitOrderBaseParams) -> LimitOrderResult:
        """
            Submits a limit order based on the quantity of the base asset.
            
            Parameters
            ----------
            orderParams: LimitOrderBaseParams
                Order parameters and input as a HermesBaseModel.

            Returns
            -------
            LimitOrderReturn
                Return of the exchange response, standardised as a HermesBaseModel.
        """
        pass

    # TODO: Determine the outpur type
    @abstractmethod
    def queryOrder(
        self,
        orderId: str) -> BaseOrderResult:
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
    def cancelOrder(
        self,
        orderId: str) -> bool:
        """
            Cancels the order with the given `orderId`.
            
            Parameters
            ----------
            orderId: str
                ID of the order to be cancelled.

            Returns
            -------
            boolean
                Returns `True` if the cancellation was a success, `False` if the cancellation failed, but not due to a failure.
        """
        pass
    
    @abstractmethod
    def currentOrders(self) -> list[BaseOrderResult]:
        """
            Returns a list of the currently open orders.

            Returns
            -------
            list[BaseOrderResult]
                List of the currently open orders
        """
        pass
    
    @abstractmethod
    def getAllOrders(self):
        """
            Returns a list of the last 50 submitted orders, open or otherwise.

            Returns
            -------
            list[BaseOrderResult]
                List of the last 50 submitted orders, open or otherwise.
        """
        pass
    
    @abstractmethod
    def historicData(self) -> DataFrame:
        """
            Requests, formats, and returns a Pandas Dataframe of the price data of the selected asset.

            The DataFrame contains the following columns:
                `['openTime', 'open', 'high', 'low', 'close', 'volume', 'pChange', 'closeTime']`
            
            Returns
            -------
            DataFrame
                A Pandas DataFrame of the price data of the asset.
        """
        pass
    
    @abstractmethod
    def initiateLiveData(self) -> None:
        pass

    @abstractmethod
    def wsHandlerInternal(self):
        """
            Handles the raw data of the order and passes
        """
        pass
