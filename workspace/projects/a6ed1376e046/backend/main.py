from typing import List, Generator
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from database import engine, Base, SessionLocal
import models
import schemas

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Web Calculator Pro API",
    description="API for saving and retrieving calculation history.",
    version="1.0.0",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# API Router for versioning and prefixing
router = APIRouter(prefix="/api")

# Dependency to get the database session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/calculations", response_model=schemas.CalculationRead, status_code=status.HTTP_201_CREATED)
def create_calculation(
    calculation: schemas.CalculationCreate, db: Session = Depends(get_db)
):
    """
    Save a new calculation to the history.
    """
    db_calculation = models.Calculation(
        session_id=calculation.session_id,
        expression=calculation.expression,
        result=calculation.result,
        timestamp=datetime.now()
    )
    db.add(db_calculation)
    db.commit()
    db.refresh(db_calculation)
    return db_calculation

@router.get("/calculations/history", response_model=List[schemas.CalculationRead])
def get_calculation_history(db: Session = Depends(get_db)):
    """
    Get the calculation history for the last 3 user sessions.
    A 'session' is identified by a unique `session_id`.
    The 'last 3 sessions' are determined by the most recent activity (timestamp) within each session.
    """
    # Subquery to find the latest timestamp for each unique session_id
    latest_session_activity_subquery = (
        select(
            models.Calculation.session_id,
            func.max(models.Calculation.timestamp).label("last_activity")
        )
        .group_by(models.Calculation.session_id)
        .order_by(func.max(models.Calculation.timestamp).desc())
        .limit(3)
        .subquery()
    )

    # Select the actual session_ids from the subquery
    session_ids_to_fetch_query = select(latest_session_activity_subquery.c.session_id)
    session_ids_to_fetch = db.execute(session_ids_to_fetch_query).scalars().all()

    if not session_ids_to_fetch:
        return []

    # Fetch all calculations belonging to these top 3 session_ids
    history = (
        db.query(models.Calculation)
        .filter(models.Calculation.session_id.in_(session_ids_to_fetch))
        .order_by(models.Calculation.timestamp.asc()) # Order by timestamp for chronological display within history
        .all()
    )
    return history

app.include_router(router)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)