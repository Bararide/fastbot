from datetime import datetime
from typing import Any
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram import types
from aiogram.enums import ParseMode

from src.FastBotLib.logger.logger import Logger
from src.FastBotLib.engine.templates.template_engine import TemplateEngine
from models.user import User
from services.auth_service import AuthService


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


async def callback_handler(callback: types.CallbackQuery) -> Any:
    await callback.answer(f"Вы нажали на кнопку: {callback.data}")
    return await callback.message.answer(f"Выбрано: {callback.data}")


async def callback_get_profile_handler(
    callback: types.CallbackQuery,
    template_engine: TemplateEngine,
    auth: AuthService,
    user: User,
) -> Any:
    try:
        Logger.info("callback_get_profile_handler")

        if not user:
            Logger.error(f"User not found for ID: {callback.from_user.id}")
            await callback.answer(
                await template_engine.render_template(
                    "commands/no_registration.j2", user=user
                )
            )
            return

        Logger.info(f"{user.id}")
        stats = await auth.get_user_stats(user.id)

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

        await callback.message.answer(**response)
    except Exception as e:
        Logger.error(f"Template error in callback_get_profile_handler: {e}")
        await callback.answer("Произошла ошибка при формировании профиля.")
