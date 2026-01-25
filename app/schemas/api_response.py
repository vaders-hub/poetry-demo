from typing import Optional

from pydantic import BaseModel


class APIRESPONSE(BaseModel):
    status: Optional[bool] = None
    message: Optional[str] = None
    error: Optional[int] = None
