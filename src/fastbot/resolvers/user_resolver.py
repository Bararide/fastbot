from typing import Union
from aiogram.types import Message, CallbackQuery

from models import User, UserStats
from services import AuthService

from FastBot.core import Result, Err


async def resolve_user(
    event: Union[Message, CallbackQuery], auth_service: AuthService
) -> Result[User, Exception]:
    try:
        return await auth_service.get_user(event.from_user.id)
    except Exception as e:
        return Err(e)


async def resolve_user_stats(
    event: Union[Message, CallbackQuery], auth_service: AuthService
) -> Result[UserStats, Exception]:
    try:
        return await auth_service.get_user_stats(event.from_user.id)
    except Exception as e:
        return Err(e)
