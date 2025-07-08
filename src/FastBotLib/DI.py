from typing import (
    Any,
    Callable,
    Dict,
    Type,
    Awaitable,
)

from aiogram.types.base import TelegramObject


class DependencyContainer:
    """Контейнер для управления зависимостями"""

    def __init__(self):
        self._dependencies: Dict[str, Any] = {}
        self._resolvers: Dict[Type, Callable[[Any], Awaitable[Any]]] = {}

    def register(self, key: str, dependency: Any) -> None:
        self._dependencies[key] = dependency

    def register_resolver(
        self, type_: Type, resolver: Callable[[Any], Awaitable[Any]]
    ) -> None:
        self._resolvers[type_] = resolver

    async def resolve(self, event: TelegramObject, additional_deps: dict) -> dict:
        resolved = {}
        resolved.update(self._dependencies)
        resolved.update(additional_deps)

        for dep_type, resolver in self._resolvers.items():
            if dep_type not in resolved:
                resolved[dep_type] = await resolver(event)

        return resolved
