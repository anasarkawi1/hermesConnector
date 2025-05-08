#
# Model Utilities and Common Definitions
# By Anas Arkawi, 2025.
#


# Module imports
from pydantic import BaseModel
from pprint import pprint


# Base model definition

class HermesBaseModel(BaseModel):

    def __repr__(self):
        pass