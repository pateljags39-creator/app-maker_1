import os
from typing import List, Optional

from fastapi import FastAPI, APIRouter, Depends, HTTPException, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import uvicorn

from database import engine, Base, get_db
from models import Calculation as DB_Calculation
from schemas import CalculationCreate, CalculationResponse

# Initialize FastAPI app
app = FastAPI(
    title="Web Calculator Pro API",
    description="API for managing calculation history.",
    version="1.0.0",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Create database tables on startup
# This ensures that the database schema is created if it doesn't exist.
# For a simple application, this is sufficient. For production, consider migrations.
Base.metadata.create_all(bind=engine)

# API Router with a prefix for all API endpoints
api_router = APIRouter(prefix="/api")

@api_router.post("/calculations", response_model=CalculationResponse, status_code=status.HTTP_201_CREATED)
def create_calculation(
    calculation: CalculationCreate, db: Session = Depends(get_db)
):
    """
    Save a new calculation to the history.
    """
    db_calculation = DB_Calculation(**calculation.model_dump())
    db.add(db_calculation)
    db.commit()
    db.refresh(db_calculation)
    return db_calculation

@api_router.get("/calculations", response_model=List[CalculationResponse])
def get_calculations(
    session_ids: Optional[str] = Query(
        None,
        description="Comma-separated list of session IDs to filter calculations. "
                    "Example: 'id1,id2,id3'. If not provided, returns all calculations."
    ),
    db: Session = Depends(get_db)
):
    """
    Get calculation history for a list of session IDs.
    """
    query = db.query(DB_Calculation)
    if session_ids:
        # Split the comma-separated string into a list of session IDs
        session_id_list = [s.strip() for s in session_ids.split(',') if s.strip()]
        if session_id_list:
            query = query.filter(DB_Calculation.sessionId.in_(session_id_list))
    
    # Order by timestamp in descending order to show most recent first
    calculations = query.order_by(DB_Calculation.timestamp.desc()).all()
    return calculations

# Include the API router in the main app
app.include_router(api_router)

# Serve static files for the frontend
# This assumes the frontend build output is in a 'frontend/dist' directory
# relative to the project root where the backend is typically run from.
FRONTEND_DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

@app.get("/{full_path:path}", include_in_schema=False)
async def serve_frontend(full_path: str):
    """
    Serve static files from the frontend/dist directory.
    If a specific file is requested and exists, serve it.
    Otherwise, for Single Page Application (SPA) routing, fall back to index.html.
    """
    # Construct the full path to the requested file
    file_path = os.path.join(FRONTEND_DIST_DIR, full_path)

    # Check if the requested path is a file and exists
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # If not a specific file, or file not found, serve index.html for SPA routing
    index_path = os.path.join(FRONTEND_DIST_DIR, "index.html")
    if os.path.exists(index_path) and os.path.isfile(index_path):
        return FileResponse(index_path)
    
    # If index.html itself is not found, or other unhandled case
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

# Run the application with Uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)