import logging

import oracledb
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


def main():
    try:
        with connect() as connection:
            logging.info(f"Database version: {connection.version}")
    except oracledb.Error as error:
        logging.critical(f"An unhandled database error occurred: {error}")
    except Exception as e:
        logging.critical(f"An unexpected error occurred: {e}")


main()

if __name__ == "__main__":
    start()
