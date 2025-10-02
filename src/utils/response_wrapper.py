from typing import Any, Generic, Optional, TypeVar

from fastapi.responses import JSONResponse
from pydantic.generics import GenericModel

T = TypeVar("T")


class ResponseData(GenericModel, Generic[T]):
    data: Optional[T] = None
    message: str = "Success"
    status: bool = True
    status_code: int = 200
    error: Optional[Any] = None


# def api_response(
#     data: Optional[Any] = None,
#     message: str = "Success",
#     status: bool = True,
#     status_code: int = 200,
#     error: Optional[Any] = None,
# ):
#     res = ResponseData(
#         data=data,
#         message=message,
#         status=status,
#         status_code=status_code,
#         error=error,
#     )
#     return JSONResponse(
#         status_code=status_code,
#         content=res.dict(),
#     )


# def api_response(
#     data: ResponseData | dict,
#     status_code: int = 200,
# ):
#     if isinstance(data, dict):
#         data = ResponseData(**data)  # dict → Pydantic 모델 변환

#     return JSONResponse(
#         status_code=status_code,
#         content=data.dict(),  # BaseModel → dict 변환
#     )
