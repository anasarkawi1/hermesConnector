


from models_utilities import HermesBaseModel
from datetime import datetime


class ClockReturnModel(HermesBaseModel):
    isOpen                  : bool
    nextOpen                : datetime
    nextClose               : datetime
    currentTimestamp        : datetime