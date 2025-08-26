from typing import (
    Any,
    Callable,
    Dict,
    Type,
    Awaitable,
    get_type_hints,
)

from aiogram.types import TelegramObject

from FastBot.logger import Logger
from FastBot.core import Result


class DependencyContainer:
    def __init__(self):
        self._dependencies: Dict[str, Any] = {}
        self._resolvers: Dict[Type, Callable[..., Awaitable[Any]]] = {}
        self._resolver_dependencies: Dict[Type, Dict[str, Any]] = {}

    def register(self, key: str, dependency: Any) -> None:
        self._dependencies[key] = dependency

    def register_resolver(
        self, type_: Type, resolver: Callable[..., Awaitable[Any]]
    ) -> None:
        self._resolvers[type_] = resolver

        type_hints = get_type_hints(resolver)
        resolver_deps = {}

        for param_name, param_type in type_hints.items():
            if param_name == "return":
                continue

            if param_name in self._dependencies:
                resolver_deps[param_name] = self._dependencies[param_name]
            else:
                matching_deps = [
                    dep
                    for dep in self._dependencies.values()
                    if isinstance(dep, param_type)
                ]
                if len(matching_deps) == 1:
                    resolver_deps[param_name] = matching_deps[0]

        self._resolver_dependencies[type_] = resolver_deps

    async def resolve(self, event: TelegramObject, additional_deps: dict) -> dict:
        resolved = {}
        resolved.update(self._dependencies)
        resolved.update(additional_deps)

        for dep_type, resolver in self._resolvers.items():
            if dep_type not in resolved:
                resolver_deps = self._resolver_dependencies.get(dep_type, {})
                result = await resolver(event, **resolver_deps)

                if isinstance(result, Result):
                    if result.is_ok():
                        resolved[dep_type] = result.unwrap()
                    else:
                        Logger.error(f"Failed to resolve {dep_type}: {result.unwrap()}")
                else:
                    resolved[dep_type] = result

        return resolved
