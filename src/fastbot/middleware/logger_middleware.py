from aiogram import types
from aiogram.types import TelegramObject
from typing import Callable, Dict, Any, Awaitable
from FastBot.logger import Logger


async def logger_middleware(
    handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: Dict[str, Any],
) -> Any:
    handler_name = getattr(handler, "__name__", str(handler))
    handler_module = getattr(handler, "__module__", "unknown")

    try:
        Logger.info(
            "Before handler",
            context={
                "handler": handler_name,
                "module": handler_module,
                "event_type": type(event).__name__,
            },
        )

        result = await handler(event, data)

        Logger.info(
            "After handler",
            context={
                "handler": handler_name,
                "result_type": type(result).__name__,
            },
        )

        return result
    except Exception as e:
        Logger.error(
            "Handler error",
            context={
                "handler": handler_name,
                "error": str(e),
                "event_type": type(event).__name__,
            },
        )
        raise
