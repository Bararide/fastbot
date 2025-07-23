import asyncio
from os import getenv
from typing import Any

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.storage.memory import MemoryStorage
from functools import partial

from fastapi import WebSocket

from src.fastbot.resolvers.context_resolvers import (
    access_denied_context,
    admin_list_context,
    app_context,
    error_message_context,
    profile_buttons_context,
    profile_context,
    profile_error_context,
    registration_context,
    registration_error_context,
)
from src.FastBotLib.engine.context.context_engine import ContextEngine
from src.fastbot.services.db_service import DBService
from src.FastBotLib.engine.templates.template_engine import TemplateEngine
from src.FastBotLib.FastBot import FastBotBuilder, MiniAppConfig
from handlers import (
    cmd_start,
    cmd_status,
    cmd_register,
    cmd_profile,
    cmd_admin_list,
    process_numbers,
    handle_invalid_input,
    cmd_app,
)
from src.FastBotLib.logger.logger import Logger
from middleware.logger_middleware import logger_middleware
from middleware.error_middleware import error_handling_middleware
from middleware.auth_middleware import AuthMiddleware
from services.auth_service import AuthService
from models.user import User
from models.user_stats import UserStats
from resolvers.user_resolver import resolve_user, resolve_user_stats
from filters.confirm_menu import handle_conf_menu_reply_buttons, show_confirmation_menu
from filters.feedback_menu import handle_feedback_menu_reply_buttons, show_feedback_menu
from states.states import MenuState
from filters.inline_menu_test import (
    callback_get_profile_handler,
    show_buttons,
    callback_handler,
)
from filters.callback_data_filter import (
    CallbackDataFilter,
    handle_default_actions,
    handle_help_button,
    handle_profile_actions,
)

load_dotenv()


async def on_startup(bot: Any) -> None:
    """Функция, выполняемая при запуске бота"""
    Logger.info("Bot started successfully!")


async def on_shutdown(bot: Any) -> None:
    """Функция, выполняемая при остановке бота"""
    Logger.info("Bot is shutting down...")


async def handle_webhook(data: dict):
    """Обработчик вебхуков от Mini App"""
    Logger.info(f"Received webhook data: {data}")
    return {"status": "ok"}


async def websocket_handler(websocket: WebSocket):
    """Обработчик WebSocket соединений"""
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        Logger.info(f"WS received: {data}")
        await websocket.send_text(f"Echo: {data}")


async def main():
    main_router = Router(name="main_router")
    admin_router = Router(name="admin_router")

    mongo_uri = getenv("MONGO_URI")
    database_service = DBService(mongo_uri, getenv("DATABASE_NAME"))
    auth_service = AuthService(database_service)
    auth_middleware = AuthMiddleware(auth_service)
    template_engine_service = TemplateEngine(
        template_dirs=["templates", "src/fastbot/templates"]
    )
    context_engine_service = ContextEngine()

    admin_router.message.middleware(auth_middleware)
    admin_router.callback_query.middleware(auth_middleware)
    main_router.callback_query.middleware(auth_middleware)

    storage = MemoryStorage()

    mini_app_config = MiniAppConfig(
        title="My Awesome App",
        description="Telegram Mini App with FastAPI",
        static_dir="static",
        webhook_path="/webhook",
        webhook_handler=handle_webhook,
        ws_handler=websocket_handler,
    )

    bot_builder = (
        FastBotBuilder()
        .set_bot(Bot(token=getenv("BOT_TOKEN")))
        .set_dispatcher(Dispatcher(storage=storage))
        .add_middleware(error_handling_middleware)
        .add_middleware(logger_middleware)
        .add_router(main_router)
        .add_router(admin_router)
        .add_mini_app(mini_app_config)
    )

    bot_builder.add_dependency("database_service", database_service)
    bot_builder.add_dependency("auth_service", auth_service)
    bot_builder.add_dependency("auth_middleware", auth_middleware)
    bot_builder.add_dependency("template_engine", template_engine_service)
    bot_builder.add_dependency("context_engine", context_engine_service)
    bot_builder.add_dependency_resolver(
        User, partial(resolve_user, auth_service=auth_service)
    )
    bot_builder.add_dependency_resolver(
        UserStats, partial(resolve_user_stats, auth_service=auth_service)
    )

    bot_builder.add_contexts(
        [
            profile_context,
            error_message_context,
            profile_buttons_context,
            registration_context,
            admin_list_context,
            access_denied_context,
            registration_error_context,
            profile_error_context,
            app_context,
        ]
    )

    command_handlers = [
        ("start", cmd_start, "Начать взаимодействие с ботом"),
        ("buttons", show_buttons, "Показать тестовые inline-кнопки"),
        ("status", cmd_status, "Проверить статус бота"),
        ("register", cmd_register, "Зарегистрироваться в системе"),
        ("profile", cmd_profile, "Просмотреть свой профиль"),
        ("admins", cmd_admin_list, "Список администраторов"),
        ("app", cmd_app, "Приложение"),
    ]

    for cmd, handler, desc in command_handlers:
        bot_builder.add_command_handler(cmd, handler, desc)

    state_handlers = [
        ("feedback", show_feedback_menu, "Меню фидбека", MenuState.WAITING_FEEDBACK),
        (
            "confirm",
            show_confirmation_menu,
            "Меню подтверждения",
            MenuState.WAITING_CONFIRMATION,
        ),
    ]

    for cmd, handler, desc, state in state_handlers:
        bot_builder.add_async_state_command_handler(cmd, handler, desc, state)

    bot_builder.add_reply_menu_handler(handle_feedback_menu_reply_buttons)
    bot_builder.add_reply_menu_handler(handle_conf_menu_reply_buttons)

    bot_builder.add_handler(
        process_numbers, F.text.regexp(r"^-?\d+\.?\d*\s-?\d+\.?\d*$")
    )
    bot_builder.add_handler(handle_invalid_input)
    bot_builder.add_callback_query_handler(
        callback_get_profile_handler, F.data.startswith("profile_")
    )
    bot_builder.add_callback_query_handler(callback_handler, F.data.startswith("btn_"))
    bot_builder.add_callback_query_handler(handle_help_button, F.data == "help")
    bot_builder.add_callback_query_handler(handle_default_actions)

    bot_builder.add_startup_callback(on_startup)
    bot_builder.add_shutdown_callback(on_shutdown)

    bot = bot_builder.build()

    @bot.app.get("/mini-app")
    async def health_check():
        return {"status": "ok"}

    use_webhook = getenv("USE_WEBHOOK", "").lower() == "true"

    if use_webhook:
        webhook_url = f"https://{getenv('WEBAPP_DOMAIN')}/webhook"
        await bot.start_with_webhook(webhook_url)
    else:
        tasks = [bot.start_polling()]
        if bot.app:
            port = int(getenv("PORT", "8000"))
            tasks.append(bot.run_web_server(port))
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    asyncio.run(main())
