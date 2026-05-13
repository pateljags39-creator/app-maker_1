import uvicorn
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from database import SessionLocal, engine, Base
import models
import schemas

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Team Todo App API",
    description="API for managing projects, tasks, statuses, users, and comments.",
    version="0.1.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Dependency to get the DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

router = APIRouter(prefix="/api")

# --- User Endpoints ---
@router.get("/users", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all users.
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# --- Project Endpoints ---
@router.get("/projects", response_model=List[schemas.Project])
def read_projects(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve a list of all projects.
    """
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return projects

@router.post("/projects", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db)):
    """
    Create a new project.
    """
    db_project = models.Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

@router.get("/projects/{project_id}", response_model=schemas.ProjectWithDetails)
def read_project(project_id: int, db: Session = Depends(get_db)):
    """
    Retrieve detailed information for a single project, including its associated tasks and statuses.
    """
    project = db.query(models.Project).options(
        joinedload(models.Project.tasks).joinedload(models.Task.assignee),
        joinedload(models.Project.statuses)
    ).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

# --- Task Endpoints ---
@router.post("/projects/{project_id}/tasks", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task(project_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    """
    Create a new task within a specific project.
    """
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    # Ensure the initial status_id belongs to this project
    if task.status_id:
        db_status = db.query(models.Status).filter(
            models.Status.id == task.status_id,
            models.Status.project_id == project_id
        ).first()
        if db_status is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status_id for this project")

    db_task = models.Task(**task.model_dump(), project_id=project_id, created_at=datetime.now())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """
    Update an existing task's details, such as its status, assignee, or description.
    Handles setting/unsetting `closed_at` based on status change.
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    old_status_id = db_task.status_id
    new_status_id = task_update.status_id

    update_data = task_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_task, key, value)

    # Handle closed_at logic if status_id is being updated
    if new_status_id is not None and new_status_id != old_status_id:
        new_status = db.query(models.Status).filter(models.Status.id == new_status_id).first()
        if new_status is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid status_id")

        if new_status.is_completion_state and db_task.closed_at is None:
            db_task.closed_at = datetime.now()
        elif not new_status.is_completion_state and db_task.closed_at is not None:
            db_task.closed_at = None

    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """
    Delete a task.
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db.delete(db_task)
    db.commit()
    return

# --- Status Endpoints ---
@router.post("/projects/{project_id}/statuses", response_model=schemas.Status, status_code=status.HTTP_201_CREATED)
def create_status(project_id: int, status_create: schemas.StatusCreate, db: Session = Depends(get_db)):
    """
    Create a new custom status for a specific project.
    """
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    db_status = models.Status(**status_create.model_dump(), project_id=project_id)
    db.add(db_status)
    db.commit()
    db.refresh(db_status)
    return db_status

# --- Comment Endpoints ---
@router.get("/tasks/{task_id}/comments", response_model=List[schemas.Comment])
def read_comments_for_task(task_id: int, db: Session = Depends(get_db)):
    """
    List all comments for a specific task.
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    comments = db.query(models.Comment).filter(models.Comment.task_id == task_id).all()
    return comments

@router.post("/tasks/{task_id}/comments", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED)
def create_comment(task_id: int, comment_create: schemas.CommentCreate, db: Session = Depends(get_db)):
    """
    Add a new comment to a specific task.
    """
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    db_comment = models.Comment(**comment_create.model_dump(), task_id=task_id, created_at=datetime.now())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

# --- Metrics Endpoints ---
@router.get("/projects/{project_id}/metrics", response_model=schemas.ProjectMetrics)
def get_project_metrics(project_id: int, db: Session = Depends(get_db)):
    """
    Calculate and retrieve completion metrics (e.g., average cycle time) for a project.
    """
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()

    total_tasks = len(tasks)
    completed_tasks = 0
    total_cycle_time = timedelta(0)
    cycle_time_count = 0

    for task in tasks:
        if task.closed_at and task.created_at:
            # Check if the task's status is a completion state
            status_obj = db.query(models.Status).filter(models.Status.id == task.status_id).first()
            if status_obj and status_obj.is_completion_state:
                completed_tasks += 1
                cycle_time = task.closed_at - task.created_at
                total_cycle_time += cycle_time
                cycle_time_count += 1

    avg_cycle_time_seconds = None
    if cycle_time_count > 0:
        avg_cycle_time_seconds = total_cycle_time.total_seconds() / cycle_time_count

    return schemas.ProjectMetrics(
        project_id=project_id,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        average_cycle_time_seconds=avg_cycle_time_seconds
    )

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)