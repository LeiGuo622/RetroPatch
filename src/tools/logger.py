import logging

from rich.logging import RichHandler

logger = logging.getLogger("backport")
logger.addHandler(RichHandler())


def add_file_handler(logger: logging.Logger, filename: str):
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
