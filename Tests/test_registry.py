"""Tests for handler registry."""

import pytest

from cqrs_framing import (
    DuplicateHandlerError,
    HandlerNotRegisteredError,
    HandlerRegistry,
    Message,
)


class _Request(Message):
    pass


class SyncTestHandler:
    def execute(self, message: _Request) -> str:
        return "sync result"


class AsyncTestHandler:
    async def execute(self, message: _Request, cancellation_token=None) -> str:
        return "async result"


class NoExecuteHandler:
    pass


def test_register_sync_handler():
    """Test registering a synchronous handler."""
    registry = HandlerRegistry()
    registry.register(_Request, SyncTestHandler)

    resolved = registry.resolve_sync(_Request)
    assert isinstance(resolved, SyncTestHandler)
    assert resolved.execute(_Request()) == "sync result"


def test_register_async_handler():
    """Test registering an asynchronous handler."""
    registry = HandlerRegistry()
    registry.register(_Request, AsyncTestHandler)

    resolved = registry.resolve_async(_Request)
    assert isinstance(resolved, AsyncTestHandler)


def test_register_handler_instance():
    """Test registering a pre-instantiated handler."""
    registry = HandlerRegistry()
    handler = SyncTestHandler()
    registry.register_instance(_Request, handler)

    resolved = registry.resolve_sync(_Request)
    assert resolved is handler


def test_register_handler_without_execute():
    """Test that registering a handler without execute method raises TypeError."""
    registry = HandlerRegistry()

    with pytest.raises(TypeError, match="execute"):
        registry.register(_Request, NoExecuteHandler)


def test_duplicate_sync_handler_raises():
    """Test that registering duplicate sync handler raises error."""
    registry = HandlerRegistry()

    registry.register(_Request, SyncTestHandler)

    with pytest.raises(DuplicateHandlerError):
        registry.register(_Request, SyncTestHandler)


def test_duplicate_async_handler_raises():
    """Test that registering duplicate async handler raises error."""
    registry = HandlerRegistry()

    registry.register(_Request, AsyncTestHandler)

    with pytest.raises(DuplicateHandlerError):
        registry.register(_Request, AsyncTestHandler)


def test_resolve_unregistered_sync_handler_raises():
    """Test that resolving unregistered sync handler raises error."""
    registry = HandlerRegistry()

    with pytest.raises(HandlerNotRegisteredError):
        registry.resolve_sync(_Request)


def test_resolve_unregistered_async_handler_raises():
    """Test that resolving unregistered async handler raises error."""
    registry = HandlerRegistry()

    with pytest.raises(HandlerNotRegisteredError):
        registry.resolve_async(_Request)


def test_handler_with_dependencies():
    """Test handler with constructor dependencies."""

    class Service:
        def get_value(self) -> str:
            return "service value"

    class HandlerWithDeps:
        def __init__(self, service: Service):
            self.service = service

        def execute(self, message: _Request) -> str:
            return self.service.get_value()

    registry = HandlerRegistry()
    # Register the service first
    registry.container.register(Service)
    # Register the handler (DI will inject Service)
    registry.register(_Request, HandlerWithDeps)

    handler = registry.resolve_sync(_Request)
    assert isinstance(handler, HandlerWithDeps)
    assert handler.execute(_Request()) == "service value"
