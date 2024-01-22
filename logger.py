import logging
from termcolor import colored
from colorama import init

init()  # enable color support on Windows


class ColorFormatter(logging.Formatter):
    def format(self, record):
        if record.levelname == "INFO":
            levelname = colored(record.levelname, "cyan")  # 'INFO' part in blue
            message = colored(
                record.getMessage(), "blue"
            )  # actual info message in cyan for contrast
            return f"=====\n{levelname} {message}\n\n"
        else:
            return super().format(record)


def get_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler()
    handler.setFormatter(ColorFormatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)
    return logger
