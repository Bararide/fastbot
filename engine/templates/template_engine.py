from asyncio import Lock
from pathlib import Path
from typing import Any, Optional, Union, Dict, List
import json
import re
from datetime import datetime

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
    Template,
    TemplateNotFound,
    TemplateSyntaxError,
    TemplateRuntimeError,
    UndefinedError,
)

from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    ForceReply,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.utils.markdown import (
    hbold,
    hitalic,
    hunderline,
    hstrikethrough,
    hlink,
    hcode,
    hide_link,
)
from aiogram.enums import ParseMode

from fastbot.logger import Logger


class TemplateEngineError(Exception):
    pass


class TemplateNotFoundError(TemplateEngineError):
    pass


class TemplateRenderError(TemplateEngineError):
    pass


class TemplateSyntaxError(TemplateEngineError):
    pass


class TemplateContextError(TemplateEngineError):
    pass


class TemplateEngine:
    def __init__(
        self,
        template_dirs: Union[str, List[str]],
        extensions: Optional[List[str]] = ["jinja2.ext.i18n"],
        auto_reload: bool = True,
        cache_size: int = 400,
        enable_async: bool = True,
        **env_options,
    ):
        if isinstance(template_dirs, str):
            template_dirs = [template_dirs]

        self.template_dirs = [Path(d) for d in template_dirs]
        self.loader = FileSystemLoader(self.template_dirs)

        default_extensions = [
            "jinja2.ext.i18n",
            "jinja2.ext.do",
            "jinja2.ext.loopcontrols",
            "jinja2.ext.debug",
        ]

        if extensions:
            default_extensions.extend(extensions)

        self.env = Environment(
            loader=self.loader,
            autoescape=select_autoescape(),
            extensions=default_extensions,
            auto_reload=auto_reload,
            cache_size=cache_size,
            enable_async=enable_async,
            **env_options,
        )

        self._register_custom_filters()
        self._register_custom_functions()

        self._template_cache: Dict[str, Template] = {}
        self._cache_lock = Lock()

    def _register_custom_filters(self):
        """Регистрация пользовательских фильтров"""
        self.env.filters.update(
            {
                "bold": lambda x: hbold(x),
                "italic": lambda x: hitalic(x),
                "underline": lambda x: hunderline(x),
                "strikethrough": lambda x: hstrikethrough(x),
                "link": lambda x, url: hlink(x, url),
                "code": lambda x: hcode(x),
                "hide_link": lambda x: hide_link(x),
                "json": lambda x: json.dumps(x, ensure_ascii=False),
                "format_date": self._format_date,
                "truncate": self._truncate,
                "markdown_escape": self._markdown_escape,
                "telegram_escape": self._telegram_escape,
                "plural": self._plural_form,
            }
        )

    def _register_custom_functions(self):
        """Регистрация пользовательских функций"""
        self.env.globals.update(
            {
                "now": datetime.now,
                "generate_inline_keyboard": self.generate_inline_keyboard,
                "generate_reply_keyboard": self.generate_reply_keyboard,
                "remove_keyboard": lambda: ReplyKeyboardRemove(),
                "force_reply": lambda: ForceReply(),
                "Message": Message,
                "hbold": hbold,
                "hitalic": hitalic,
                "hunderline": hunderline,
                "hstrikethrough": hstrikethrough,
                "hlink": hlink,
                "hcode": hcode,
                "hide_link": hide_link,
                "parse_mode": ParseMode,
            }
        )

    async def reply(
        self,
        message: Message,
        template_name: str,
        context: Optional[dict] = None,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        buttons_template: Optional[str] = None,
        buttons_context: Optional[dict] = None,
        row_width: int = 2,
        **kwargs,
    ) -> Any:
        context = context or {}
        buttons_context = buttons_context or {}

        response = await self.render_template(
            template_name, parse_mode=parse_mode, **context
        )

        if buttons_template:
            buttons = await self.load_buttons_from_template(
                buttons_template, **buttons_context
            )
            response["reply_markup"] = await self.generate_inline_keyboard(
                buttons, row_width=row_width
            )

        if reply_markup:
            response["reply_markup"] = reply_markup

        return await message.answer(**response)

    async def render(
        self,
        template_name: str,
        context: Optional[dict] = None,
        buttons_template: Optional[str] = None,
        buttons_context: Optional[dict] = None,
        row_width: int = 2,
        **kwargs,
    ) -> dict:
        context = context or {}
        buttons_context = buttons_context or {}

        response = await self.render_template(template_name, **context)

        if buttons_template:
            buttons = await self.load_buttons_from_template(
                buttons_template, **buttons_context
            )
            response["reply_markup"] = await self.generate_inline_keyboard(
                buttons, row_width=row_width
            )

        return response

    async def render_template(
        self,
        template_name: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        **context,
    ) -> Union[str, Dict[str, Any]]:
        try:
            template = await self._get_template(template_name)
            rendered = await template.render_async(**context)

            result = {"text": rendered}
            if parse_mode:
                result["parse_mode"] = parse_mode
            if disable_web_page_preview is not None:
                result["disable_web_page_preview"] = disable_web_page_preview

            return result
        except TemplateNotFound as e:
            raise TemplateNotFoundError(f"Template not found: {template_name}") from e
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(
                f"Syntax error in template {template_name}: {e}"
            ) from e
        except (TemplateRuntimeError, UndefinedError) as e:
            raise TemplateRenderError(
                f"Error rendering template {template_name}: {e}"
            ) from e
        except Exception as e:
            raise TemplateEngineError(
                f"Unexpected error in template {template_name}: {e}"
            ) from e

    async def answer(self, message: Message, response) -> Any:
        return await message.answer(**response)

    async def render_message(
        self,
        message: Message,
        template_name: str,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
        **context,
    ) -> Dict[str, Any]:
        template_data = await self.render_template(
            template_name,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            **context,
        )

        if reply_markup:
            template_data["reply_markup"] = reply_markup

        return template_data

    async def render_response(
        self,
        template_name: str,
        context: Optional[Dict[str, Any]] = None,
        parse_mode: Optional[str] = None,
        disable_web_page_preview: Optional[bool] = None,
        reply_markup: Optional[Union[InlineKeyboardMarkup, ReplyKeyboardMarkup]] = None,
    ) -> Dict[str, Any]:
        context = context or {}
        template_data = await self.render_template(
            template_name,
            parse_mode=parse_mode,
            disable_web_page_preview=disable_web_page_preview,
            **context,
        )

        if reply_markup:
            template_data["reply_markup"] = reply_markup

        return template_data

    async def render_html_template(
        self,
        template_name: str,
        context: Optional[dict] = None,
        **kwargs,
    ) -> str:
        try:
            template = await self._get_template(template_name)
            rendered = await template.render_async(**(context or {}))
            return rendered
        except TemplateNotFound as e:
            raise TemplateNotFoundError(
                f"HTML template not found: {template_name}"
            ) from e
        except TemplateSyntaxError as e:
            raise TemplateSyntaxError(
                f"Syntax error in HTML template {template_name}: {e}"
            ) from e
        except (TemplateRuntimeError, UndefinedError) as e:
            raise TemplateRenderError(
                f"Error rendering HTML template {template_name}: {e}"
            ) from e
        except Exception as e:
            raise TemplateEngineError(
                f"Unexpected error in HTML template {template_name}: {e}"
            ) from e

    async def generate_inline_keyboard(
        self, buttons: List[Dict[str, Any]], row_width: int = 3, **kwargs
    ) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()

        for button in buttons:
            if "callback_data" in button:
                builder.button(
                    text=button["text"], callback_data=button["callback_data"]
                )
            elif "url" in button:
                builder.button(text=button["text"], url=button["url"])
            elif "web_app" in button:
                builder.button(text=button["text"], web_app=button["web_app"])
            elif "login_url" in button:
                builder.button(text=button["text"], login_url=button["login_url"])
            elif "switch_inline_query" in button:
                builder.button(
                    text=button["text"],
                    switch_inline_query=button["switch_inline_query"],
                )
            elif "switch_inline_query_current_chat" in button:
                builder.button(
                    text=button["text"],
                    switch_inline_query_current_chat=button[
                        "switch_inline_query_current_chat"
                    ],
                )
            elif "pay" in button:
                builder.button(text=button["text"], pay=button["pay"])

        builder.adjust(row_width)
        return builder.as_markup(**kwargs)

    async def generate_reply_keyboard(
        self,
        buttons: List[Union[str, Dict[str, Any]]],
        row_width: int = 3,
        resize_keyboard: bool = True,
        one_time_keyboard: bool = False,
        selective: bool = False,
        **kwargs,
    ) -> ReplyKeyboardMarkup:
        builder = ReplyKeyboardBuilder()

        for button in buttons:
            if isinstance(button, str):
                builder.button(text=button)
            elif isinstance(button, dict):
                if "request_contact" in button and button["request_contact"]:
                    builder.button(text=button["text"], request_contact=True)
                elif "request_location" in button and button["request_location"]:
                    builder.button(text=button["text"], request_location=True)
                elif "request_poll" in button and button["request_poll"]:
                    builder.button(
                        text=button["text"], request_poll=button["request_poll"]
                    )
                elif "request_user" in button:
                    builder.button(
                        text=button["text"], request_user=button["request_user"]
                    )
                elif "request_chat" in button:
                    builder.button(
                        text=button["text"], request_chat=button["request_chat"]
                    )
                else:
                    builder.button(text=button["text"])

        builder.adjust(row_width)
        return builder.as_markup(
            resize_keyboard=resize_keyboard,
            one_time_keyboard=one_time_keyboard,
            selective=selective,
            **kwargs,
        )

    async def load_buttons_from_template(
        self, template_name: str, **context
    ) -> List[Dict[str, Any]]:
        try:
            template = await self._get_template(template_name)
            rendered = await template.render_async(**context)

            rendered_clean = rendered.strip()
            for key, value in context.items():
                rendered_clean = rendered_clean.replace(
                    f'"{{{{{key}}}}}"', json.dumps(value)
                )
                rendered_clean = rendered_clean.replace(
                    f"'{{{{{key}}}}}'", json.dumps(value)
                )

            buttons = json.loads(rendered_clean)

            if not isinstance(buttons, list):
                raise ValueError("Buttons template must return a list")

            return buttons

        except json.JSONDecodeError as e:
            error_msg = (
                f"Invalid JSON in buttons template: {e}\nTemplate content: {rendered}"
            )
            Logger.error(error_msg)
            raise TemplateEngineError(error_msg) from e
        except Exception as e:
            Logger.error(f"Failed to load buttons: {e}")
            raise

    async def _get_template(self, template_name: str) -> Template:
        async with self._cache_lock:
            if template_name in self._template_cache:
                return self._template_cache[template_name]

            template = self.env.get_template(template_name)
            self._template_cache[template_name] = template
            return template

    @staticmethod
    def _format_date(value, format_str="%Y-%m-%d %H:%M:%S"):
        """Форматирует дату"""
        if isinstance(value, str):
            try:
                value = datetime.fromisoformat(value)
            except ValueError:
                return value
        return value.strftime(format_str) if value else ""

    @staticmethod
    def _truncate(value, length=100, end="..."):
        if not isinstance(value, str):
            value = str(value)
        return value[:length] + (end if len(value) > length else "")

    @staticmethod
    def _markdown_escape(text: str) -> str:
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

    @staticmethod
    def _telegram_escape(text: str) -> str:
        escape_chars = r"_*[]()~`>#+-=|{}.!"
        return re.sub(f"([{re.escape(escape_chars)}])", r"\\\1", text)

    @staticmethod
    def _plural_form(number: int, forms: List[str]) -> str:
        if not forms or len(forms) < 3:
            return ""

        number = abs(number) % 100
        if 11 <= number <= 19:
            return forms[2]

        number %= 10
        if number == 1:
            return forms[0]
        if 2 <= number <= 4:
            return forms[1]
        return forms[2]
