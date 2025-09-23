from fastapi import Request
from fastbot.engine import WebTemplateEngine


def get_web_engine(request: Request) -> WebTemplateEngine:
    return request.app.state.bot_instance.get_dependency("web_engine")


def get_template_engine(request: Request) -> WebTemplateEngine:
    return request.app.state.bot_instance.get_dependency("template_engine")


def get_context_engine(request: Request) -> WebTemplateEngine:
    return request.app.state.bot_instance.get_dependency("context_engine")
