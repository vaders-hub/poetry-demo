from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from router import app


class GlobalException(Exception):
    pass


@app.exception_handler(GlobalException)
async def global_exception_handler(request: Request, exc: GlobalException):
    return JSONResponse(
        status_code=500,
        content={"message": f"Global handler: {str(exc)}"},
    )
