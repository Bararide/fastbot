from typing import Union
from aiogram.types import Message, CallbackQuery

from models import User, UserStats
from services import AuthService

from FastBot.core import Result


async def resolve_user(
    event: Union[Message, CallbackQuery], auth_service: AuthService
) -> Result[User, Exception]:
    return await auth_service.get_user(event.from_user.id)


async def resolve_user_stats(
    event: Union[Message, CallbackQuery], auth_service: AuthService
) -> Result[UserStats, Exception]:
    return await auth_service.get_user_stats(event.from_user.id)
