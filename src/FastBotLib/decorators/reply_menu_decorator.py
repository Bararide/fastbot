from functools import wraps
from typing import List, Callable, Any, Optional, Union
from aiogram import types
from aiogram.fsm.state import State
from aiogram.fsm.context import FSMContext


def menu_handler(
    buttons: List[str],
    state: Optional[Union[State, List[State]]] = None,
    clear_state: bool = True,
) -> Callable:
    """
    Декоратор для автоматической привязки обработчика к кнопкам меню с определенным FSMContext.

    :param buttons: Список кнопок, на которые реагирует обработчик
    :param state: Состояние FSM или список состояний, в которых должен работать обработчик
    :param clear_state: Очищать ли состояние FSM после обработки (по умолчанию True)
    :return: Декорированная функция
    """

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

        wrapper._menu_handler_info = {
            "buttons": buttons,
            "state": state,
            "clear_state": clear_state,
        }

        return wrapper

    return decorator
