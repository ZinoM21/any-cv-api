from abc import ABC, abstractmethod


class ILogger(ABC):
    @abstractmethod
    def info(self, message: object, *args: object) -> None:
        pass

    @abstractmethod
    def error(self, message: object, *args: object) -> None:
        pass

    @abstractmethod
    def warn(self, message: object, *args: object) -> None:
        pass

    @abstractmethod
    def debug(self, message: object, *args: object) -> None:
        pass
