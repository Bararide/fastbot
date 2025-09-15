from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
)

from aiogram import Router
from aiogram.filters import BaseFilter
from aiogram.types import Message
from aiogram.types.base import TelegramObject


class HandlerConfig:
    def __init__(
        self,
        handler: Callable,
        filters: Optional[List[BaseFilter]] = None,
        event_type: Type[TelegramObject] = Message,
        router: Optional[Router] = None,
        dependencies: Optional[Dict[str, Any]] = None,
    ):
        self.handler = handler
        self.filters = filters or []
        self.event_type = event_type
        self.router = router
        self.dependencies = dependencies or {}
