from pydantic import BaseModel


class APIRESPONSE(BaseModel):
    status: bool | None = None
    message: str | None = None
    error: int | None = None
