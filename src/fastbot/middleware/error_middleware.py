from aiogram import types
from aiogram.types import TelegramObject, Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from src.FastBotLib.logger.logger import Logger
from functools import partial
import traceback


async def error_handling_middleware(
    handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: Dict[str, Any],
) -> Any:
    """Middleware для обработки ошибок в handlers.
    Логирует ошибки и отправляет пользователю сообщение об ошибке.
    """
    try:
        return await handler(event, data)
    except Exception as e:
        handler_name = (
            handler.__name__
            if not isinstance(handler, partial)
            else handler.func.__name__
        )

        Logger.error(
            f"Error in handler {handler_name}: {str(e)}",
            exc_info=e,
            context={
                "event_type": type(event).__name__,
                "handler": handler_name,
                "module": handler.__module__,
                "traceback": traceback.format_exc(),
            },
        )

        chat_id = None
        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and event.message:
            chat_id = event.message.chat.id

        if chat_id:
            bot = data.get("bot")
            if bot and isinstance(bot, types.Bot):
                try:
                    await bot.send_message(
                        chat_id=chat_id,
                        text="⚠️ Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже.",
                    )
                except Exception as send_error:
                    Logger.error(
                        f"Failed to send error message: {send_error}",
                        exc_info=send_error,
                    )

        raise
