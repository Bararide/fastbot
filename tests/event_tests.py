import pytest
from fastbot.event import Event, EventPriority
from fastbot.logger import Logger


def test_event_handler():
    Logger.info("test_event")


@pytest.mark.asyncio
async def test_event():
    event = Event("test")

    await event.add(
        handler=test_event_handler,
        name="test",
        priority=EventPriority.HIGH,
    )

    result = await event.trigger()
    Logger.info(result)
