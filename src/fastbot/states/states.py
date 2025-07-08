from aiogram.fsm.state import State, StatesGroup


class MenuState(StatesGroup):
    WAITING_FEEDBACK = State()
    WAITING_CONFIRMATION = State()
