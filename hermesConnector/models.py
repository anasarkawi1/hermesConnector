


from pydantic import BaseModel
from datetime import datetime


class ClockReturnModel(BaseModel):
    isOpen                  : bool
    nextOpen                : datetime
    nextClose               : datetime
    currentTimestamp        : datetime