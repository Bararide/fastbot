from FastBot.logger import Logger
from typing import Any


async def error_handler(exception: Exception) -> Any:
    """Глобальный обработчик ошибок"""

    Logger.error(f"Error occurred: {exception}", exc_info=exception)
