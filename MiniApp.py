import os
from typing import (
    Callable,
    Optional,
)

from aiogram import F, Bot, types
from aiogram.types import WebAppInfo

from fastapi import FastAPI, Request, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse


class MiniAppConfig:
    def __init__(
        self,
        title: str = "Telegram Mini App",
        description: str = "My Awesome Mini App",
        path: str = "/mini-app",
        static_dir: str = "static",
        webhook_path: Optional[str] = None,
        webhook_handler: Optional[Callable] = None,
        ws_handler: Optional[Callable] = None,
    ):
        self.title = title
        self.description = description
        self.path = path
        self.static_dir = static_dir
        self.webhook_path = webhook_path
        self.webhook_handler = webhook_handler
        self.ws_handler = ws_handler


class MiniAppManager:
    def __init__(self, bot: Bot, config: MiniAppConfig):
        self.bot = bot
        self.config = config
        self.app = FastAPI(title=config.title, description=config.description)
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        self._setup_routes()

    def _setup_routes(self):
        @self.app.get(self.config.path, response_class=HTMLResponse)
        async def mini_app(request: Request):
            return self._generate_mini_app_html(request)

        if self.config.static_dir and os.path.exists(self.config.static_dir):
            self.app.mount(
                "/static", StaticFiles(directory=self.config.static_dir), "static"
            )

        if self.config.webhook_path and self.config.webhook_handler:

            @self.app.post(self.config.webhook_path)
            async def webhook_handler(data: dict):
                return await self.config.webhook_handler(data)

        if self.config.ws_handler:

            @self.app.websocket("/ws")
            async def websocket_endpoint(websocket: WebSocket):
                await self.config.ws_handler(websocket)

    def get_webapp_button(
        self, text: str = "Open App", url: Optional[str] = None
    ) -> types.InlineKeyboardButton:
        """Create a button to open the Mini App"""
        web_app_url = url or f"https://{os.getenv('WEBAPP_DOMAIN')}{self.config.path}"
        return types.InlineKeyboardButton(
            text=text, web_app=WebAppInfo(url=web_app_url)
        )
