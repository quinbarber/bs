import logging
import sys


def setup_logging():
    logger = logging.getLogger("blackswan")
    logger.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(
        logging.Formatter("%(asctime)s - [%(levelname)s] - %(name)s - %(message)s")
    )

    logger.addHandler(stream_handler)

    return logger


bs_logger = setup_logging()
