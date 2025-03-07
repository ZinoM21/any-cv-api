class UncaughtException(Exception):
    """Exception for uncaught exceptions"""

    def __init__(self, origin: str, detail: str | None = None) -> None:
        super().__init__(detail)
        if detail is None:
            self.origin = "unknown origin"
            self.detail = origin
        else:
            self.origin = origin
            self.detail = detail
