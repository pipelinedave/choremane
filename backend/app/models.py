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

class UndoRequest(BaseModel):
    log_id: int
