from .context_decorator import register_context

from .with_template_engine import (
    apply_decorators,
    with_template_engine,
    with_parse_mode,
    with_context,
    with_auto_reply,
)

from .dependencies import inject

from .reply_menu_decorator import menu, menu_handler

__all__ = [
    "with_template_engine",
    "apply_decorators",
    "register_context",
    "with_parse_mode",
    "with_context",
    "with_auto_reply",
    "menu",
    "menu_handler",
    "inject",
]
