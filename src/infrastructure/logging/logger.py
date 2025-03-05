import logging

from src.core.domain.interfaces import ILogger


class UvicornLogger(ILogger):
    def __init__(self):
        self.logger = logging.getLogger("uvicorn")
        self.logger.setLevel(logging.DEBUG)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)
