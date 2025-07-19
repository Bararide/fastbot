from datetime import datetime
import os
from aiogram import types
from aiogram.enums import ParseMode

from src.FastBotLib.decorators.with_template_engine import (
    with_auto_reply,
    with_template_engine,
)
from src.FastBotLib.builders.inline_menu_builder import InlineMenuBuilder
from src.FastBotLib.engine.templates.template_engine import TemplateEngine
from src.FastBotLib.logger.logger import Logger
from models.user import User
from models.user_stats import UserStats
from services.auth_service import AuthService

from celery.result import AsyncResult


@with_template_engine
@with_auto_reply("commands/start.j2", buttons_template="commands/start_menu_buttons.j2")
async def cmd_start(
    message: types.Message, user: User, template_engine: TemplateEngine
):
    pass


async def cmd_app(message: types.Message):
    await message.answer(
        "Открыть Mini App",
        reply_markup=InlineMenuBuilder()
        .add_row(
            {
                "text": "Open",
                "web_app": f"https://{os.getenv('WEBAPP_DOMAIN')}/mini-app",
            }
        )
        .build(),
    )


@with_template_engine
@with_auto_reply("commands/status.j2")
async def cmd_status(message: types.Message, template_engine: TemplateEngine):
    try:
        parts = message.text.split()
        task_id = parts[1] if len(parts) > 1 else None

        task = AsyncResult(task_id) if task_id else None
        task_status = task.status if task else "not_found"
        task_result = task.result if task else None

        return {
            "context": {
                "task_id": task_id,
                "task_status": task_status,
                "task_result": str(task_result) if task_result else None,
                "error": None,
                "exists": task is not None,
            },
            "parse_mode": ParseMode.HTML,
        }

    except Exception as e:
        return {
            "context": {
                "task_id": None,
                "task_status": "error",
                "task_result": None,
                "error": str(e),
                "exists": False,
            },
            "parse_mode": ParseMode.HTML,
        }


@with_template_engine
@with_auto_reply("commands/register.j2")
async def cmd_register(
    message: types.Message, template_engine: TemplateEngine, auth_service: AuthService
):
    user = message.from_user
    try:
        new_user = await auth_service.register_user(
            {
                "id": user.id,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "registered_at": datetime.now().isoformat(),
            }
        )

        return {
            "context": {
                "success": True,
                "error": None,
                "user": new_user,
            }
        }

    except ValueError as e:
        return {"context": {"success": False, "error": str(e), "user": None}}


@with_template_engine
@with_auto_reply(
    template_name="commands/profile.j2",
    buttons_template="commands/profile_menu_buttons.j2",
)
async def cmd_profile(
    message: types.Message,
    template_engine: TemplateEngine,
    user: User,
    stats: UserStats,
):
    try:
        return {
            "context": {
                "user": user,
                "stats": {
                    "messages": stats.get("messages", 0),
                    "completed_tasks": stats.get("completed_tasks", 0),
                    "active_tasks": stats.get("active_tasks", 0),
                },
                "is_admin": user.is_admin,
                "error_message": None,
            },
            "buttons_context": {"user_id": user.id, "is_admin": user.is_admin},
            "parse_mode": ParseMode.HTML,
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
            },
            "parse_mode": ParseMode.HTML,
        }


@with_template_engine
@with_auto_reply(
    template_name="commands/admin_list.j2",
    buttons_template="commands/admin_list_buttons.j2",
)
async def cmd_admin_list(
    message: types.Message,
    template_engine: TemplateEngine,
    user: User,
    auth_service: AuthService,
):
    try:
        if not user.is_admin:
            return {
                "context": {
                    "error_message": "⛔ Доступ только для администраторов",
                    "has_access": False,
                }
            }

        admins = await auth_service.users.find({"is_admin": True}).to_list(None)

        return {
            "context": {
                "admins": admins or [],
                "has_access": True,
                "current_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            },
            "buttons_context": {"user_id": user.id, "is_admin": True},
        }

    except Exception as e:
        Logger.error(f"Error in cmd_admin_list: {str(e)}")
        return {
            "context": {
                "error_message": "⚠️ Ошибка при загрузке списка администраторов",
                "has_access": user.is_admin,
            }
        }
