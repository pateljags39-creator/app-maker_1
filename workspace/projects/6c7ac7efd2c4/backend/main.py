import uvicorn
from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Absolute imports as per instructions
from database import engine, SessionLocal, Base
from models import PersistentCalculatorData
from schemas import CalculatorStateRead, CalculatorStateCreate

# Create database tables upon application startup if they don't exist
# This ensures the database schema is ready before handling requests.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Scientific Calculator Backend",
    description="FastAPI backend for persisting calculator state (memory and history).",
    version="1.0.0",
)

# Configure CORS middleware
# Allows requests from any origin ('*') for development purposes.
# In a production environment, this should be restricted to known frontend origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Dependency to get a database session
# This function creates a new SQLAlchemy session for each request and closes it afterwards.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create an API router with a prefix for all its routes
router = APIRouter(prefix="/api")

@router.get("/calculator-state", response_model=CalculatorStateRead)
def get_calculator_state(db: Session = Depends(get_db)):
    """
    Retrieve the current persisted calculator memory register and calculation history.
    Since we only manage a single global calculator state, we attempt to retrieve
    the record with ID 1. If no state exists, a default initial state is returned.
    """
    state = db.query(PersistentCalculatorData).filter(PersistentCalculatorData.id == 1).first()
    if not state:
        # If no record is found, return a default initial state as per BRD
        return CalculatorStateRead(
            id=1,  # Assume ID 1 for the single persistent state
            memory_register=0.0,
            history_log="[]"  # Represents an empty JSON array
        )
    return state

@router.post("/calculator-state", response_model=CalculatorStateRead)
def save_calculator_state(state_data: CalculatorStateCreate, db: Session = Depends(get_db)):
    """
    Save or update the current calculator memory register and calculation history.
    This endpoint performs an "upsert" operation: it updates an existing state
    (identified by ID 1) or creates a new one if it doesn't exist.
    """
    # Attempt to find the existing state record, assuming a single state with ID 1
    existing_state = db.query(PersistentCalculatorData).filter(PersistentCalculatorData.id == 1).first()

    if existing_state:
        # If the state exists, update its attributes
        existing_state.memory_register = state_data.memory_register
        existing_state.history_log = state_data.history_log
        db.add(existing_state) # Add is idempotent and handles updates
        db.commit()
        db.refresh(existing_state) # Refresh the instance to load any new data from the DB
        return existing_state
    else:
        # If no state exists, create a new one with ID 1
        new_state = PersistentCalculatorData(
            id=1,  # Explicitly set ID to 1 for the single global state
            memory_register=state_data.memory_register,
            history_log=state_data.history_log
        )
        db.add(new_state)
        db.commit()
        db.refresh(new_state) # Refresh the instance to load any new data from the DB
        return new_state

# Include the defined router in the main FastAPI application
app.include_router(router)

# Entry point for running the application with Uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)