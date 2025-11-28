import logging
from app.config.settings import settings

_FMT = "%(asctime)s %(levelname)s %(name)s - %(message)s"

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(settings.log_level.upper())
        h = logging.StreamHandler()
        h.setFormatter(logging.Formatter(_FMT))
        logger.addHandler(h)
        logger.propagate = False
    return logger
