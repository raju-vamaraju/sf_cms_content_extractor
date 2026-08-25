import logging
import os

LOG_DIR = "logs"

os.makedirs(
    LOG_DIR,
    exist_ok=True
)

def get_logger(
    log_name
):

    logger = logging.getLogger(
        log_name
    )

    logger.setLevel(
        logging.INFO
    )

    if not logger.handlers:

        file_handler = logging.FileHandler(
            os.path.join(
                LOG_DIR,
                f"{log_name}.log"
            ),
            encoding="utf-8"
        )

        formatter = logging.Formatter(
            "%(asctime)s "
            "[%(levelname)s] "
            "%(message)s"
        )

        file_handler.setFormatter(
            formatter
        )

        logger.addHandler(
            file_handler
        )

    return logger