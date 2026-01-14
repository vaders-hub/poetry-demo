from fastapi import APIRouter, FastAPI, HTTPException, Request
from utils.response_wrapper import api_response


class GlobalException(Exception):
    pass


async def global_exception_handler(request: Request, exc: GlobalException):
    return api_response(
        data=None,
        message=f"Global handler: {str(exc)}",
        status=False,
        status_code=500,
    )


async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return api_response(
        data=None,
        message=exc.detail,
        status=False,
        status_code=exc.status_code,
    )