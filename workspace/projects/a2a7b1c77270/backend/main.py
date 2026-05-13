import os
from datetime import datetime, timedelta
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, selectinload
from passlib.context import CryptContext
from jose import JWTError, jwt

# Absolute imports from project structure
from database import Base, engine, SessionLocal
import models
import schemas

# --- Configuration for JWT ---
# In a real application, these should be loaded from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-for-development-only")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

# --- Utility Functions for Authentication ---

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception
    return user

# --- FastAPI Application Setup ---

app = FastAPI(
    title="Team Todo App API",
    description="API for managing projects, tasks, and users in a collaborative environment.",
    version="1.0.0",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Database Initialization ---
@app.on_event("startup")
def on_startup():
    # Create all database tables
    Base.metadata.create_all(bind=engine)
    print("Database tables created or already exist.")

# --- API Router ---
api_router = APIRouter(prefix="/api")

# --- User Endpoints ---

@api_router.post("/users", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = models.User(email=user.email, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@api_router.post("/token", response_model=schemas.Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/users/me", response_model=schemas.User)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@api_router.get("/users", response_model=List[schemas.User])
def read_users(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    # Only allow listing users if authenticated
    users = db.query(models.User).all()
    return users

# --- Project Endpoints ---

@api_router.get("/projects", response_model=List[schemas.Project])
def read_projects(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    projects = db.query(models.Project).filter(models.Project.owner_id == current_user.id).all()
    return projects

@api_router.post("/projects", response_model=schemas.Project, status_code=status.HTTP_201_CREATED)
def create_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_project = models.Project(**project.model_dump(), owner_id=current_user.id)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)

    # Create default statuses for the new project
    default_status_names = [
        ("To Do", False),
        ("In Progress", False),
        ("Done", True)
    ]
    for name, is_completion in default_status_names:
        db_status = models.Status(
            project_id=db_project.id,
            name=name,
            is_completion_state=is_completion
        )
        db.add(db_status)
    db.commit()
    db.refresh(db_project) # Refresh again to load relationships if any were added by status creation

    return db_project

@api_router.get("/projects/{project_id}", response_model=schemas.Project)
def read_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    project = db.query(models.Project).options(
        selectinload(models.Project.tasks).selectinload(models.Task.assignee),
        selectinload(models.Project.tasks).selectinload(models.Task.status),
        selectinload(models.Project.statuses)
    ).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project

@api_router.put("/projects/{project_id}", response_model=schemas.Project)
def update_project(project_id: int, project_update: schemas.ProjectUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    for key, value in project_update.model_dump(exclude_unset=True).items():
        setattr(db_project, key, value)
    
    db.commit()
    db.refresh(db_project)
    return db_project

@api_router.delete("/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not db_project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    db.delete(db_project)
    db.commit()
    return {"ok": True}

# --- Task Endpoints ---

@api_router.post("/projects/{project_id}/tasks", response_model=schemas.Task, status_code=status.HTTP_201_CREATED)
def create_task_for_project(project_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    # Ensure the status_id belongs to this project
    status_obj = db.query(models.Status).filter(models.Status.id == task.status_id, models.Status.project_id == project_id).first()
    if not status_obj:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status not found or does not belong to this project")

    db_task = models.Task(**task.model_dump(), project_id=project_id, created_at=datetime.utcnow())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@api_router.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task(task_id: int, task_update: schemas.TaskUpdate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_task = db.query(models.Task).options(
        selectinload(models.Task.project)
    ).filter(models.Task.id == task_id).first()
    
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Check if the current user owns the project associated with the task
    if db_task.project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to update this task")

    # Handle status change and closed_at
    if task_update.status_id is not None and task_update.status_id != db_task.status_id:
        new_status = db.query(models.Status).filter(
            models.Status.id == task_update.status_id,
            models.Status.project_id == db_task.project_id
        ).first()
        if not new_status:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New status not found or does not belong to this project")
        
        if new_status.is_completion_state and db_task.closed_at is None:
            db_task.closed_at = datetime.utcnow()
        elif not new_status.is_completion_state and db_task.closed_at is not None:
            db_task.closed_at = None # Reopen task

    for key, value in task_update.model_dump(exclude_unset=True).items():
        setattr(db_task, key, value)
    
    db.commit()
    db.refresh(db_task)
    return db_task

@api_router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    db_task = db.query(models.Task).options(
        selectinload(models.Task.project)
    ).filter(models.Task.id == task_id).first()
    
    if not db_task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    if db_task.project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this task")
    
    db.delete(db_task)
    db.commit()
    return {"ok": True}

# --- Comment Endpoints ---

@api_router.post("/tasks/{task_id}/comments", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED)
def create_comment_for_task(task_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    task = db.query(models.Task).options(
        selectinload(models.Task.project)
    ).filter(models.Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Allow project owner or assignee to comment
    if task.project.owner_id != current_user.id and task.assignee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to comment on this task")

    db_comment = models.Comment(**comment.model_dump(), task_id=task_id, user_id=current_user.id, created_at=datetime.utcnow())
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

@api_router.get("/tasks/{task_id}/comments", response_model=List[schemas.Comment])
def read_comments_for_task(task_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    task = db.query(models.Task).options(
        selectinload(models.Task.project)
    ).filter(models.Task.id == task_id).first()
    
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    
    # Allow project owner or assignee to view comments
    if task.project.owner_id != current_user.id and task.assignee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to view comments for this task")

    comments = db.query(models.Comment).filter(models.Comment.task_id == task_id).all()
    return comments

# --- Status Endpoints (for project-specific statuses) ---
@api_router.get("/projects/{project_id}/statuses", response_model=List[schemas.Status])
def read_project_statuses(project_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    
    statuses = db.query(models