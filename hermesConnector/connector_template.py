


from hermesConnector.hermesExceptions import InsufficientParameters


class Template:

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

        if mode == 'live':
            pass
        elif mode == 'test':
            pass

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

    def initiateLiveData():
        pass

    def wsHandlerInternal():
        pass
