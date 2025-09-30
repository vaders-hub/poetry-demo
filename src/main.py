import logging
import sys
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.config import setting
from src.db import sessionmanager

logging.basicConfig(
    stream=sys.stdout,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.DEBUG if setting.log_level == "DEBUG" else logging.INFO,
    # handlers=[logging.StreamHandler()]
)


def start():
    try:
        uvicorn.run("src.router:app", host="0.0.0.0", port=8001, reload=True)
    except uvicorn.Error as error:
        logging.critical(f"An unhandled uvicorn error occurred: {error}")


if __name__ == "__main__":
    start()
