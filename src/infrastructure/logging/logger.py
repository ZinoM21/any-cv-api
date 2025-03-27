import logging

from src.core.domain.interfaces import ILogger


class UvicornLogger(ILogger):
    def __init__(self):
        self.logger = logging.getLogger("uvicorn")
        self.logger.setLevel(logging.DEBUG)

    def info(self, message: object, *args: object):
        self.logger.info(message, *args)

    def error(self, message: object, *args: object):
        self.logger.error(message, *args)

    def warn(self, message: object, *args: object) -> None:
        self.logger.warning(message, *args)

    def debug(self, message: object, *args: object):
        self.logger.debug(message, *args)
