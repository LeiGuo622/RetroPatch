import logging
import os

from rich.logging import RichHandler

logger = logging.getLogger("backport")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger.addHandler(RichHandler())
