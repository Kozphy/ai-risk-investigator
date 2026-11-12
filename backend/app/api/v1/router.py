from fastapi import APIRouter

from app.api.v1 import analyses, auth, documents, knowledge, reports

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(documents.router)
api_router.include_router(knowledge.router)
api_router.include_router(analyses.router)
api_router.include_router(reports.router)
