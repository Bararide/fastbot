import pytest
from fastbot.event import Event, EventPriority
from fastbot.logger import Logger


def test_event_handler():
    Logger.info("test_event_handler")
    return "handler_executed"


@pytest.mark.asyncio
async def test_event():
    event = Event("test")

    await event.add(
        handler=test_event_handler,
        name="test",
        priority=EventPriority.HIGH,
    )

    result = await event.trigger()
    Logger.info(f"Result: {result}")
    Logger.info(f"Result type: {type(result)}")


@pytest.mark.asyncio
async def test_event_debug():
    """Тест для отладки - что именно возвращает trigger()"""
    event = Event("debug")

    await event.add(
        handler=lambda: "simple_handler",
        name="simple",
        priority=EventPriority.NORMAL,
    )

    result = await event.trigger()
    print(f"DEBUG - Result: {result}")
    print(f"DEBUG - Result is_ok: {result.is_ok()}")

    if result.is_ok():
        value = result.unwrap()
        print(f"DEBUG - Unwrapped value: {value}")
        print(f"DEBUG - Value type: {type(value)}")
