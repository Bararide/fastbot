from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Awaitable,
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
        dependency_resolvers: Dict[Type, Callable[[Any], Awaitable[Any]]] = {},
    ):
        self.handler = handler
        self.filters = filters or []
        self.event_type = event_type
        self.router = router
        self.dependencies = dependencies or {}
        self.dependency_resolvers = dependency_resolvers or {}
