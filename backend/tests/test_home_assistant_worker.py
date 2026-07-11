import pytest

from app.workers.home_assistant import retry_delay_seconds, run_with_retry


class FakeLogger:
    def __init__(self) -> None:
        self.messages = []

    def exception(self, message: str, *args) -> None:
        if args:
          message = message % args
        self.messages.append(message)


def test_retry_delay_seconds_uses_backoff_and_caps() -> None:
    assert retry_delay_seconds(1) == 5
    assert retry_delay_seconds(2) == 10
    assert retry_delay_seconds(3) == 20
    assert retry_delay_seconds(10) == 300


@pytest.mark.anyio
async def test_run_with_retry_retries_after_error_then_succeeds() -> None:
    attempts = 0
    delays = []
    logger = FakeLogger()

    async def operation() -> None:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise RuntimeError("temporary websocket failure")

    async def fake_sleep(delay: int) -> None:
        delays.append(delay)

    await run_with_retry(
        operation,
        sleep=fake_sleep,
        logger=logger,
        stop_after_success=True,
    )

    assert attempts == 2
    assert delays == [5]
    assert logger.messages == ["Home Assistant ingestion cycle failed; retrying in 5 seconds"]
