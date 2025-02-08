from starlette.requests import Request
from starlette.responses import Response


class StarletteCachesException(Exception):
    pass


class RequestNotCachable(StarletteCachesException):
    """Raised when a request cannot be cached."""

    def __init__(self, request: Request) -> None:
        super().__init__()
        self.request = request


class ResponseNotCachable(StarletteCachesException):
    """Raised when a response cannot be cached."""

    def __init__(self, response: Response) -> None:
        super().__init__()
        self.response = response


class DuplicateCaching(StarletteCachesException):
    """Raised when multiple cache middleware were detected."""


class MissingCaching(StarletteCachesException):
    """Raised when no cache middleware was detected."""
