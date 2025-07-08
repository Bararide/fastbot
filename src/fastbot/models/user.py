from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    id: int
    username: Optional[str]
    first_name: str
    last_name: Optional[str]
    is_active: bool = True
    is_admin: bool = False
    registered_at: str
