from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    tasks,
    calendar,
    meetings,
    ai_assistant,
    notifications,
    workspaces,
    analytics,
    integrations
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(calendar.router, prefix="/calendar", tags=["calendar"])
api_router.include_router(meetings.router, prefix="/meetings", tags=["meetings"])
api_router.include_router(ai_assistant.router, prefix="/ai", tags=["ai-assistant"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(workspaces.router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
