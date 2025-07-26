from aiogram import types
from aiogram.filters import Filter

from models import User


class CallbackDataFilter(Filter):
    def __init__(self, prefix: str):
        self.prefix = prefix

    async def __call__(self, callback: types.CallbackQuery) -> bool:
        return callback.data.startswith(self.prefix)


async def handle_profile_actions(callback: types.CallbackQuery, user: User):
    action = callback.data.removeprefix("profile_")
    if action == "edit":
        await callback.answer("Редактирование профиля")
        await callback.message.answer("Раздел редактирования профиля...")
    elif action == "stats":
        await callback.answer("Статистика")
        await callback.message.answer("Ваша статистика...")
    else:
        await callback.answer("Неизвестное действие")


async def handle_help_button(callback: types.CallbackQuery):
    await callback.answer("Помощь")
    await callback.message.answer("Раздел помощи...")


async def handle_default_actions(callback: types.CallbackQuery):
    await callback.answer(f"Действие: {callback.data}")
    await callback.message.answer(f"Вы выбрали: {callback.data}")
