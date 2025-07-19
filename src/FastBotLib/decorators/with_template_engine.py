from functools import wraps
from aiogram.enums import ParseMode
from aiogram import types


def apply_decorators(*decorators):
    """Применяет несколько декораторов последовательно"""

    def wrapper(f):
        for decorator in reversed(decorators):
            f = decorator(f)
        return f

    return wrapper


def with_template_engine(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if "template_engine" not in kwargs:
            raise ValueError("TemplateEngine not found!")
        return await func(*args, **kwargs)

    return wrapper


def with_auto_reply(template_name, buttons_template=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            message = kwargs.get("message")
            if message is None:
                for arg in args:
                    if isinstance(arg, types.Message):
                        message = arg
                        break

            if message is None:
                raise ValueError("Message object not found in arguments")

            template_engine = kwargs["template_engine"]

            context = {
                "user": kwargs.get("user"),
                "message": message,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["template_engine", "message"]
                },
            }

            reply_params = {
                "message": message,
                "template_name": template_name,
                "context": context,
                "parse_mode": ParseMode.HTML,
                "row_width": 2,
            }

            if buttons_template:
                reply_params["buttons_template"] = buttons_template

            return await template_engine.reply(**reply_params)

        return wrapper

    return decorator
