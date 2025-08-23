from datetime import datetime
from typing import Any
from aiogram import types
from aiogram.enums import ParseMode

from aiogram.utils.keyboard import InlineKeyboardBuilder

from FastBot.engine import ContextEngine
from FastBot.engine import TemplateEngine
from FastBot.logger import Logger
from models import User
from models import UserStats
from services import AuthService
from celery.result import AsyncResult
from FastBot.decorators import (
    with_template_engine,
    with_parse_mode,
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
@with_parse_mode(ParseMode.HTML)
@with_auto_reply("filters/number_status.j2")
async def check_number_status(
    callback: types.CallbackQuery, ten: TemplateEngine, cen: ContextEngine
) -> Any:
    task_id = callback.data.split("_")[1]
    task = AsyncResult(task_id)
    if task.ready():
        result = task.result
        return {
            "context": await cen.get("number_status", task_id=task_id, result=result)
        }
    else:
        return {
            "template_name": "filters/number_status_error.j2",
            "context": {"task_id": task_id},
        }


@with_template_engine
@with_parse_mode(parse_mode=ParseMode.HTML)
@with_auto_reply("commands/profile.j2", "buttons/profile_menu_buttons.j2")
async def callback_get_profile_handler(
    callback: types.CallbackQuery,
    ten: TemplateEngine,
    cen: ContextEngine,
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
            "context": await cen.get("profile", user=user, stats=stats),
            "buttons_context": await cen.get("profile_buttons", user=user),
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
