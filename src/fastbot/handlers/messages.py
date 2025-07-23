from decimal import Decimal
from typing import Any, Dict

from aiogram import types
from aiogram.enums import ParseMode

from src.FastBotLib.engine.templates.template_engine import TemplateEngine
from src.FastBotLib.decorators.with_template_engine import (
    with_auto_reply,
    with_parse_mode,
    with_template_engine,
)
from src.config.celery_utils import run_task
from src.FastBotLib.logger.logger import Logger


@with_template_engine
@with_auto_reply("commands/hello.j2")
async def hello_handler(
    message: types.Message, name: str, template_engine: TemplateEngine
) -> Any:
    return {"context": {"name": name}}


@with_template_engine
@with_auto_reply(
    template_name="commands/process_numbers_success.j2",
    buttons_template="buttons/process_numbers_buttons.j2",
)
@with_parse_mode(ParseMode.HTML)
async def process_numbers(
    message: types.Message, template_engine: TemplateEngine
) -> Dict[str, Any]:
    try:
        parts = message.text.split()
        if len(parts) != 2:
            raise ValueError("Требуется ровно два числа через пробел")

        num1, num2 = map(Decimal, parts)
        task_id = run_task("tasks.calculate_sum", float(num1), float(num2))

        context = {
            "num1": f"{num1:.2f}",
            "num2": f"{num2:.2f}",
            "task_id": str(task_id),
            "error": None,
        }

        return {"context": context, "buttons_context": {"task_id": task_id}}

    except Exception as e:
        Logger.error(f"Error processing numbers: {str(e)}", exc_info=True)
        return {"context": {"error": str(e), "numbers": None, "task_id": None}}


@with_template_engine
@with_auto_reply("commands/invalid_input.j2")
@with_parse_mode(ParseMode.MARKDOWN)
async def handle_invalid_input(
    message: types.Message, template_engine: TemplateEngine
) -> Dict[str, Any]:
    if message.text.startswith("/"):
        return {"skip": True}

    return {"context": {"command_example": "5 3.14"}}
