from src.config.celery import celery_app


@celery_app.task(name="tasks.calculate_sum")
def calculate_sum(a: float, b: float) -> float:
    return a + b


@celery_app.task(name="tasks.generate_report")
def generate_report(arg1, arg2):
    return f"Report: {arg1}, {arg2}"
