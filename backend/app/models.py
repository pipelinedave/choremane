from pydantic import BaseModel, Field
from typing import Optional

class Chore(BaseModel):
    id: Optional[int] = None
    name: str
    interval_days: int
    due_date: str
    done: bool = Field(default=False)
    done_by: Optional[str] = Field(default=None)
    archived: bool = Field(default=False)
    owner_email: Optional[str] = None  # Email of the user who owns the chore (null for shared chores)
    is_private: bool = Field(default=False)  # True if the chore is private to the owner

class UndoRequest(BaseModel):
    log_id: int
