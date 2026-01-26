"""
API Response Wrapper

모든 API 응답을 일관된 형식으로 래핑하는 유틸리티
"""

from typing import Any, Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

T = TypeVar("T")


class ResponseData(BaseModel, Generic[T]):
    """표준 API 응답 모델"""

    data: T | None = Field(default=None, description="응답 데이터")
    message: str = Field(default="Success", description="응답 메시지")
    status: bool = Field(default=True, description="성공 여부")
    error: Any | None = Field(default=None, description="에러 정보")

    # 추가 메타데이터 (선택사항)
    execution_time_ms: float | None = Field(
        default=None, description="실행 시간 (밀리초)"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="추가 메타데이터")


def api_response(
    data: Any | None = None,
    message: str = "Success",
    status: bool = True,
    status_code: int = 200,
    error: Any | None = None,
    execution_time_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
):
    """
    API 응답 래퍼 함수

    Args:
        data: 응답 데이터
        message: 응답 메시지
        status: 성공 여부 (True/False)
        status_code: HTTP 상태 코드
        error: 에러 정보 (실패 시)
        execution_time_ms: 실행 시간 (밀리초)
        metadata: 추가 메타데이터

    Returns:
        JSONResponse: 표준 형식의 JSON 응답

    Example:
        >>> return api_response(
        ...     data={"user_id": 123, "name": "John"},
        ...     message="User retrieved successfully",
        ...     execution_time_ms=45.67
        ... )
    """
    response_data = ResponseData(
        data=data,
        message=message,
        status=status,
        error=error,
        execution_time_ms=execution_time_ms,
        metadata=metadata,
    )

    # None 값 제거 (응답 크기 최소화)
    content = response_data.model_dump(exclude_none=True)

    return JSONResponse(
        status_code=status_code,
        content=content,
    )


def success_response(
    data: Any | None = None,
    message: str = "Success",
    execution_time_ms: float | None = None,
    metadata: dict[str, Any] | None = None,
):
    """성공 응답 헬퍼 (200 OK)"""
    return api_response(
        data=data,
        message=message,
        status=True,
        status_code=200,
        execution_time_ms=execution_time_ms,
        metadata=metadata,
    )


def created_response(
    data: Any | None = None,
    message: str = "Created",
    execution_time_ms: float | None = None,
):
    """생성 성공 응답 (201 Created)"""
    return api_response(
        data=data,
        message=message,
        status=True,
        status_code=201,
        execution_time_ms=execution_time_ms,
    )


def error_response(
    message: str = "Error",
    error: Any | None = None,
    status_code: int = 500,
):
    """에러 응답 헬퍼"""
    return api_response(
        data=None,
        message=message,
        status=False,
        status_code=status_code,
        error=error,
    )
