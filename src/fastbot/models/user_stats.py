from pydantic import BaseModel, Field


class UserStats(BaseModel):
    messages: int = Field(default=0, alias="total_messages")
    completed_tasks: int = 0
    active_tasks_count: int = 0

    class Config:
        allow_population_by_field_name = True
