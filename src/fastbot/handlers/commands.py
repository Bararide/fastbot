import asyncio
from datetime import datetime
import os
from typing import Any, Dict
from aiogram import types
from aiogram.enums import ParseMode

from FastBot.decorators import (
    with_auto_reply,
    with_context,
    with_parse_mode,
    with_template_engine,
)
from FastBot.builders import InlineMenuBuilder
from FastBot.engine import TemplateEngine, ContextEngine
from FastBot.logger import Logger
from models import User, UserStats
from services import AuthService

from celery.result import AsyncResult


@with_template_engine
@with_auto_reply("commands/start.j2", buttons_template="buttons/start_menu_buttons.j2")
async def cmd_start(
    message: types.Message,
    user: User,
    ten: TemplateEngine,
    cen: ContextEngine,
):
    pass


async def cmd_app(message: types.Message, cen: ContextEngine):
    context = await cen.get("app")
    await message.answer(
        context.get("text", "Открыть Mini App"),
        reply_markup=InlineMenuBuilder()
        .add_row(
            {
                "text": context.get("button_text", "Open"),
                "web_app": f"https://{os.getenv('WEBAPP_DOMAIN')}/mini-app",
            }
        )
        .build(),
    )


@with_template_engine
@with_auto_reply("commands/status.j2")
@with_parse_mode(ParseMode.HTML)
async def cmd_status(
    message: types.Message,
    ten: TemplateEngine,
    cen: ContextEngine,
):
    try:
        parts = message.text.split()
        task_id = parts[1] if len(parts) > 1 else None
        task = AsyncResult(task_id) if task_id else None

        return {
            "context": await cen.get(
                "status", task_id=task_id, task=task, exists=task is not None
            )
        }
    except Exception as e:
        return {"context": await cen.get("error_message", error_message=str(e))}


@with_template_engine
@with_auto_reply("commands/register.j2")
@with_parse_mode(ParseMode.HTML)
async def cmd_register(
    message: types.Message,
    ten: TemplateEngine,
    auth_service: AuthService,
    cen: ContextEngine,
):
    user = message.from_user
    result = await auth_service.register_user(
        {
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "registered_at": datetime.now().isoformat(),
        }
    )

    if result.is_ok():
        return {
            "context": await cen.get("registration", user=result.unwrap(), success=True)
        }
    else:
        return {"context": await cen.get("registration_error", error=str(result.err()))}


@with_template_engine
@with_auto_reply(
    template_name="commands/choose_lang.j2",
    buttons_template="buttons/choose_lang_buttons.j2",
)
async def cmd_choose_lang(
    message: types.Message,
    ten: TemplateEngine,
    user: User,
    cen: ContextEngine,
):
    try:
        return {
            "context": await cen.get("choose_lang"),
            "buttons_context": await cen.get("choose_lang_buttons", user_id=user.id),
            "row_width": 2,
        }
    except Exception as e:
        Logger.error(f"Error in cmd_choose_lang: {e}")
        return {
            "context": await cen.get("choose_lang_error", error="Error in choose lang")
        }


@with_template_engine
@with_auto_reply(
    template_name="commands/profile.j2",
    buttons_template="buttons/profile_menu_buttons.j2",
)
async def cmd_profile(
    message: types.Message,
    user: User,
    stats: UserStats,
    cen: ContextEngine,
    ten: TemplateEngine,
    auth_service: AuthService,
) -> Dict[str, Any]:
    try:
        return {
            "context": await cen.get("profile", user=user, stats=stats),
            "buttons_context": await cen.get("profile_buttons", user=user),
            "row_width": 2,
        }
    except Exception as e:
        Logger.error(f"Error in cmd_profile: {e}")
        return {
            "context": await cen.get(
                "profile_error", user=user, error_message="Ошибка загрузки профиля"
            )
        }


@with_template_engine
@with_auto_reply(
    template_name="commands/admin_list.j2",
    buttons_template="buttons/admin_list_buttons.j2",
)
@with_context(current_date=datetime.now().strftime("%d.%m.%Y %H:%M"))
@with_parse_mode(ParseMode.HTML)
async def cmd_admin_list(
    message: types.Message,
    ten: TemplateEngine,
    user: User,
    auth_service: AuthService,
    cen: ContextEngine,
):
    try:
        if not user.is_admin:
            return {
                "context": await cen.get(
                    "access_denied", message="⛔ Доступ только для администраторов"
                )
            }

        return {
            "context": await cen.get(
                "admin_list",
                admins=await auth_service.users.find({"is_admin": True}).to_list(None)
                or [],
            ),
            "buttons_context": await cen.get("admin_buttons", user_id=user.id),
        }
    except Exception as e:
        Logger.error(f"Error in cmd_admin_list: {str(e)}")
        return {
            "context": await cen.get(
                "admin_list_error",
                error_message="⚠️ Ошибка при загрузке списка администраторов",
            )
        }
