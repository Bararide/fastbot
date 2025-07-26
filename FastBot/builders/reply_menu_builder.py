from typing import (
    List,
    Union,
)

from aiogram.utils.keyboard import ReplyKeyboardMarkup, KeyboardButton


class ReplyMenuBuilder:
    def __init__(self):
        self.buttons = []
        self.resize_keyboard = True
        self.one_time_keyboard = False
        self.selective = False
        self.placeholder = None
        self.input_field_placeholder = None

    def add_row(self, *buttons: Union[str, KeyboardButton]) -> "ReplyMenuBuilder":
        row = []
        for btn in buttons:
            if isinstance(btn, str):
                row.append(KeyboardButton(text=btn))
            elif isinstance(btn, KeyboardButton):
                row.append(btn)
        self.buttons.append(row)
        return self

    def set_resize_keyboard(self, resize: bool) -> "ReplyMenuBuilder":
        self.resize_keyboard = resize
        return self

    def set_one_time_keyboard(self, one_time: bool) -> "ReplyMenuBuilder":
        self.one_time_keyboard = one_time
        return self

    def set_selective(self, selective: bool) -> "ReplyMenuBuilder":
        self.selective = selective
        return self

    def set_placeholder(self, placeholder: str) -> "ReplyMenuBuilder":
        self.placeholder = placeholder
        return self

    def set_input_field_placeholder(self, placeholder: str) -> "ReplyMenuBuilder":
        self.input_field_placeholder = placeholder
        return self

    def build(self) -> ReplyKeyboardMarkup:
        return ReplyKeyboardMarkup(
            keyboard=self.buttons,
            resize_keyboard=self.resize_keyboard,
            one_time_keyboard=self.one_time_keyboard,
            selective=self.selective,
            placeholder=self.placeholder,
            input_field_placeholder=self.input_field_placeholder,
        )

    @staticmethod
    def simple_menu(*buttons: str, resize: bool = True) -> ReplyKeyboardMarkup:
        builder = ReplyMenuBuilder().set_resize_keyboard(resize)
        for btn in buttons:
            builder.add_row(btn)
        return builder.build()

    @staticmethod
    def grid_menu(
        buttons: List[str], columns: int = 2, resize: bool = True
    ) -> ReplyKeyboardMarkup:
        builder = ReplyMenuBuilder().set_resize_keyboard(resize)
        row = []
        for i, btn in enumerate(buttons, 1):
            row.append(btn)
            if i % columns == 0:
                builder.add_row(*row)
                row = []
        if row:
            builder.add_row(*row)
        return builder.build()
