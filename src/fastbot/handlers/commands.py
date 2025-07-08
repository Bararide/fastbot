from datetime import datetime
import os
from aiogram import types
from aiogram.enums import ParseMode

from src.FastBotLib.builders.inline_menu_builder import InlineMenuBuilder
from src.FastBotLib.engine.templates.template_engine import TemplateEngine
from src.FastBotLib.logger.logger import Logger
from models.user import User
from services.auth_service import AuthService

from celery.result import AsyncResult


async def cmd_start(
    message: types.Message, user: User, template_engine: TemplateEngine
):
    try:
        text = await template_engine.render_template("commands/start.j2", user=user)

        buttons = await template_engine.load_buttons_from_template(
            "commands/start_menu_buttons.j2"
        )

        await message.answer(
            text=text["text"],
            parse_mode=ParseMode.HTML,
            reply_markup=await template_engine.generate_inline_keyboard(
                buttons, row_width=2
            ),
        )
    except Exception as e:
        Logger.error(f"Error in cmd_start: {e}")
        await message.answer("Произошла ошибка при загрузке шаблона")


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


async def cmd_status(message: types.Message, template_engine: TemplateEngine):
    try:
        task_id = message.text.split()[1] if len(message.text.split()) > 1 else None
        task = AsyncResult(task_id) if task_id else None

        response = await template_engine.render_template(
            "commands/status.j2", task_id=task_id, task=task
        )
        await message.answer(**response)
    except Exception as e:
        response = await template_engine.render_template(
            "commands/status.j2", error=str(e)
        )
        await message.answer(**response)


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

        response = await template_engine.render_template(
            "commands/register.j2", success=True
        )
    except ValueError as e:
        response = await template_engine.render_template(
            "commands/register.j2", success=False, error=str(e)
        )

    await message.answer(**response)


async def cmd_profile(
    message: types.Message,
    template_engine: TemplateEngine,
    user: User,
    auth_service: AuthService,
):
    try:
        stats = await auth_service.get_user_stats(user.id)

        buttons = await template_engine.load_buttons_from_template(
            "commands/profile_menu_buttons.j2", user_id=user.id, is_admin=user.is_admin
        )

        response = await template_engine.render_response(
            "commands/profile.j2",
            context={"user": user, "stats": stats, "current_date": datetime.now()},
            parse_mode=ParseMode.HTML,
            reply_markup=await template_engine.generate_inline_keyboard(
                buttons=buttons, row_width=2
            ),
        )

        await message.answer(**response)
    except Exception as e:
        Logger.error(f"Template error in cmd_profile: {e}")
        await message.answer("Произошла ошибка при формировании профиля.")


async def cmd_admin_list(
    message: types.Message,
    template_engine: TemplateEngine,
    user: User,
    auth_service: AuthService,
):
    try:
        admins = (
            await auth_service.users.find({"is_admin": True}).to_list(None)
            if user and user.is_admin
            else None
        )

        response = await template_engine.render_template(
            "commands/admin_list.j2", user=user, admins=admins
        )

        await message.answer(**response)
    except Exception as e:
        Logger.error(f"Error in cmd_admin_list: {e}")
        await message.answer(
            await template_engine.render_template("commands/error.j2", user=user)
        )
