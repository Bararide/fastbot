from datetime import datetime
from models import User, UserStats
from FastBot.decorators import register_context


@register_context("profile")
async def profile_context(user: User, stats: UserStats):
    return {
        "user": user,
        "stats": {
            "messages": 0,
            "completed_tasks": 0,
            "active_tasks": 0,
        },
        "is_admin": user.is_admin,
    }


@register_context("profile_error")
async def profile_error_context(user: User, error_message: str):
    return {
        "user": user,
        "stats": {
            "messages": 0,
            "completed_tasks": 0,
            "active_tasks": 0,
        },
        "is_admin": user.is_admin,
        "error_message": error_message,
    }


@register_context("app")
async def app_context():
    return {"open": "open"}


@register_context("profile_buttons")
async def profile_buttons_context(user: User):
    return {"user_id": user.id, "is_admin": user.is_admin}


@register_context("error_message")
async def error_message_context(error_message: str):
    return {"error_message": error_message}


@register_context("start")
async def start_context(user: User):
    return {"user": user, "welcome_message": f"Добро пожаловать, {user.first_name}!"}


@register_context("registration_error")
async def registration_error_context(error: str):
    return {"error": error, "has_access": False}


@register_context("registration")
async def registration_context(user: User, success: bool):
    return {
        "success": success,
        "user": user,
        "message": "Регистрация прошла успешно!" if success else "Ошибка регистрации",
    }


@register_context("admin_list")
async def admin_list_context(admins: list):
    return {
        "admins": admins,
        "count": len(admins),
        "last_updated": datetime.now().isoformat(),
    }


@register_context("access_denied")
async def access_denied_context(message: str):
    return {"error_message": message, "has_access": False}
