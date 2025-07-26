from aiogram import types
from aiogram.dispatcher.middlewares.base import BaseMiddleware
from typing import Callable, Dict, Any
from services import AuthService


class AuthMiddleware(BaseMiddleware):
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service
        super().__init__()

    async def __call__(
        self,
        handler: Callable,
        event: types.TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, (types.Message, types.CallbackQuery)):
            return await handler(event, data)

        command = None
        if isinstance(event, types.Message) and event.text:
            command = event.text.split()[0].lower()

        if command == "/register":
            return await handler(event, data)

        user = event.from_user
        if not user:
            return await handler(event, data)

        user = await self.auth_service.get_user(event.from_user.id)
        if not user:
            if isinstance(event, types.Message):
                await event.answer(
                    "🔐 Вы не зарегистрированы. Используйте /register для регистрации"
                )
            return

        data["user"] = user
        data["auth_service"] = self.auth_service
        return await handler(event, data)
