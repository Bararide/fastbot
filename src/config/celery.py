from celery import Celery
import os

os.environ.setdefault("CELERY_IMPORTS", "src.tasks.test_tasks")

celery_app = Celery(
    "tasks",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/1",
    include=["src.tasks.test_tasks"],
)

celery_app.conf.update(
    task_serializer="json", result_serializer="json", timezone="Europe/Moscow"
)

celery_app.autodiscover_tasks(["src.tasks"], force=True)
