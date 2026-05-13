"""Local App Creator - orchestrator entrypoint (FastAPI)."""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# Init logging early.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
)

from db import close_client, ensure_indexes, init_client  # noqa: E402
from routes import api  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_client()
    await ensure_indexes()
    Path(os.environ.get("WORKSPACE_DIR", "/app/workspace")).mkdir(parents=True, exist_ok=True)
    yield
    # Shutdown
    await close_client()


app = FastAPI(title="Local App Creator", version="0.2.0", lifespan=lifespan)

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"service": "Local App Creator", "version": "0.2.0", "api_prefix": "/api"}
