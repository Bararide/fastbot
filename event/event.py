import asyncio
from typing import Callable, List, Dict, Any, Optional, Union, Set
from dataclasses import dataclass
from enum import Enum
from weakref import WeakSet, WeakMethod
from fastbot.core import Result, result_try, Err, Ok
from fastbot.logger import Logger


class EventPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class EventHandler:
    name: str
    callback: Callable
    priority: EventPriority = EventPriority.NORMAL
    is_async: bool = False
    one_shot: bool = False


class Event:
    def __init__(self, name: Optional[str] = None):
        self.name = name or f"Event_{id(self)}"
        self._handlers: Dict[str, EventHandler] = {}
        self._handler_priorities: Dict[EventPriority, Set[str]] = {
            priority: set() for priority in EventPriority
        }
        self._weak_handlers: WeakSet = WeakSet()

    @result_try
    async def add(
        self,
        handler: Union[Callable, List[Union[str, Callable]]],
        name: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        one_shot: bool = False,
    ) -> Result[bool, Exception]:
        """
        Add event handler with various options
        """
        if callable(handler):
            handler_name = name or handler.__name__
            callback = handler
        elif isinstance(handler, list) and len(handler) >= 2:
            handler_name = str(handler[0])
            callback = handler[1]
            if not callable(callback):
                return Err(ValueError("Second element must be callable"))
        else:
            return Err(ValueError("Handler must be callable or list [name, callable]"))

        if handler_name in self._handlers:
            return Err(ValueError(f"Handler '{handler_name}' already exists"))

        is_async = asyncio.iscoroutinefunction(callback)
        event_handler = EventHandler(
            name=handler_name,
            callback=callback,
            priority=priority,
            is_async=is_async,
            one_shot=one_shot,
        )

        self._handlers[handler_name] = event_handler
        self._handler_priorities[priority].add(handler_name)

        try:
            if hasattr(callback, "__self__") and callback.__self__ is not None:
                self._weak_handlers.add(WeakMethod(callback))
        except TypeError:
            pass

        return Ok(True)

    @result_try
    async def remove(
        self, handler_identifier: Union[str, Callable]
    ) -> Result[bool, Exception]:
        """
        Remove handler by name or callback function
        """
        handler_name = None

        if isinstance(handler_identifier, str):
            handler_name = handler_identifier
        elif callable(handler_identifier):
            for name, handler in self._handlers.items():
                if handler.callback == handler_identifier:
                    handler_name = name
                    break

        if not handler_name or handler_name not in self._handlers:
            return Err(ValueError(f"Handler '{handler_identifier}' not found"))

        handler = self._handlers[handler_name]
        self._handler_priorities[handler.priority].discard(handler_name)
        del self._handlers[handler_name]

        return Ok(True)

    async def trigger(self, *args, **kwargs) -> Result[List[Any], Exception]:
        results = []
        handlers_to_remove = []

        try:
            for priority in sorted(EventPriority, reverse=True):
                handler_names = list(self._handler_priorities[priority])

                for handler_name in handler_names:
                    if handler_name not in self._handlers:
                        continue

                    handler = self._handlers[handler_name]

                    try:
                        if handler.is_async:
                            result = await handler.callback(*args, **kwargs)
                        else:
                            result = handler.callback(*args, **kwargs)

                        results.append(result)

                        if handler.one_shot:
                            handlers_to_remove.append(handler_name)

                    except Exception as e:
                        Logger.error(
                            f"Error in event handler '{handler_name}': {str(e)}"
                        )
                        results.append(Err(e))

            for handler_name in handlers_to_remove:
                await self.remove(handler_name)

            return Ok(results)

        except Exception as e:
            return Err(e)

    async def trigger_parallel(self, *args, **kwargs) -> Result[List[Any], Exception]:
        """
        Trigger event with parallel execution of async handlers
        """
        async_handlers = []
        sync_handlers = []
        handlers_to_remove = []

        try:
            for priority in sorted(EventPriority, reverse=True):
                for handler_name in self._handler_priorities[priority]:
                    if handler_name not in self._handlers:
                        continue

                    handler = self._handlers[handler_name]

                    if handler.one_shot:
                        handlers_to_remove.append(handler_name)

                    if handler.is_async:
                        async_handlers.append(handler)
                    else:
                        sync_handlers.append(handler)

            sync_results = []
            for handler in sync_handlers:
                try:
                    result = handler.callback(*args, **kwargs)
                    sync_results.append(result)
                except Exception as e:
                    Logger.error(
                        f"Error in sync event handler '{handler.name}': {str(e)}"
                    )
                    sync_results.append(Err(e))

            async_tasks = []
            for handler in async_handlers:
                task = asyncio.create_task(
                    self._execute_handler(handler, *args, **kwargs)
                )
                async_tasks.append((handler.name, task))

            async_results = []
            for handler_name, task in async_tasks:
                try:
                    result = await task
                    async_results.append(result)
                except Exception as e:
                    Logger.error(
                        f"Error in async event handler '{handler_name}': {str(e)}"
                    )
                    async_results.append(Err(e))

            for handler_name in handlers_to_remove:
                await self.remove(handler_name)

            return Ok(sync_results + async_results)

        except Exception as e:
            return Err(e)

    async def _execute_handler(self, handler: EventHandler, *args, **kwargs) -> Any:
        """Execute single handler with error handling"""
        try:
            return await handler.callback(*args, **kwargs)
        except Exception as e:
            Logger.error(f"Error in event handler '{handler.name}': {str(e)}")
            raise

    def has_handler(self, handler_identifier: Union[str, Callable]) -> bool:
        """Check if handler exists"""
        if isinstance(handler_identifier, str):
            return handler_identifier in self._handlers
        elif callable(handler_identifier):
            return any(
                handler.callback == handler_identifier
                for handler in self._handlers.values()
            )
        return False

    def get_handler_count(self) -> int:
        """Get total number of handlers"""
        return len(self._handlers)

    def clear(self) -> None:
        """Remove all handlers"""
        self._handlers.clear()
        for priority_set in self._handler_priorities.values():
            priority_set.clear()
        self._weak_handlers.clear()

    def list_handlers(self) -> List[Dict[str, Any]]:
        """Get list of all handlers with their properties"""
        return [
            {
                "name": handler.name,
                "priority": handler.priority.name,
                "is_async": handler.is_async,
                "one_shot": handler.one_shot,
            }
            for handler in self._handlers.values()
        ]


class EventManager:
    """
    Manager for multiple events with namespacing support
    """

    def __init__(self):
        self._events: Dict[str, Event] = {}
        self._namespaces: Dict[str, Dict[str, Event]] = {}

    @result_try
    async def create_event(
        self, event_name: str, namespace: str = "global"
    ) -> Result[Event, Exception]:
        """Create a new event in specified namespace"""
        if namespace not in self._namespaces:
            self._namespaces[namespace] = {}

        if event_name in self._namespaces[namespace]:
            return Err(
                ValueError(
                    f"Event '{event_name}' already exists in namespace '{namespace}'"
                )
            )

        event = Event(event_name)
        self._events[event_name] = event
        self._namespaces[namespace][event_name] = event

        return Ok(event)

    def get_event(self, event_name: str, namespace: str = "global") -> Optional[Event]:
        """Get event by name and namespace"""
        if namespace in self._namespaces:
            return self._namespaces[namespace].get(event_name)
        return None

    @result_try
    async def remove_event(
        self, event_name: str, namespace: str = "global"
    ) -> Result[bool, Exception]:
        """Remove event from namespace"""
        if (
            namespace not in self._namespaces
            or event_name not in self._namespaces[namespace]
        ):
            return Err(
                ValueError(f"Event '{event_name}' not found in namespace '{namespace}'")
            )

        event = self._namespaces[namespace][event_name]
        event.clear()

        del self._namespaces[namespace][event_name]
        if event_name in self._events:
            del self._events[event_name]

        return Ok(True)

    async def trigger_event(
        self, event_name: str, *args, namespace: str = "global", **kwargs
    ) -> Result[List[Any], Exception]:
        """Trigger event by name"""
        event = self.get_event(event_name, namespace)
        if not event:
            return Err(
                ValueError(f"Event '{event_name}' not found in namespace '{namespace}'")
            )

        return await event.trigger(*args, **kwargs)

    def get_namespace_events(self, namespace: str = "global") -> List[str]:
        """Get all event names in namespace"""
        if namespace in self._namespaces:
            return list(self._namespaces[namespace].keys())
        return []


def event_handler(
    name: Optional[str] = None,
    priority: EventPriority = EventPriority.NORMAL,
    one_shot: bool = False,
):
    """Decorator for event handlers"""

    def decorator(func):
        func._event_handler = {
            "name": name or func.__name__,
            "priority": priority,
            "one_shot": one_shot,
        }
        return func

    return decorator


class EventMixin:
    """Mixin class for adding event capabilities to other classes"""

    def __init__(self):
        self._events: Dict[str, Event] = {}
        self._event_manager = EventManager()

    def create_event(self, event_name: str) -> Event:
        """Create event for this instance"""
        event = Event(event_name)
        self._events[event_name] = event
        return event

    def on(
        self, event_name: str, handler: Callable, **kwargs
    ) -> Result[bool, Exception]:
        """Subscribe to event"""
        if event_name not in self._events:
            return Err(ValueError(f"Event '{event_name}' not found"))

        return asyncio.run(self._events[event_name].add(handler, **kwargs))

    async def emit(
        self, event_name: str, *args, **kwargs
    ) -> Result[List[Any], Exception]:
        """Emit event"""
        if event_name not in self._events:
            return Err(ValueError(f"Event '{event_name}' not found"))

        return await self._events[event_name].trigger(*args, **kwargs)
