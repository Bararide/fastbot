from typing import Any
from aiogram import types
from decimal import Decimal
from aiogram import F

from src.config.celery_utils import run_task


async def hello_handler(message: types.Message, name: str) -> Any:
    return await message.answer(f"Hello, {name}!")


async def process_numbers(message: types.Message):
    try:
        num1, num2 = map(Decimal, message.text.split())
        task_id = run_task("tasks.calculate_sum", float(num1), float(num2))

        await message.answer(
            f"Задача сложения запущена!\n"
            f"Числа: {num1} + {num2}\n"
            f"ID задачи: {task_id}\n"
            f"Проверить статус: /status {task_id}"
        )
    except Exception as e:
        await message.answer(f"Ошибка: {str(e)}")


async def handle_invalid_input(message: types.Message):
    if message.text.startswith("/"):
        return
    await message.answer(
        "Пожалуйста, введите два числа через пробел (например: 5 3.14)"
    )
