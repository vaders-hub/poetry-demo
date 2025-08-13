import logging
from logging.config import dictConfig
import sys
from src.config import setting
import uvicorn
from uvicorn.config import LOGGING_CONFIG

log_config = uvicorn.config.LOGGING_CONFIG
LOGGING_CONFIG["formatters"]["access"]["fmt"] = "%(asctime)s - Uvicorn.Access - %(levelname)s - %(message)s"
LOGGING_CONFIG["formatters"]["default"]["fmt"] = "%(asctime)s - Uvicorn.Default - %(levelname)s - %(message)s"


logging.basicConfig(
    stream=sys.stdout,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG if setting.log_level == "DEBUG" else logging.INFO,
    # handlers=[logging.StreamHandler()]
)

def start():
    try:
        uvicorn.run("src.router:app", host="0.0.0.0", port=8001, reload=True, log_config=LOGGING_CONFIG)
    except uvicorn.Error as error:
        logging.critical(f"An unhandled uvicorn error occurred: {error}")

if __name__ == "__main__":
    start()
