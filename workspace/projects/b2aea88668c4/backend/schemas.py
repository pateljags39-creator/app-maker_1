from datetime import datetime
from pydantic import BaseModel, ConfigDict


class NoteBase(BaseModel):
    title: str
    body: str


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: str | None = None
    body: str | None = None


class Note(NoteBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)