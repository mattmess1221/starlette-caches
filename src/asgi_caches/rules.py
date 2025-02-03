from __future__ import annotations

import re
import typing
from dataclasses import dataclass

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from starlette.requests import Request
    from starlette.responses import Response


@dataclass
class Rule:
    """A rule for configuring caching behavior.

    A rule is matched if the request path matches the `match` attribute and the response
    status code matches the `status` attribute.

    If the rule matches, the response will be cached for the duration specified by the
    `ttl` attribute. A value of 0 will disable caching for the response.

    All arguments are optional.
    """

    match: str | re.Pattern | Iterable[str | re.Pattern] = "*"
    """The request path to match.

    If a regular expression is provided, it will be matched against the request path.

    If a sequence is provided, the request path will be matched against each item in the
    sequence.

    If the request path matches any item in the sequence, the rule will match.
    """

    status: int | Iterable[int] | None = None
    """An integer or sequence of integers that match the response status code.

    If the response status code matches any item in the sequence, the rule will match.
    """

    ttl: float | None = None
    """Time-to-live for the cached response in seconds.

    If set, the response will be cached for the specified duration. If not set, the
    default TTL will be used. A value of 0 will disable caching for the response.
    """


def request_matches_rule(
    rule: Rule,
    *,
    request: Request,
) -> bool:
    match = (
        [rule.match] if isinstance(rule.match, (str, re.Pattern)) else list(rule.match)
    )
    for item in match:
        if isinstance(item, re.Pattern):
            if item.match(request.url.path):
                return True
        elif item == "*" or item == request.url.path:
            return True
    return False


def response_matches_rule(rule: Rule, *, request: Request, response: Response) -> bool:
    if not request_matches_rule(rule, request=request):
        return False

    if rule.status is not None:
        statuses = [rule.status] if isinstance(rule.status, int) else rule.status
        if response.status_code not in statuses:
            return False
    return True


def get_rule_matching_request(
    rules: Sequence[Rule], *, request: Request
) -> Rule | None:
    return next(
        (rule for rule in rules if request_matches_rule(rule, request=request)), None
    )


def get_rule_matching_response(
    rules: Sequence[Rule],
    *,
    request: Request,
    response: Response,
) -> Rule | None:
    return next(
        (
            rule
            for rule in rules
            if response_matches_rule(rule, request=request, response=response)
        ),
        None,
    )
