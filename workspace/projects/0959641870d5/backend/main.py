import uvicorn
from fastapi import FastAPI, APIRouter
from starlette.middleware.cors import CORSMiddleware

from database import Base, engine

# Initialize FastAPI app
app = FastAPI(
    title="Simple Web Calculator Backend (Boilerplate)",
    description="This backend is a non-functional boilerplate as the application is client-side only.",
    version="0.0.1",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create database tables (even if models.py is empty, this ensures the db file is created)
Base.metadata.create_all(bind=engine)

# Create an API router (even if no endpoints are defined)
api_router = APIRouter(prefix="/api")

# Include the router in the main app
app.include_router(api_router)

# Root endpoint (optional, for basic health check)
@app.get("/")
async def root():
    return {"message": "Simple Web Calculator Backend (Boilerplate) is running."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)