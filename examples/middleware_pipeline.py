"""Example: Using middleware pipeline."""

import asyncio
import time
from dataclasses import dataclass

from cqrs_framing import (
    AsyncHandlerContext,
    Broker,
    CommandResponse,
    HandlerRegistry,
    Message,
    Pipeline,
    Response,
)


# Command
@dataclass
class ProcessPayment(Message):
    """Command to process a payment."""

    payment_id: str
    amount: float


# Handler
class ProcessPaymentHandler:
    """Handler for processing payments."""

    async def execute(
        self, command: ProcessPayment, cancellation_token
    ) -> CommandResponse[str]:
        """Execute the payment processing."""
        # Simulate payment processing
        await asyncio.sleep(0.1)
        print(f"   💳 Processing payment ${command.amount:.2f}")
        return Response.ok(f"Payment {command.payment_id} processed")


# Middleware
async def logging_middleware(ctx: AsyncHandlerContext, next):
    """Log request and response."""
    print(f"→ Request: {ctx.request.__class__.__name__}")
    result = await next(ctx)
    print(f"← Response: success={ctx.success}")
    return result


async def timing_middleware(ctx: AsyncHandlerContext, next):
    """Measure execution time."""
    start = time.time()
    result = await next(ctx)
    elapsed = (time.time() - start) * 1000
    print(f"⏱  Execution time: {elapsed:.2f}ms")
    return result


async def validation_middleware(ctx: AsyncHandlerContext, next):
    """Validate request before processing."""
    print("✓ Validating request...")

    # Example validation
    if isinstance(ctx.request, ProcessPayment):
        if ctx.request.amount <= 0:
            print("✗ Validation failed: Invalid amount")
            ctx.should_continue = False
            ctx.response = Response.failed("Amount must be greater than 0")
            return ctx.response

    result = await next(ctx)
    return result


async def exception_handling_middleware(ctx: AsyncHandlerContext, next):
    """Handle exceptions gracefully."""
    try:
        result = await next(ctx)
        return result
    except Exception as e:
        print(f"✗ Exception caught: {e}")
        ctx.success = False
        ctx.exception = e
        ctx.response = Response.failed(str(e), exception=e)
        return ctx.response


async def transaction_middleware(ctx: AsyncHandlerContext, next):
    """Simulate transaction management."""
    print("  ▶ BEGIN TRANSACTION")
    try:
        result = await next(ctx)
        if ctx.success:
            print("  ✓ COMMIT TRANSACTION")
        else:
            print("  ✗ ROLLBACK TRANSACTION")
        return result
    except Exception:
        print("  ✗ ROLLBACK TRANSACTION")
        raise


async def main():
    """Run the example."""
    print("=== Pipeline Middleware Example ===\n")

    # Setup
    registry = HandlerRegistry()
    registry.register(ProcessPayment, ProcessPaymentHandler)

    # Create pipeline
    pipeline = Pipeline[AsyncHandlerContext]()
    pipeline.use(logging_middleware)
    pipeline.use(timing_middleware)
    pipeline.use(exception_handling_middleware)
    pipeline.use(validation_middleware)
    pipeline.use(transaction_middleware)

    broker = Broker(registry, async_pipeline=pipeline)

    # Example 1: Valid payment
    print("Example 1: Valid payment\n")
    result1 = await broker.handle_async(
        ProcessPayment(payment_id="PAY-001", amount=99.99)
    )
    print(f"\nResult: {result1.data}\n")
    print("-" * 50 + "\n")

    # Example 2: Invalid payment (validation fails)
    print("Example 2: Invalid payment (validation fails)\n")
    result2 = await broker.handle_async(
        ProcessPayment(payment_id="PAY-002", amount=-50.00)
    )
    print(f"\nResult: {result2.message}\n")
    print("-" * 50 + "\n")

    # Example 3: Custom middleware order
    print("Example 3: Different middleware order\n")
    minimal_pipeline = Pipeline[AsyncHandlerContext]()
    minimal_pipeline.use(logging_middleware)
    minimal_pipeline.use(timing_middleware)

    minimal_broker = Broker(registry, async_pipeline=minimal_pipeline)
    result3 = await minimal_broker.handle_async(
        ProcessPayment(payment_id="PAY-003", amount=49.99)
    )
    print(f"\nResult: {result3.data}\n")


if __name__ == "__main__":
    asyncio.run(main())
