from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.api_response import APIRESPONSE


class Customer(BaseModel):
    customer_id: int
    name: str
    address: Optional[str] = None
    website: Optional[str] = None
    credit_limit: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class CustomerResponseData(APIRESPONSE):
    data: list[Customer] | Customer

    model_config = ConfigDict(from_attributes=True, extra="allow")
