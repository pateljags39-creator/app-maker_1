from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


# --- User Schemas ---
class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str  # Raw password for creation


class UserResponse(UserBase):
    id: int
    # password_hash is internal and not exposed via API

    model_config = ConfigDict(from_attributes=True)


# --- Status Schemas ---
class StatusBase(BaseModel):
    name: str
    is_completion_state: bool = False


class StatusCreate(StatusBase):
    pass  # No extra fields for creation beyond base


class StatusResponse(StatusBase):
    id: int
    project_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Comment Schemas ---
class CommentBase(BaseModel):
    content: str


class CommentCreate(CommentBase):
    user_id: int  # User making the comment


class CommentResponse(CommentBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime
    user: Optional[UserResponse] = None  # Nested user for response

    model_config = ConfigDict(from_attributes=True)


# --- Attachment Schemas ---
class AttachmentBase(BaseModel):
    file_url: str
    filename: str


class AttachmentCreate(AttachmentBase):
    pass


class AttachmentResponse(AttachmentBase):
    id: int
    task_id: int

    model_config = ConfigDict(from_attributes=True)


# --- Task Schemas ---
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status_id: int
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    priority: Optional[str] = None  # e.g., 'Low', 'Medium', 'High'
    parent_task_id: Optional[int] = None


class TaskCreate(TaskBase):
    project_id: int  # Required when creating a task


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[int] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    priority: Optional[str] = None
    parent_task_id: Optional[int] = None
    closed_at: Optional[datetime] = None  # Can be set when task is completed


class TaskResponse(TaskBase):
    id: int
    project_id: int
    created_at: datetime
    closed_at: Optional[datetime] = None

    # Nested relationships
    status: Optional[StatusResponse] = None
    assignee: Optional[UserResponse] = None
    comments: List[CommentResponse] = []
    attachments: List[AttachmentResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Project Schemas ---
class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    owner_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class ProjectResponse(ProjectBase):
    id: int

    # Nested relationships
    owner: Optional[UserResponse] = None
    statuses: List[StatusResponse] = []
    tasks: List[TaskResponse] = []  # Tasks associated with the project

    model_config = ConfigDict(from_attributes=True)


# --- Metrics Schema ---
class ProjectMetricsResponse(BaseModel):
    project_id: int
    total_tasks: int
    completed_tasks: int
    open_tasks: int
    average_completion_time_days: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

# AUTO-STUB: missing module attributes referenced by backend/main.py (Local App Creator post-fixup)
from pydantic import BaseModel as _AutoBaseModel
class Comment(_AutoBaseModel):
    pass

class Project(_AutoBaseModel):
    pass

class ProjectMetrics(_AutoBaseModel):
    pass

class ProjectWithDetails(_AutoBaseModel):
    pass

class Status(_AutoBaseModel):
    pass

class Task(_AutoBaseModel):
    pass

class User(_AutoBaseModel):
    pass

