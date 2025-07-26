from typing import Union, Optional
from aiogram.types import Message, CallbackQuery

from FastBot.logger import Logger
from models import User, UserStats
from services import AuthService


async def resolve_user(
    event: Union[Message, CallbackQuery], auth_service: AuthService
) -> Optional[User]:
    return await auth_service.get_user(event.from_user.id)


async def resolve_user_stats(
    event: Union[Message, CallbackQuery], auth_service: AuthService
) -> Optional[UserStats]:
    try:
        return await auth_service.get_user_stats(event.from_user.id)
    except Exception as e:
        Logger.error(f"Failed to get user stats: {e}")
        return UserStats(id=event.from_user.id)
