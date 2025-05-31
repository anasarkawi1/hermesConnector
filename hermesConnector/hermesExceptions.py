from typing_extensions import Literal
from typing import Union



genericErrStr = Literal[
    "UNKNOWN_ERR",
    "INTERNAL_CON_ERR",
    "TOO_MANY_REQUESTS",
    "REQUEST_TIMEOUT",
    "WS_HANDLER_NX",
    "AUTHORISATION_FAILED",
    "INSUFFICIENT_PARAMETERS",
    "NON_STANDARD_PARAMETER_GIVEN",
    "UNEXPECTED_OUTPUT_TYPE",
    "UNSUPPORTED_PARAMETER_INPUT",
    "TARGET_CLIENT_INITIATION",
    "UNEXPECTED_INPUT",
    "UNSUPPORTED_FEATURE"
]
orderErrStr = Literal[
    "UNKNOWN_ORDER_ERR",
    "ORDER_FAILED_TO_SEND",
    "ORDER_REJECTED_GENERAL",
]
accountErrStr = Literal[
    "INSUFFICIENT_BALANCE",
]


# Base exception
class HermesBaseException(Exception):
    errCode         : int
    errStr          : Union[genericErrStr, orderErrStr, accountErrStr]


#
# Errors are grouped into seperated related groups using the error codes:
#       1xxx: Generic, platform related errors (network, unknown, etc.)
#       2xxx: Order related errors
#       3xxx: Account related errors
#


#
# Generic errors
#

# Unknown generic error
class UnknownGenericHermesException(HermesBaseException):
    errCode     = 1000
    errStr      = "UNKNOWN_ERR"

# Authorisation failure
class AuthFailed(HermesBaseException):
    errCode     = 1002
    errStr      = "AUTHORISATION_FAILED"

# Insufficient parameters
class InsufficientParameters(HermesBaseException):
    errCode     = 1003
    errStr      = "INSUFFICIENT_PARAMETERS"

# Internal connection error
class InternalConnectionError(HermesBaseException):
    errCode     = 1006
    errStr      = "INTERNAL_CON_ERR"

# Too many requests
class TooManyRequests(HermesBaseException):
    errCode     = 1007
    errStr      = "TOO_MANY_REQUESTS"

# Request timeout
class RequestTimeout(HermesBaseException):
    errCode     = 1008
    errStr      = "REQUEST_TIMEOUT"

class HandlerNonExistent(HermesBaseException):
    errCode     = 1009
    errStr      = "WS_HANDLER_NX"

class NonStandardInput(HermesBaseException):
    errCode     = 1010
    errStr      = "NON_STANDARD_PARAMETER_GIVEN"

class UnexpectedOutputType(HermesBaseException):
    errCode     = 1011
    errStr      = "UNEXPECTED_OUTPUT_TYPE"

class UnsupportedParameterValue(HermesBaseException):
    errCode     = 1012
    errStr      = "UNSUPPORTED_PARAMETER_INPUT"

class TargetClientInitiationError(HermesBaseException):
    errCode     = 1013
    errStr      = "TARGET_CLIENT_INITIATION"

class UnexpectedInput(HermesBaseException):
    errCode     = 1014
    errStr      = "UNEXPECTED_INPUT"

class UnsupportedFeature(HermesBaseException):
    errCode     = 1015
    errStr      = "UNSUPPORTED_FEATURE"

#
# Order errors 
#

# Generic order error
class GenericOrderError(HermesBaseException):
    errCode     = 2000
    errStr      = "UNKNOWN_ORDER_ERR"

# Order sending failed
class OrderFailedToSend(HermesBaseException):
    errCode     = 2004
    errStr      = "ORDER_FAILED_TO_SEND"

# Order rejected
class OrderRejected(HermesBaseException):
    errCode     = 2005
    errStr      = "ORDER_REJECTED_GENERAL"


#
# Account errors
#

# Insufficient Balance
class InsufficientBalance(HermesBaseException):
    errCode     = 3001
    errStr      = "INSUFFICIENT_BALANCE"