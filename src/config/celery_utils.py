from .celery import celery_app
from celery.result import AsyncResult
from src.FastBotLib.logger.logger import Logger


def get_task_result(task_id):
    Logger.info(f"Get task result: {task_id}")
    return AsyncResult(task_id, app=celery_app)


def run_task(task_name, *args, **kwargs):
    Logger.info(f"Run task: {task_name}")
    task = celery_app.send_task(task_name, args=args, kwargs=kwargs)
    Logger.info(f"Return task id: {task.id}")
    return task.id
