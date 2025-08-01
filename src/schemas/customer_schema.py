from typing import Optional

from pydantic import BaseModel, EmailStr


class CustomerSchema(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    website: Optional[str] = None
    credit_limit: Optional[int] = None

    class Config:
        from_attributes = True
