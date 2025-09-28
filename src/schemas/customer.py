from typing import Optional

from pydantic import BaseModel, ConfigDict
from src.schemas.api_response import APIRESPONSE

class Customer(BaseModel):
    customer_id: Optional[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    credit_limit: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class CustomerResponseData(APIRESPONSE):
    data: list[Customer] | Customer = None

    model_config = ConfigDict(from_attributes=True, extra='allow')
