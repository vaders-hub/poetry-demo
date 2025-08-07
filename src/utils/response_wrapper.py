from typing import TypeVar, Generic

T = TypeVar('T')

def api_response(data=Generic[T], message="Success", status=True, error=None):
    return {
        "status": status,
        "message": message,
        "data": data,
        "error": error,
    }
