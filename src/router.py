from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from db import sessionmanager
from dependencies.auth import verify_token
from routers import customers, users
from utils import exception
from utils.exception import global_exception_handler, custom_http_exception_handler  # ✅ import



@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Function that handles startup and shutdown events.
    To understand more, read https://fastapi.tiangolo.com/advanced/events/
    """
    yield
    if sessionmanager._engine is not None:
        # Close the DB connection
        await sessionmanager.close()


app = FastAPI(lifespan=lifespan, root_path="/api/v1", dependencies=[Depends(verify_token)])

origins = ["http://localhost", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(customers.router)
app.include_router(users.router)

app.add_exception_handler(HTTPException, custom_http_exception_handler)
app.add_exception_handler(exception.GlobalException, global_exception_handler)


@app.get("/", tags=["root"])
async def read_root() -> dict:
    return {"message": "Welcome to your todo list."}
