from pydantic import BaseModel
from typing import Optional
from enum import IntEnum


class LANG(IntEnum):
    EN = 0
    RU = 1


class User(BaseModel):
    id: int
    username: Optional[str] = None
    first_name: str
    last_name: Optional[str] = None
    is_active: bool = True
    is_admin: bool = False
    registered_at: str
    lang: LANG = LANG.EN
