from typing import Union
from aiogram.types import Message, CallbackQuery
from aiogram.types.base import TelegramObject

from models.user import User
from services import auth_service


async def resolve_user(
    event: Union[Message, CallbackQuery], auth_service: auth_service.AuthService
) -> User:
    """Резолвер для получения пользователя"""
    if isinstance(event, CallbackQuery):
        message = event.message
    else:
        message = event

    return await auth_service.get_user(message.from_user.id)
