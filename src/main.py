import uvicorn
from loguru import logger

# from configs.log_config import setup_logging

# setup_logging()


def start():
    try:
        logger.info("🚀 FastAPI Application Started")

        uvicorn.run(
            "src.router:app",
            host="0.0.0.0",
            port=8001,
            log_config="src/configs/logging.yaml",
            reload=True,
        )
    except Exception as e:
        # Log the error and its traceback
        logger.error("An unexpected Uvicorn/ASGI server error occurred.", exc_info=True)
        logger.error(e)
        # You can inspect the type of 'e' here if needed: type(e).__name__
