from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Filter
from aiogram.fsm.state import State


class StateFilter(Filter):
    def __init__(self, state: State):
        self.state = state

    async def __call__(self, message: Message, state: FSMContext) -> bool:
        current_state = await state.get_state()
        return current_state == self.state.state
