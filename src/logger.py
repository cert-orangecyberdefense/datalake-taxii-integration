import logging

logger = logging.getLogger("OCD_TAXII")

LOG_FORMAT = '%(asctime)s %(name)s:%(levelname)-4s %(message)s'


def configure_logging(loglevel: int):
    handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT)
    handler.suffix = "%Y-%m-%d"
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(loglevel)
