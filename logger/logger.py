from loguru import logger
import sys
from typing import Optional, Dict, Any
import json


class Logger:
    _is_configured = False
    _default_level = "DEBUG"
    _default_format = "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>logger:{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    _default_rotation = "10 MB"
    _default_retention = "7 days"

    @staticmethod
    def configure(
        level: str = None,
        format: str = None,
        rotation: str = None,
        retention: str = None,
        log_file: Optional[str] = None,
        serialize: bool = False,
        **kwargs,
    ):
        Logger._default_level = level or Logger._default_level
        Logger._default_format = format or Logger._default_format
        Logger._default_rotation = rotation or Logger._default_rotation
        Logger._default_retention = retention or Logger._default_retention

        logger.remove()
        handlers = [
            {
                "sink": sys.stderr,
                "level": Logger._default_level,
                "format": Logger._default_format,
                **kwargs,
            }
        ]

        if log_file:
            handlers.append(
                {
                    "sink": log_file,
                    "level": Logger._default_level,
                    "format": Logger._default_format,
                    "rotation": Logger._default_rotation,
                    "retention": Logger._default_retention,
                    "enqueue": True,
                    "backtrace": True,
                    "diagnose": True,
                    "serialize": serialize,
                    **kwargs,
                }
            )

        logger.configure(handlers=handlers)
        Logger._is_configured = True

    @staticmethod
    def _ensure_configured():
        if not Logger._is_configured:
            Logger.configure()

    @staticmethod
    def log(
        level: str, message: str, context: Optional[Dict[str, Any]] = None, **kwargs
    ):
        Logger._ensure_configured()
        if context:
            message = f"{message} | {json.dumps(context, ensure_ascii=False)}"
        logger.log(level, message, **kwargs)

    @staticmethod
    def debug(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        Logger.log("DEBUG", message, context, **kwargs)

    @staticmethod
    def info(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        Logger.log("INFO", message, context, **kwargs)

    @staticmethod
    def warning(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        Logger.log("WARNING", message, context, **kwargs)

    @staticmethod
    def error(
        message: str,
        context: Optional[Dict[str, Any]] = None,
        exc_info: Optional[Exception] = None,
        **kwargs,
    ):
        kwargs["exc_info"] = exc_info
        Logger.log("ERROR", message, context, **kwargs)

    @staticmethod
    def critical(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        Logger.log("CRITICAL", message, context, **kwargs)

    @staticmethod
    def exception(message: str, context: Optional[Dict[str, Any]] = None, **kwargs):
        Logger._ensure_configured()
        logger.exception(message, **kwargs)
        if context:
            logger.debug(f"Context: {json.dumps(context, ensure_ascii=False)}")

    @staticmethod
    def add_context(**context):
        Logger._ensure_configured()
        logger.bind(**context)

    @staticmethod
    def get_logger():
        Logger._ensure_configured()
        return logger
