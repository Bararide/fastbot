import asyncio
from os import getenv
from typing import Any

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.storage.memory import MemoryStorage

from fastapi import WebSocket

from FastBot.engine import TemplateEngine
from FastBot.engine import ContextEngine

from FastBot import FastBotBuilder, MiniAppConfig
from FastBot.logger import Logger

import handlers
import resolvers
import services
import middleware
import models
import filters

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

    database_service = services.DBService(getenv("MONGO_URI"), getenv("DATABASE_NAME"))
    auth_service = services.AuthService(database_service)
    auth_middleware = middleware.AuthMiddleware(auth_service)
    ten_service = TemplateEngine(template_dirs=["templates", "src/fastbot/templates"])
    cen_service = ContextEngine()

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
        .add_middleware(middleware.error_handling_middleware)
        .add_middleware(middleware.logger_middleware)
        .add_router(main_router)
        .add_router(admin_router)
        .add_mini_app(mini_app_config)
    )

    bot_builder.add_dependency("database_service", database_service)
    bot_builder.add_dependency("auth_service", auth_service)
    bot_builder.add_dependency("auth_middleware", auth_middleware)
    bot_builder.add_dependency("template_engine", ten_service)
    bot_builder.add_dependency("cen", cen_service)
    bot_builder.add_dependency_resolver(models.User, resolvers.resolve_user)
    bot_builder.add_dependency_resolver(models.UserStats, resolvers.resolve_user_stats)

    bot_builder.add_contexts(
        [
            resolvers.profile_context,
            resolvers.error_message_context,
            resolvers.profile_buttons_context,
            resolvers.registration_context,
            resolvers.admin_list_context,
            resolvers.access_denied_context,
            resolvers.registration_error_context,
            resolvers.profile_error_context,
            resolvers.app_context,
            resolvers.test_photo_context,
            resolvers.test_photo_error_context,
            resolvers.number_status_context,
            resolvers.number_status_error_context,
        ]
    )

    command_handlers = [
        ("start", handlers.cmd_start, "Начать взаимодействие с ботом"),
        ("buttons", filters.show_buttons, "Показать тестовые inline-кнопки"),
        ("status", handlers.cmd_status, "Проверить статус бота"),
        ("register", handlers.cmd_register, "Зарегистрироваться в системе"),
        ("profile", handlers.cmd_profile, "Просмотреть свой профиль"),
        ("admins", handlers.cmd_admin_list, "Список администраторов"),
        ("app", handlers.cmd_app, "Приложение"),
    ]

    for cmd, handler, desc in command_handlers:
        bot_builder.add_command_handler(cmd, handler, desc)

    bot_builder.add_reply_menu(
        filters.show_feedback_menu, filters.handle_feedback_menu_reply_buttons
    )
    bot_builder.add_reply_menu(
        filters.show_confirmation_menu, filters.handle_conf_menu_reply_buttons
    )

    bot_builder.add_handler(handlers.test_photo, F.photo)
    bot_builder.add_handler(
        handlers.process_numbers, F.text.regexp(r"^-?\d+\.?\d*\s-?\d+\.?\d*$")
    )
    bot_builder.add_handler(handlers.new_member_handler, F.chat_join)
    bot_builder.add_handler(
        handlers.handle_invalid_input,
        F.text
        & ~F.text.regexp(r"^-?\d+\.?\d*\s-?\d+\.?\d*$")
        & ~F.text.startswith("/"),
    )
    bot_builder.add_callback_query_handler(
        filters.callback_get_profile_handler, F.data.startswith("profile_")
    )
    bot_builder.add_callback_query_handler(
        filters.callback_handler, F.data.startswith("btn_")
    )
    bot_builder.add_callback_query_handler(
        filters.check_number_status, F.data.startswith("status_")
    )
    bot_builder.add_callback_query_handler(filters.handle_help_button, F.data == "help")
    bot_builder.add_callback_query_handler(filters.handle_default_actions)

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
