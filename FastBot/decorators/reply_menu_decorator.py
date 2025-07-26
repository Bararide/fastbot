from functools import wraps
from typing import List, Callable, Any, Optional, Union
from aiogram import types
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext


def menu(
    name: str,
    desc: str,
    state: Optional[Union[State, List[State]]] = None,
    clear_state: bool = False,
    command: Optional[str] = None,
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: types.Message, state: FSMContext, *args, **kwargs):
            result = await func(message, state, *args, **kwargs)
            if clear_state:
                await state.clear()
            return result

        wrapper._menu_meta = {
            "name": name,
            "description": desc,
            "state": state,
            "clear_state": clear_state,
            "command": command or name.lower(),
            "is_menu": True,
        }

        return wrapper

    return decorator


def menu_handler(
    buttons: List[str],
    state: Optional[Union[State, List[State]]] = None,
    clear_state: bool = True,
) -> Callable:
    def decorator(handler_func: Callable) -> Callable:
        @wraps(handler_func)
        async def wrapper(
            message: types.Message, state: FSMContext, *args: Any, **kwargs: Any
        ) -> Any:
            if message.text not in buttons:
                return

            result = await handler_func(message, state, *args, **kwargs)

            if clear_state:
                await state.clear()

            return result

        wrapper._menu_handler_meta = {
            "buttons": buttons,
            "state": state,
            "clear_state": clear_state,
        }

        return wrapper

    return decorator
