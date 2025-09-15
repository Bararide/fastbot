from typing import List, Union, Optional, Dict, Any
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    LoginUrl,
    CallbackGame,
    SwitchInlineQueryChosenChat,
)


class InlineMenuBuilder:
    def __init__(self):
        self.buttons = []
        self.row_width = None

    def add_row(
        self, *buttons: Union[InlineKeyboardButton, Dict[str, Any]]
    ) -> "InlineMenuBuilder":
        row = []
        for btn in buttons:
            if isinstance(btn, dict):
                row.append(self._create_button(**btn))
            elif isinstance(btn, InlineKeyboardButton):
                row.append(btn)
        self.buttons.append(row)
        return self

    def _create_button(
        self,
        text: str,
        callback_data: Optional[str] = None,
        url: Optional[str] = None,
        web_app: Optional[Union[WebAppInfo, str]] = None,
        login_url: Optional[LoginUrl] = None,
        switch_inline_query: Optional[str] = None,
        switch_inline_query_current_chat: Optional[str] = None,
        switch_inline_query_chosen_chat: Optional[SwitchInlineQueryChosenChat] = None,
        callback_game: Optional[CallbackGame] = None,
        pay: Optional[bool] = None,
        **kwargs,
    ) -> InlineKeyboardButton:
        if web_app and isinstance(web_app, str):
            web_app = WebAppInfo(url=web_app)

        return InlineKeyboardButton(
            text=text,
            callback_data=callback_data,
            url=url,
            web_app=web_app,
            login_url=login_url,
            switch_inline_query=switch_inline_query,
            switch_inline_query_current_chat=switch_inline_query_current_chat,
            switch_inline_query_chosen_chat=switch_inline_query_chosen_chat,
            callback_game=callback_game,
            pay=pay,
            **kwargs,
        )

    def set_row_width(self, width: int) -> "InlineMenuBuilder":
        self.row_width = width
        return self

    def build(self) -> InlineKeyboardMarkup:
        """Построить клавиатуру"""
        return InlineKeyboardMarkup(
            inline_keyboard=self.buttons,
        )

    @staticmethod
    def simple_menu(
        *buttons: Union[InlineKeyboardButton, Dict[str, Any]]
    ) -> InlineKeyboardMarkup:
        builder = InlineMenuBuilder()
        for btn in buttons:
            builder.add_row(btn)
        return builder.build()

    @staticmethod
    def grid_menu(
        buttons: List[Union[InlineKeyboardButton, Dict[str, Any]]],
        columns: int = 2,
    ) -> InlineKeyboardMarkup:
        builder = InlineMenuBuilder()
        row = []
        for i, btn in enumerate(buttons, 1):
            row.append(btn)
            if i % columns == 0:
                builder.add_row(*row)
                row = []
        if row:
            builder.add_row(*row)
        return builder.build()
