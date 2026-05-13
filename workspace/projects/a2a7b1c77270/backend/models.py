from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    projects = relationship("Project", back_populates="owner")
    assigned_tasks = relationship("Task", back_populates="assignee")
    comments = relationship("Comment", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(Date)
    end_date = Column(Date)

    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    statuses = relationship("Status", back_populates="project", cascade="all, delete-orphan")


class Status(Base):
    __tablename__ = "statuses"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String, nullable=False)
    is_completion_state = Column(Boolean, default=False)

    project = relationship("Project", back_populates="statuses")
    tasks = relationship("Task", back_populates="status")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, index=True, nullable=False)
    description = Column(Text)
    status_id = Column(Integer, ForeignKey("statuses.id"), nullable=False)
    due_date = Column(DateTime, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    priority = Column(String, default="Medium")  # e.g., "Low", "Medium", "High"
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)  # Self-referencing for subtasks
    created_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime, nullable=True)  # Set when task moves to a completion status

    project = relationship("Project", back_populates="tasks")
    status = relationship("Status", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks")

    # Self-referencing relationship for subtasks
    parent_task = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent_task", cascade="all, delete-orphan")

    comments = relationship("Comment", back_populates="task", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="task", cascade="all, delete-orphan")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    task = relationship("Task", back_populates="comments")
    user = relationship("User", back_populates="comments")


class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    file_url = Column(String, nullable=False)
    filename = Column(String, nullable=False)

    task = relationship("Task", back_populates="attachments")