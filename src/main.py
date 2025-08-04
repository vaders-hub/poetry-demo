import logging
import sys
from contextlib import asynccontextmanager
from src.config import setting
from src.db import sessionmanager
from fastapi import FastAPI
import uvicorn

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG if setting.log_level == "DEBUG" else logging.INFO)

def start():
    try:
        uvicorn.run("src.router:app", host="0.0.0.0", port=8001, reload=True)
    except uvicorn.Error as error:
        logging.critical(f"An unhandled uvicorn error occurred: {error}")


if __name__ == "__main__":
    start()
