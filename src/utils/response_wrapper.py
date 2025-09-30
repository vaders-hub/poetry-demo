from typing import Generic, TypeVar

T = TypeVar("T")


def api_response(data=Generic[T], message="Success", status=True, error=None):
    return {
        "status": status,
        "message": message,
        "data": data,
        "error": error,
    }
