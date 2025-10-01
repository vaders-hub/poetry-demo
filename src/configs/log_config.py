import logging
import sys

from loguru import logger


class InterceptHandler(logging.Handler):

    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except Exception:
            level = record.levelno
        logger.opt(depth=6, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    # 기존 logging → loguru 브리지
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # uvicorn 기본 로거들을 loguru로 redirect
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        logging.getLogger(name).handlers = [InterceptHandler()]

    # loguru 기본 설정
    logger.remove()
    logger.add(
        sys.stdout,
        colorize=True,
        serialize=True,  # JSON 포맷
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
        "<level>{message}</level>",
        level="INFO",
        enqueue=True,  # 멀티프로세스 안전
        backtrace=True,
        diagnose=True,  # 디버깅시 stacktrace 자세히
    )
