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


@register_context("profile_buttons")
async def profile_buttons_context(user: User):
    return {"user_id": user.id, "is_admin": user.is_admin}


@register_context("test_photo")
async def test_photo_context(photo_id):
    return {"photo_id": photo_id}


@register_context("test_photo_error")
async def test_photo_error_context():
    return {}


@register_context("choose_lang")
async def choose_lang_context():
    return {}


@register_context("choose_lang_buttons")
async def choose_lang_buttons_context(user_id):
    return {"user_id": user_id}


@register_context("choose_lang_error")
async def choose_lang_error_context(error: str):
    return {"error": error}


@register_context("number_status")
async def number_status_context(task_id, result):
    return {"task_id": task_id, "result": result}


@register_context("number_status_error")
async def number_status_error_context(task_id):
    return {"task_id": task_id}


@register_context("app")
async def app_context():
    return {"open": "open"}


@register_context("error_message")
async def error_message_context(error_message: str):
    return {"error_message": error_message}


@register_context("start")
async def start_context(user: User):
    return {"user": user, "welcome_message": f"Добро пожаловать, {user.first_name}!"}


@register_context("registration_error")
async def registration_error_context(error: str):
    return {"error": error, "has_access": False, "success": False}


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
