from __future__ import annotations

from typing import TYPE_CHECKING, Any

from httpx import Response as ClientResponse
from starlette.responses import Response as ServerResponse

from .utils import ComparableHTTPXResponse, ComparableStarletteResponse

if TYPE_CHECKING:
    import pytest


def pytest_assertrepr_compare(
    op: str, left: Any, right: Any, config: pytest.Config
) -> list[str] | None:  # pragma: no cover
    def forward(op: str, left: Any, right: Any) -> list[str]:
        return [
            f"  {line}"
            for line in config.hook.pytest_assertrepr_compare(
                op=op, left=left, right=right, config=config
            )[0]
        ]

    if isinstance(left, ComparableStarletteResponse) and isinstance(
        right, ServerResponse
    ):
        msg = [
            "Comparing ComparableStarletteResponse with Starlette Response",
        ]
        if left.response.status_code != right.status_code:
            msg.append("Different status codes:")
            msg += forward(op, left.response.status_code, right.status_code)
        if left.response.raw_headers != right.raw_headers:
            msg.append("Different headers:")
            msg += forward(op, dict(left.response.headers), dict(right.headers))

        if left.response.body != right.body:
            msg.append("Different bodies:")
            # Optionally, you could add more detailed body comparison here.
            msg += forward(op, left.response.body, right.body)

        return msg

    if isinstance(left, ComparableHTTPXResponse) and isinstance(right, ClientResponse):
        msg = [
            "Comparing ComparableHTTPXResponse with HTTPX Response",
        ]
        if left.response.status_code != right.status_code:
            msg.append("Different status codes:")
            msg += forward(op, left.response.status_code, right.status_code)
        if left.response.headers != right.headers:
            msg.append("Different headers:")
            msg += forward(op, dict(left.response.headers), dict(right.headers))

        if left.response.content != right.content:
            msg.append("Different content:")
            # Optionally, you could add more detailed body comparison here.
            msg += forward(op, left.response.content, right.content)

        return msg
    return None
