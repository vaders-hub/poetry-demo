from typing import Any, Generic, Optional, TypeVar
from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class ResponseData(BaseModel, Generic[T]):
    data: Optional[T] = None
    message: str = "Success"
    status: bool = True
    status_code: int = 200
    error: Optional[Any] = None


def api_response(
    data: Optional[Any] = None,
    message: str = "Success",
    status: bool = True,
    status_code: int = 200,
    error: Optional[Any] = None,
):
    res = ResponseData(
        data=data,
        message=message,
        status=status,
        status_code=status_code,
        error=error,
    )
    return JSONResponse(
        status_code=status_code,
        content=res.model_dump(),
    )
