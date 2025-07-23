from datetime import datetime
from typing import Any
from aiogram import types
from aiogram.enums import ParseMode

from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.FastBotLib.engine.context.context_engine import ContextEngine
from src.FastBotLib.engine.templates.template_engine import TemplateEngine
from src.FastBotLib.logger.logger import Logger
from models.user import User
from models.user_stats import UserStats
from services.auth_service import AuthService
from src.FastBotLib.decorators.with_template_engine import (
    with_template_engine,
    with_parse_mode,
    with_context,
    with_auto_reply,
)


async def show_buttons(message: types.Message):
    """Показать тестовые кнопки"""
    builder = InlineKeyboardBuilder()

    builder.add(types.InlineKeyboardButton(text="Кнопка 1", callback_data="btn_1"))
    builder.add(types.InlineKeyboardButton(text="Кнопка 2", callback_data="btn_2"))
    builder.add(types.InlineKeyboardButton(text="Кнопка 3", callback_data="btn_3"))

    builder.add(
        types.InlineKeyboardButton(text="Открыть Google", url="https://google.com")
    )

    builder.adjust(2, 1)

    await message.answer("Выберите действие:", reply_markup=builder.as_markup())


async def callback_handler(
    callback: types.CallbackQuery, user: User, auth: AuthService
) -> Any:
    await callback.answer(f"Пользователь: {user.id}")
    return await callback.message.answer(f"Выбрано: {callback.data}")


@with_template_engine
@with_parse_mode(parse_mode=ParseMode.HTML)
@with_auto_reply("commands/profile.j2", "buttons/profile_menu_buttons.j2")
async def callback_get_profile_handler(
    callback: types.CallbackQuery,
    template_engine: TemplateEngine,
    context_engine: ContextEngine,
    user: User,
    stats: UserStats,
) -> dict:
    try:
        if not user:
            Logger.error(f"User not found for ID: {callback.from_user.id}")
            return {
                "template_name": "commands/no_registration.j2",
                "message": callback.message,
                "user": user,
            }

        return {
            "context": await context_engine.get("profile", user=user, stats=stats),
            "buttons_context": await context_engine.get("profile_buttons", user=user),
            "row_width": 2,
        }
    except Exception as e:
        Logger.error(f"Error in cmd_profile: {e}")
        return {
            "context": {
                "user": user,
                "stats": {"messages": 0, "completed_tasks": 0, "active_tasks": 0},
                "is_admin": user.is_admin,
                "error_message": "Произошла ошибка при загрузке статистики",
            }
        }
