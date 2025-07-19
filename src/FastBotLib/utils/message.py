from typing import Any
from aiogram import types


class Message:
    async def answer(self, **kwargs) -> Any:
        return await self.send_answer(self, **kwargs)

    async def send_answer(self, message: types.Message, **response) -> Any:
        return await message.answer(**response)
