from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import datetime, date
from typing import Optional, List
from enum import Enum

# --- Enums ---
class PriorityEnum(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"

# --- Base Schemas (common fields for creation/update) ---

class UserBase(BaseModel):
    email: EmailStr

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class StatusBase(BaseModel):
    name: str
    is_completion_state: bool = False

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status_id: Optional[int] = None # Will be set by default or chosen
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    priority: PriorityEnum = PriorityEnum.MEDIUM
    parent_task_id: Optional[int] = None

class CommentBase(BaseModel):
    content: str

class AttachmentBase(BaseModel):
    file_url: str
    filename: str

# --- Create Schemas (for POST requests) ---

class UserCreate(UserBase):
    password: str

class ProjectCreate(ProjectBase):
    # owner_id will be derived from authenticated user
    pass

class StatusCreate(StatusBase):
    # project_id will be derived from path parameter
    pass

class TaskCreate(TaskBase):
    # project_id will be derived from path parameter
    pass

class CommentCreate(CommentBase):
    # task_id will be derived from path parameter
    # user_id will be derived from authenticated user
    pass

class AttachmentCreate(AttachmentBase):
    # task_id will be derived from path parameter
    pass

# --- Update Schemas (for PUT/PATCH requests) ---

class UserUpdate(UserBase):
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class ProjectUpdate(ProjectBase):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class StatusUpdate(StatusBase):
    name: Optional[str] = None
    is_completion_state: Optional[bool] = None

class TaskUpdate(TaskBase):
    title: Optional[str] = None
    description: Optional[str] = None
    status_id: Optional[int] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None
    priority: Optional[PriorityEnum] = None
    parent_task_id: Optional[int] = None
    closed_at: Optional[datetime] = None # Allow setting closed_at on update

class CommentUpdate(CommentBase):
    content: Optional[str] = None

class AttachmentUpdate(AttachmentBase):
    file_url: Optional[str] = None
    filename: Optional[str] = None

# --- Read Schemas (for GET responses, includes IDs and relationships) ---

class User(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Attachment(AttachmentBase):
    id: int
    task_id: int
    model_config = ConfigDict(from_attributes=True)

class Comment(CommentBase):
    id: int
    task_id: int
    user_id: int
    created_at: datetime
    user: User # Nested user object
    model_config = ConfigDict(from_attributes=True)

class Status(StatusBase):
    id: int
    project_id: int
    model_config = ConfigDict(from_attributes=True)

class Task(TaskBase):
    id: int
    project_id: int
    created_at: datetime
    closed_at: Optional[datetime] = None
    
    # Nested relationships
    status: Optional[Status] = None
    assignee: Optional[User] = None
    comments: List[Comment] = []
    attachments: List[Attachment] = []
    
    model_config = ConfigDict(from_attributes=True)

# To handle potential circular dependency between Task and Project/Task (parent_task)
# We define Project and then update forward refs for Task
class Project(ProjectBase):
    id: int
    owner_id: int
    
    # Nested relationships
    owner: User
    statuses: List[Status] = []
    tasks: List[Task] = []
    
    model_config = ConfigDict(from_attributes=True)

# Update forward references for Task to resolve circular dependencies
# Task.model_rebuild() # Pydantic v2 handles this automatically if types are strings or imported correctly.
# If issues arise, uncomment and use Task.model_rebuild() or Project.model_rebuild()

# --- Authentication Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Metrics Schemas ---

class ProjectMetrics(BaseModel):
    total_tasks: int
    completed_tasks: int
    open_tasks: int
    average_cycle_time_days: Optional[float] = None # Average time from created_at to closed_at for completed tasks
    tasks_by_status: dict[str, int]
    tasks_by_assignee: dict[str, int]
    completion_rate: float
    model_config = ConfigDict(from_attributes=True)