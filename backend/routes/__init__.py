"""Routes aggregator."""
from fastapi import APIRouter

from .acceptance import router as acceptance_router
from .architecture import router as architecture_router
from .brd import router as brd_router
from .build import router as build_router
from .constraints import router as constraints_router
from .events import router as events_router
from .export import router as export_router
from .files import router as files_router
from .generate import router as generate_router
from .improve import router as improve_router
from .ingest import router as ingest_router
from .plan import router as plan_router
from .projects import router as projects_router
from .system import router as system_router

api = APIRouter(prefix="/api")
api.include_router(projects_router)
api.include_router(brd_router)
api.include_router(architecture_router)
api.include_router(plan_router)
api.include_router(generate_router)
api.include_router(files_router)
api.include_router(build_router)
api.include_router(acceptance_router)
api.include_router(export_router)
api.include_router(events_router)
api.include_router(system_router)
api.include_router(constraints_router)
api.include_router(improve_router)
api.include_router(ingest_router)
