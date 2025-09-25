from functools import wraps
from aiogram.enums import ParseMode
from aiogram import types

from fastbot.engine import TemplateEngine


def apply_decorators(*decorators):
    def wrapper(f):
        for decorator in reversed(decorators):
            f = decorator(f)
        return f

    return wrapper


def with_template_engine(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        for arg in args:
            if isinstance(arg, TemplateEngine):
                return await func(*args, **kwargs)

        for arg in kwargs.values():
            if isinstance(arg, TemplateEngine):
                return await func(*args, **kwargs)

        raise ValueError("TemplateEngine не передан в аргументах")

    return wrapper


def with_parse_mode(parse_mode: str = ParseMode.HTML):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            if isinstance(result, dict):
                result["parse_mode"] = parse_mode
            return result

        return wrapper

    return decorator


def with_context(**default_context):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)

            if not isinstance(result, dict):
                return result

            auto_context = {}
            for arg in args:
                if isinstance(arg, types.Message):
                    auto_context["message"] = arg

            result["context"] = {
                **default_context,
                **auto_context,
                **result.get("context", {}),
            }
            return result

        return wrapper

    return decorator


def with_auto_reply(template_name, buttons_template=None):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            message = None
            callback = None
            this_context = True

            for arg in args:
                if isinstance(arg, types.Message):
                    message = arg
                elif isinstance(arg, types.CallbackQuery):
                    callback = arg

            if message is None and callback is None:
                message = kwargs.get("message")
                callback = kwargs.get("callback")

            if callback is not None and message is None:
                message = callback.message

            if message is None:
                raise ValueError(
                    "Message or CallbackQuery object not found in arguments"
                )

            ten = None
            for arg in args:
                if isinstance(arg, TemplateEngine):
                    ten = arg
                    break
            if ten is None:
                for value in kwargs.values():
                    if isinstance(value, TemplateEngine):
                        ten = value
                        break

            if ten is None:
                raise ValueError("TemplateEngine не найден!")

            func_result = await func(*args, **kwargs)

            if func_result is None:
                context = {
                    "user": kwargs.get("user"),
                    "message": message,
                    "callback": callback,
                    **{
                        k: v
                        for k, v in kwargs.items()
                        if k not in ["template_engine", "message", "callback"]
                    },
                }
                template_to_use = template_name
                buttons_to_use = buttons_template

            elif isinstance(func_result, dict):
                if func_result.get("skip_render"):
                    return func_result

                template_to_use = func_result.get("template_name", template_name)
                buttons_to_use = func_result.get("buttons_template", buttons_template)

                this_context = False

                if "context" in func_result:
                    context = func_result["context"]
                else:
                    context = {
                        "user": kwargs.get("user"),
                        "message": message,
                        "callback": callback,
                        **func_result,
                        **{
                            k: v
                            for k, v in kwargs.items()
                            if k not in ["template_engine", "message", "callback"]
                        },
                    }
            else:
                return func_result

            reply_params = {
                "message": message,
                "template_name": template_to_use,
                "context": context,
                "parse_mode": ParseMode.HTML,
                "row_width": 2,
            }

            if buttons_to_use and this_context:
                if isinstance(func_result, dict) and "buttons_context" in func_result:
                    reply_params["buttons_context"] = func_result["buttons_context"]
                reply_params["buttons_template"] = buttons_to_use

            return await ten.reply(**reply_params)

        return wrapper

    return decorator
