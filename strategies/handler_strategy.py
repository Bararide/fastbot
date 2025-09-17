from typing import (
    Callable,
    List,
    Type,
)

from aiogram import Router
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, InlineQuery
from aiogram.types.base import TelegramObject

from fastbot.logger import Logger


class HandlerStrategy:
    @staticmethod
    def register(
        router: Router,
        handler: Callable,
        filters: List[BaseFilter],
        event_type: Type[TelegramObject],
    ) -> None:
        if event_type is Message:
            router.message.register(handler, *filters)
        elif event_type is CallbackQuery:
            router.callback_query.register(handler, *filters)
        elif event_type is InlineQuery:
            router.inline_query.register(handler, *filters)
        else:
            Logger.warning(f"Unsupported event type: {event_type}")
