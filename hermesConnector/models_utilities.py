#
# Model Utilities and Common Definitions
# By Anas Arkawi, 2025.
#


# Module imports
from pydantic import BaseModel, ConfigDict
from pprint import pprint


# Base model definition

class HermesBaseModel(BaseModel):

    model_config = ConfigDict(arbitrary_types_allowed=True)

    # def __repr__(self):
    #     pass