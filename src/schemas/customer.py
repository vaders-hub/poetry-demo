from typing import Annotated, Optional, Required

from pydantic import AfterValidator, BaseModel, ConfigDict, ValidationError
from src.schemas.api_response import APIRESPONSE

def is_null(value: int) -> int:
    if value is None:
        raise ValueError(f'{value} is null')
    return value

class Customer(BaseModel):
    customer_id: Annotated[int, AfterValidator(is_null)]
    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    credit_limit: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class CustomerResponseData(APIRESPONSE):
    data: list[Customer] | Customer = None

    model_config = ConfigDict(from_attributes=True, extra='allow')
