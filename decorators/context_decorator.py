from functools import wraps
from typing import Callable, Optional

import inspect

from FastBot.engine import ContextEngine


def register_context(
    name: Optional[str] = None, *, cen: Optional[ContextEngine] = None
):
    def decorator(func: Callable) -> Callable:
        context_name = name or func.__name__

        func._context_name = context_name

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return async_wrapper if inspect.iscoroutinefunction(func) else sync_wrapper

    return decorator
