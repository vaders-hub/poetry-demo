from typing import Optional, Required

from pydantic import BaseModel, ConfigDict


class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    customer_id: Required[int] = None
    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    credit_limit: Optional[int] = None
