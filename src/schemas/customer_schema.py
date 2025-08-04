from typing import Optional

from pydantic import BaseModel, ConfigDict


class CustomerSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    credit_limit: Optional[int] = None
