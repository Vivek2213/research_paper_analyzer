from fastapi import APIRouter

from research_paper_analyser.api.ping import router as ping_router
from research_paper_analyser.api.routers.analyze.analyze import router as analyze_router

api_router = APIRouter()
api_router.include_router(ping_router)
api_router.include_router(analyze_router)
