import logging
import os

logger = logging.getLogger("backport")
logger.setLevel(os.getenv("LOG_LEVEL", "INFO").upper())
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch = logging.StreamHandler()
ch.setFormatter(formatter)
logger.addHandler(ch)
