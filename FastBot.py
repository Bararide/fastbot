import asyncio
from functools import partial
import inspect
from contextlib import suppress
import json
import os
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Union,
    Tuple,
    Awaitable,
)

from pampy import match, _

from aiogram import F, Bot, Dispatcher, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.filters import BaseFilter
from aiogram.types import Message, CallbackQuery, InlineQuery
from aiogram.types.base import TelegramObject
from aiogram.fsm.state import State

from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from FastBot.engine import ContextEngine
from FastBot.logger import Logger

from FastBot.MiniApp import MiniAppConfig, MiniAppManager
from FastBot.filters import StateFilter
from FastBot.DI import DependencyContainer
from FastBot.configs import HandlerConfig
from FastBot.strategies import HandlerStrategy


class FastBotError(Exception):
    """Базовый класс исключений для FastBot"""

    pass


class ConfigurationError(FastBotError):
    """Ошибка в конфигурации бота"""

    pass


class DispatcherNotSetError(ConfigurationError):
    """Ошибка: диспетчер не установлен"""

    pass


class BotNotSetError(ConfigurationError):
    """Ошибка: бот не установлен"""

    pass


class FastBot:
    def __init__(self, bot: Bot, dp: Dispatcher):
        self.bot = bot
        self.dp = dp
        self._routers: List[Router] = []
        self._default_router = Router(name="default_router")
        self._shutdown_callbacks: List[Callable] = []
        self._startup_callbacks: List[Callable] = []
        self.dependency_container = DependencyContainer()
        self.mini_app: Optional[MiniAppManager] = None
        self.app: Optional[FastAPI] = None
        self.handler_strategy = HandlerStrategy()

        self.dp.include_router(self._default_router)

    def add_dependency(self, key: str, value: Any) -> "FastBot":
        self.dependency_container.register(key, value)
        return self

    def add_dependency_resolver(
        self, type_: Type, resolver: Callable[[Any], Awaitable[Any]]
    ) -> "FastBot":
        self.dependency_container.register_resolver(type_, resolver)
        return self

    def get_dependency(self, key: str) -> Any:
        return self.dependency_container._dependencies.get(key)

    def setup_mini_app(self, config: MiniAppConfig) -> "FastBot":
        """Setup Mini App after bot creation"""
        self.mini_app = MiniAppManager(self.bot, config)
        return self

    async def start_polling(self, **kwargs):
        Logger.info("Starting bot polling...")

        try:
            for callback in self._startup_callbacks:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self)
                else:
                    callback(self)

            await self.dp.start_polling(self.bot, **kwargs)
        except Exception as e:
            Logger.error(f"Error during bot polling: {e}", exc_info=e)
            raise
        finally:
            for callback in self._shutdown_callbacks:
                with suppress(Exception):
                    if asyncio.iscoroutinefunction(callback):
                        await callback(self)
                    else:
                        callback(self)

    async def run_web_server(self, port: int = 8000):
        if not self.app:
            Logger.error("Cannot start web server: FastAPI app not configured")
            return

        Logger.info(f"Starting FastAPI server on port {port}")
        config = uvicorn.Config(self.app, host="0.0.0.0", port=port, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def start_with_webhook(
        self, webhook_url: str, host: str = "0.0.0.0", port: int = 8000
    ) -> None:
        """Start bot with webhook and Mini App server"""
        if not self.mini_app:
            raise ConfigurationError("Mini App not configured")

        await self.bot.set_webhook(webhook_url)

        config = uvicorn.Config(
            self.mini_app.app, host=host, port=port, log_level="info"
        )
        server = uvicorn.Server(config)

        Logger.info(f"Starting bot with webhook at {webhook_url}")
        await server.serve()

    def add_startup_callback(self, callback: Callable) -> "FastBot":
        self._startup_callbacks.append(callback)
        return self

    def add_shutdown_callback(self, callback: Callable) -> "FastBot":
        self._shutdown_callbacks.append(callback)
        return self

    async def send_message(
        self, chat_id: Union[int, str], text: str, **kwargs
    ) -> Optional[Message]:
        try:
            return await self.bot.send_message(chat_id=chat_id, text=text, **kwargs)
        except TelegramAPIError as e:
            Logger.error(f"Failed to send message to {chat_id}: {e}")
            return None

    @property
    def default_router(self) -> Router:
        return self._default_router


class FastBotBuilder:
    def __init__(self):
        self._bot: Optional[Bot] = None
        self._dp: Optional[Dispatcher] = None
        self._routers: List[Router] = []
        self._message_middlewares: List[Callable] = []
        self._callback_query_middlewares: List[Callable] = []
        self._inline_query_middlewares: List[Callable] = []
        self._handlers: List[HandlerConfig] = []
        self._default_router = Router(name="default_router")
        self._error_handler: Optional[Callable] = None
        self._default_commands: List[Tuple[str, str]] = []
        self._startup_callbacks: List[Callable] = []
        self._shutdown_callbacks: List[Callable] = []
        self._is_fsm_storage_set = False
        self._default_rate_limit: Optional[float] = None
        self.dependency_container = DependencyContainer()
        self._mini_app_config: Optional[MiniAppConfig] = None
        self._mini_app_manager: Optional[MiniAppManager] = None
        self.handler_strategy = HandlerStrategy()

    def set_bot(self, bot: Bot) -> "FastBotBuilder":
        self._bot = bot
        Logger.info(f"Bot set with token: {bot.token[:5]}...{bot.token[-5:]}")
        return self

    def set_dispatcher(self, dp: Dispatcher) -> "FastBotBuilder":
        self._dp = dp
        Logger.info("Dispatcher set")
        return self

    def add_mini_app(self, config: MiniAppConfig) -> "FastBotBuilder":
        self._mini_app_config = config
        return self

    def add_middleware(
        self, middleware: Callable, event_type: Type[TelegramObject] = Message
    ) -> "FastBotBuilder":
        middleware_name = getattr(middleware, "__name__", str(middleware))

        if event_type == Message:
            self._message_middlewares.append(middleware)
            Logger.info(f"Message middleware added: {middleware_name}")
        elif event_type == CallbackQuery:
            self._callback_query_middlewares.append(middleware)
            Logger.info(f"Callback query middleware added: {middleware_name}")
        elif event_type == InlineQuery:
            self._inline_query_middlewares.append(middleware)
            Logger.info(f"Inline query middleware added: {middleware_name}")
        else:
            Logger.warning(f"Unsupported event type for middleware: {event_type}")

        return self

    def add_router(self, router: Router) -> "FastBotBuilder":
        self._routers.append(router)
        Logger.info(f"Router added: {router.name or str(router)}")
        return self

    def add_dependency(self, key: str, value: Any) -> "FastBotBuilder":
        self.dependency_container.register(key, value)
        Logger.info(f"Dependency added: {key}")
        return self

    def add_dependency_resolver(
        self, type_: Type, resolver: Callable[[Any], Awaitable[Any]]
    ) -> "FastBotBuilder":
        self.dependency_container.register_resolver(type_, resolver)
        return self

    def add_reply_menu_handler(
        self,
        handler: Callable,
        buttons: List[str] = None,
        state: Optional[Any] = None,
        router: Optional[Router] = None,
        dependencies: Optional[Dict[str, Any]] = None,
    ) -> "FastBotBuilder":
        menu_handler_info = getattr(handler, "_menu_handler_info", None)

        final_buttons = buttons
        final_state = state

        if menu_handler_info:
            final_buttons = menu_handler_info.get("buttons", buttons)
            final_state = menu_handler_info.get("state", state)

        if not final_buttons:
            raise ValueError(
                "Buttons list must be specified either through parameter or @menu_handler decorator"
            )

        filters = [F.text.in_(final_buttons)]

        if final_state is not None:
            if isinstance(final_state, list):
                state_filter = StateFilter(final_state[0])
                for s in final_state[1:]:
                    state_filter = state_filter | StateFilter(s)
                filters.append(state_filter)
            else:
                filters.append(StateFilter(final_state))

        return self.add_handler(
            handler, *filters, router=router, dependencies=dependencies
        )

    def add_reply_menu(
        self,
        menu_handler: Callable,
        *button_handlers: Callable,
        router: Optional[Router] = None,
        dependencies: Optional[Dict[str, Any]] = None,
    ) -> "FastBotBuilder":
        if not hasattr(menu_handler, "_menu_meta"):
            raise ValueError("Menu handler must be decorated with @menu decorator")

        menu_meta = menu_handler._menu_meta

        self.add_async_state_command_handler(
            command=menu_meta["command"],
            handler=menu_handler,
            description=menu_meta["description"],
            state=menu_meta["state"],
            router=router,
        )

        for button_handler in button_handlers:
            if not hasattr(button_handler, "_menu_handler_meta"):
                raise ValueError(
                    "Button handler must be decorated with @menu_handler decorator"
                )

            handler_meta = button_handler._menu_handler_meta

            if handler_meta["state"] != menu_meta["state"]:
                Logger.error(
                    f"Button handler state ({handler_meta['state']}) "
                    f"does not match menu state ({menu_meta['state']})"
                )

            self.add_handler(
                button_handler,
                F.text.in_(handler_meta["buttons"]),
                StateFilter(handler_meta["state"]),
                router=router,
                dependencies=dependencies,
            )

        return self

    def add_handler(
        self,
        handler: Callable,
        *filters: Union[BaseFilter, State],
        event_type: Type[TelegramObject] = Message,
        router: Optional[Router] = None,
        dependencies: Optional[Dict[str, Any]] = None,
    ) -> "FastBotBuilder":
        handler_name = self._get_handler_name(handler)

        base_filters = []
        state_filters = []

        for f in filters:
            if isinstance(f, State):
                state_filters.append(f)
            else:
                base_filters.append(f)

        if state_filters:
            state_filter = StateFilter(state_filters[0])
            for s in state_filters[1:]:
                state_filter = state_filter | StateFilter(s)
            base_filters.append(state_filter)

        handler_config = HandlerConfig(
            handler=handler,
            filters=base_filters,
            event_type=event_type,
            router=router,
            dependencies=dependencies or {},
        )

        self._handlers.append(handler_config)
        Logger.info(
            f"Handler added: {handler_name} with {len(base_filters)} filters for {event_type.__name__}"
        )
        return self

    def add_state_command_handler(
        self,
        command: Union[str, List[str]],
        handler: Callable,
        description: Optional[str] = None,
        state: Optional[Any] = None,
        router: Optional[Router] = None,
    ) -> "FastBotBuilder":
        async def wrapped_handler(message: types.Message, state: FSMContext, **kwargs):
            if state is not None:
                await state.set_state(state)
            return await handler(message, state, **kwargs)

        return self.add_command_handler(command, wrapped_handler, description, router)

    def add_async_state_command_handler(
        self,
        command: Union[str, List[str]],
        handler: Callable,
        description: Optional[str] = None,
        state: Optional[Any] = None,
        router: Optional[Router] = None,
    ) -> "FastBotBuilder":
        async def wrapped_handler(message: types.Message, state: FSMContext, **kwargs):
            if state is not None:
                await state.set_state(state)
            asyncio.create_task(handler(message, state, **kwargs))

        return self.add_command_handler(command, wrapped_handler, description, router)

    def add_command_handler(
        self,
        command: Union[str, List[str]],
        handler: Callable,
        description: Optional[str] = None,
        router: Optional[Router] = None,
    ) -> "FastBotBuilder":
        commands = [command] if isinstance(command, str) else command

        original_handler = handler.func if hasattr(handler, "func") else handler
        handler_name = getattr(original_handler, "__name__", str(original_handler))

        if description and isinstance(command, str):
            self._default_commands.append((command, description))
            Logger.info(f"Command '{command}' added with description: {description}")

        Logger.info(
            f"Registering command handler: {handler_name} for commands: {commands}"
        )
        return self.add_handler(handler, Command(commands=commands), router=router)

    def add_callback_query_handler(
        self, handler: Callable, *filters: BaseFilter, router: Optional[Router] = None
    ) -> "FastBotBuilder":
        return self.add_handler(
            handler, *filters, event_type=CallbackQuery, router=router
        )

    def add_inline_query_handler(
        self, handler: Callable, *filters: BaseFilter, router: Optional[Router] = None
    ) -> "FastBotBuilder":
        return self.add_handler(
            handler, *filters, event_type=InlineQuery, router=router
        )

    def set_error_handler(self, handler: Callable) -> "FastBotBuilder":
        self._error_handler = handler
        Logger.info(f"Error handler set: {handler.__name__}")
        return self

    def add_startup_callback(self, callback: Callable) -> "FastBotBuilder":
        self._startup_callbacks.append(callback)
        Logger.info(f"Startup callback added: {callback.__name__}")
        return self

    def add_shutdown_callback(self, callback: Callable) -> "FastBotBuilder":
        self._shutdown_callbacks.append(callback)
        Logger.info(f"Shutdown callback added: {callback.__name__}")
        return self

    def get_router(self, name: str) -> Router:
        for router in self._routers:
            if router.name == name:
                return router
        raise ValueError(f"Router with name '{name}' not found")

    def set_default_rate_limit(self, rate_limit: float) -> "FastBotBuilder":
        self._default_rate_limit = rate_limit
        Logger.info(f"Default rate limit set to {rate_limit} seconds")
        return self

    def add_context(self, context_func: Callable) -> "FastBotBuilder":
        cen = self._get_or_create_cen()

        context_name = (
            getattr(context_func, "_context_name", None) or context_func.__name__
        )

        cen.add(context_name, context_func)
        Logger.info(f"Context registered: {context_name}")

        return self

    def add_contexts(self, context_funcs: List[Callable]) -> "FastBotBuilder":
        for func in context_funcs:
            self.add_context(func)
        return self

    def _get_or_create_cen(self) -> ContextEngine:
        for dependency in self.dependency_container._dependencies.values():
            if isinstance(dependency, ContextEngine):
                return dependency

        cen = ContextEngine()
        self.add_dependency("cen", cen)
        return cen

    async def _setup_commands(self, bot: Bot):
        """Настроить команды бота в меню команд"""
        if not self._default_commands:
            return

        from aiogram.types import BotCommand

        commands = [
            BotCommand(command=cmd, description=desc)
            for cmd, desc in self._default_commands
        ]

        try:
            await bot.set_my_commands(commands)
            Logger.info(
                f"Bot commands set: {', '.join(cmd for cmd, _ in self._default_commands)}"
            )
        except Exception as e:
            Logger.error(f"Failed to set bot commands: {e}")

    def _get_handler_name(self, handler: Callable) -> str:
        try:
            if isinstance(handler, partial):
                func = handler.func
                while isinstance(func, partial):
                    func = func.func
                return (
                    f"partial_{func.__name__}"
                    if hasattr(func, "__name__")
                    else "partial"
                )

            if hasattr(handler, "__name__"):
                return handler.__name__

            if hasattr(handler, "func"):
                func = handler.func
                while hasattr(func, "func"):
                    func = func.func
                return func.__name__ if hasattr(func, "__name__") else "wrapped"

            return str(handler)
        except Exception:
            return "unknown_handler"

    async def _resolve_dependencies(
        self, event: TelegramObject, dependencies: dict
    ) -> dict:
        resolved = await self.dependency_container.resolve(event, dependencies)
        return resolved

    def _wrap_handler(self, handler: Callable, dependencies: dict) -> Callable:
        original_handler = handler.func if isinstance(handler, partial) else handler

        async def wrapped_handler(event: TelegramObject, **kwargs):
            try:
                sig = inspect.signature(original_handler)

                resolved_deps = await self._resolve_dependencies(event, dependencies)

                bound_args = {}

                match_result = match(
                    event,
                    Message,
                    lambda msg: {
                        "message": msg if "message" in sig.parameters else None,
                        "msg": msg if "msg" in sig.parameters else None,
                    },
                    CallbackQuery,
                    lambda cb: {
                        "callback": cb if "callback" in sig.parameters else None,
                        "callback_query": (
                            cb if "callback_query" in sig.parameters else None
                        ),
                        "query": cb if "query" in sig.parameters else None,
                    },
                    InlineQuery,
                    lambda iq: {
                        "inline_query": (
                            iq if "inline_query" in sig.parameters else None
                        ),
                        "query": iq if "query" in sig.parameters else None,
                    },
                    _,
                    lambda x: {},
                )

                for key, value in match_result.items():
                    if value is not None and key in sig.parameters:
                        bound_args[key] = value

                if "state" in sig.parameters and "state" in kwargs:
                    bound_args["state"] = kwargs["state"]

                for name, param in sig.parameters.items():
                    if name in bound_args:
                        continue

                    if param.annotation != param.empty:
                        for dep in resolved_deps.values():
                            if isinstance(dep, param.annotation):
                                bound_args[name] = dep
                                break

                    elif name in resolved_deps:
                        bound_args[name] = resolved_deps[name]
                    elif name in kwargs:
                        bound_args[name] = kwargs[name]

                if isinstance(handler, partial):
                    for k, v in handler.keywords.items():
                        if k not in bound_args and k in sig.parameters:
                            bound_args[k] = v

                if inspect.iscoroutinefunction(original_handler):
                    return await original_handler(**bound_args)
                else:
                    return original_handler(**bound_args)

            except Exception as e:
                Logger.error(
                    f"Error in wrapped handler {self._get_handler_name(handler)}: {e}"
                )
                raise

        wrapped_handler.__name__ = self._get_handler_name(handler)
        wrapped_handler._original_handler = original_handler

        return wrapped_handler

    def _setup_mini_app_handlers(self):
        if not self._mini_app_manager:
            return

        self.add_command_handler("app", self._handle_app_command, "Open Mini App")

        self.add_handler(self._handle_web_app_data, F.content_type == "web_app_data")

    async def _handle_app_command(self, message: types.Message):
        if not self._mini_app_manager:
            await message.answer("Mini App not configured")
            return

        button = self._mini_app_manager.get_webapp_button()
        await message.answer(
            "Open Mini App:",
            reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[[button]]),
        )

    async def _handle_web_app_data(self, message: types.Message):
        try:
            data = json.loads(message.web_app_data.data)
            Logger.info(f"Received data from Mini App: {data}")

            response = f"Received: {data.get('action', 'unknown')}"
            await message.answer(response)
        except Exception as e:
            Logger.error(f"Error processing Mini App data: {e}")
            await message.answer("Error processing data from Mini App")

    def build(self) -> "FastBot":
        if not self._bot:
            raise BotNotSetError("Bot is not set")

        if not self._dp:
            self._dp = Dispatcher()
            Logger.info("Created default Dispatcher")

        bot_instance = FastBot(self._bot, self._dp)

        if self._mini_app_config:
            Logger.info("Creating FastAPI app for MiniApp...")

            app = FastAPI()
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

            if self._mini_app_config.static_dir and os.path.exists(
                self._mini_app_config.static_dir
            ):
                Logger.info(
                    f"Mounting static directory: {self._mini_app_config.static_dir}"
                )
                app.mount(
                    "/static",
                    StaticFiles(directory=self._mini_app_config.static_dir),
                    "static",
                )

            if (
                self._mini_app_config.webhook_path
                and self._mini_app_config.webhook_handler
            ):

                @app.post(self._mini_app_config.webhook_path)
                async def webhook_handler(data: dict):
                    return await self._mini_app_config.webhook_handler(data)

            if self._mini_app_config.ws_handler:

                @app.websocket("/ws")
                async def websocket_endpoint(websocket: WebSocket):
                    await self._mini_app_config.ws_handler(websocket)

            bot_instance.app = app
            Logger.info("FastAPI app created and configured")

            self._setup_mini_app_handlers()

        for key in self.dependency_container._dependencies:
            bot_instance.add_dependency(
                key, self.dependency_container._dependencies[key]
            )

        for type_, resolver in self.dependency_container._resolvers.items():
            bot_instance.add_dependency_resolver(type_, resolver)

        self._dp.include_router(self._default_router)

        for middleware in self._message_middlewares:
            self._dp.message.middleware.register(middleware)

        for middleware in self._callback_query_middlewares:
            self._dp.callback_query.middleware.register(middleware)

        for middleware in self._inline_query_middlewares:
            self._dp.inline_query.middleware.register(middleware)

        for router in self._routers:
            self._dp.include_router(router)

        for handler_config in self._handlers:
            router = handler_config.router or self._default_router

            wrapped_handler = self._wrap_handler(
                handler_config.handler,
                {
                    **self.dependency_container._dependencies,
                    **handler_config.dependencies,
                },
            )

            self.handler_strategy.register(
                router,
                wrapped_handler,
                handler_config.filters,
                handler_config.event_type,
            )

        if self._error_handler:
            self._dp.errors.register(self._error_handler)

        for callback in self._startup_callbacks:
            bot_instance.add_startup_callback(callback)

        for callback in self._shutdown_callbacks:
            bot_instance.add_shutdown_callback(callback)

        if self._default_commands:
            bot_instance.add_startup_callback(
                lambda bot_instance: asyncio.create_task(
                    self._setup_commands(bot_instance.bot)
                )
            )

        Logger.info("Bot successfully built")
        return bot_instance


class BotBuilder(FastBotBuilder):
    """Алиас для сохранения обратной совместимости"""

    pass
