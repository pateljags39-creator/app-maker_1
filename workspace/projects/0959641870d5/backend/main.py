from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware
import uvicorn

# Absolute imports for database setup
from database import Base, engine

# Initialize FastAPI app
app = FastAPI(
    title="Simple Web Calculator Backend (Placeholder)",
    description="This is a placeholder backend for the Simple Web Calculator. All application logic is client-side.",
    version="0.0.1",
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Create database tables (even if no models are defined, this satisfies the structure)
# This will create the app.db file if it doesn't exist.
Base.metadata.create_all(bind=engine)

# Create an API router with a prefix
api_router = APIRouter(prefix="/api")

# Define a simple placeholder endpoint
@api_router.get("/status")
async def get_status():
    """
    Placeholder endpoint to confirm the backend is running.
    """
    return {"message": "Backend is running (placeholder, all logic is client-side)."}

# Include the API router in the main app
app.include_router(api_router)

# Main entry point for running the application with uvicorn
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)