"""Handler protocols for sync and async execution."""

from __future__ import annotations

from typing import Protocol, TypeVar

from .cancellation import CancellationToken

TRequest = TypeVar("TRequest", contravariant=True)
TResponse = TypeVar("TResponse", covariant=True)


class Handler(Protocol[TRequest, TResponse]):
    """Protocol for synchronous message handlers."""

    def execute(self, message: TRequest) -> TResponse:
        """Execute the handler with the given message."""
        ...


class AsyncHandler(Protocol[TRequest, TResponse]):
    """Protocol for asynchronous message handlers."""

    async def execute(
        self, message: TRequest, cancellation_token: CancellationToken
    ) -> TResponse:
        """Execute the handler asynchronously with the given message and cancellation token."""
        ...
