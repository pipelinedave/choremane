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

class User(BaseModel):
    email: str
    name: Optional[str] = None
    given_name: Optional[str] = None
    family_name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: Optional[str] = None
    id_token: Optional[str] = None
