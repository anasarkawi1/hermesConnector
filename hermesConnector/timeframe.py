


from hermesConnector.hermes_enums import TimeframeUnit


class TimeFrame:

    _amount      : int
    _unit        : TimeframeUnit

    def __init__(
            self,
            amount: int,
            unit: TimeframeUnit):
        
        self._amount      = amount
        self._unit        = unit
    

    @property
    def amount(self) -> int:
        return self._amount
    
    @property
    def unit(self):
        return self._unit