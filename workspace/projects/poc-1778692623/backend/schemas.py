from datetime import datetime
from pydantic import BaseModel, ConfigDict

class NoteBase(BaseModel):
    """Base schema for a Note, containing common fields for creation and update."""
    title: str
    body: str

class NoteCreate(NoteBase):
    """Schema for creating a new Note."""
    pass

class NoteUpdate(NoteBase):
    """Schema for updating an existing Note."""
    # All fields from NoteBase are required for an update as per BRD R5
    # If partial updates were allowed, fields could be Optional[str] = None
    pass

class NoteResponse(NoteBase):
    """Schema for returning a Note, including read-only fields."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)