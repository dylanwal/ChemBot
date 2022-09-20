"""
Logger
"""

import logging


color_codes = {
    "reset": "\033[0m",  # add at the end to stop coloring
    "black": "\033[30m",
    "red": "\033[31m",
    "green": "\033[32m",
    "yellow": "\033[33m",
    "blue": "\033[34m",
    "magenta": "\033[35m",
    "cyan": "\033[36m",
    "white": "\033[37m",
}

BOLD_SEQ = "\033[1m"


class LogFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(fmt="%(levelno)d: %(msg)s", datefmt=None, style='%')

    def format(self, record):
        # Save the original format configured by the user when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = f"\t \t{color_codes['green']}DEBUG: %(msg)s{color_codes['reset']}"
        elif record.levelno == logging.INFO:
            self._style._fmt = f"\t{color_codes['white']}INFO: %(msg)s{color_codes['reset']}"
        elif record.levelno == logging.WARNING:
            self._style._fmt = f"{color_codes['yellow']}WARNING: %(msg)s {color_codes['reset']}"
        elif record.levelno == logging.ERROR:
            self._style._fmt = f"{color_codes['red']}ERROR: %(msg)s {color_codes['reset']}\n\n\n"
        elif record.levelno == logging.CRITICAL:
            self._style._fmt = f"{color_codes['red']}CRITICAL: %(msg)s {color_codes['reset']}\n\n\n"

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig

        return result


logger = logging.getLogger("chembot")

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(LogFormatter())
logger.addHandler(stream_handler)

logger.setLevel(logging.DEBUG)
