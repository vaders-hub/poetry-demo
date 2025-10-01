from typing import Any, Optional, TypeVar

T = TypeVar("T")


def api_response(
    data: Optional[T] = None,
    message: str = "Success",
    status: bool = True,
    error: Optional[Any] = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "message": message,
        "data": data,
        "error": error,
    }
