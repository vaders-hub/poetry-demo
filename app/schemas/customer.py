from pydantic import BaseModel, ConfigDict

from app.schemas.api_response import APIRESPONSE


class Customer(BaseModel):
    customer_id: str
    name: str
    address: str | None = None
    website: str | None = None
    credit_limit: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CustomerResponseData(APIRESPONSE):
    data: list[Customer] | Customer = None

    model_config = ConfigDict(from_attributes=True, extra="allow")
