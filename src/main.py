import logging

import uvicorn

from db import connect

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def start():
    try:
        uvicorn.run("src.router:app", host="0.0.0.0", port=8001, reload=True)
    except uvicorn.Error as error:
        logging.critical(f"An unhandled uvicorn error occurred: {error}")


print("connect", connect)

if __name__ == "__main__":
    start()
