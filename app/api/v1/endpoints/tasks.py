from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.models.task import Task, TaskStatus, TaskPriority, TaskDependency
from app.models.user import User
from app.schemas.task import (
    TaskCreate, 
    TaskUpdate, 
    TaskResponse, 
    TaskListResponse,
    NaturalLanguageTaskCreate
)
from app.services.ai.grok_service import grok_service
from app.core.auth import get_current_user
from app.services.task_service import TaskService

logger = structlog.get_logger()
router = APIRouter()

@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new task"""
    try:
        task_service = TaskService(db)
        task = await task_service.create_task(task_data, current_user.id)
        
        # Schedule AI optimization in background
        background_tasks.add_task(
            task_service.optimize_task_scheduling,
            task.id,
            current_user.id
        )
        
        logger.info("Task created", task_id=task.id, user_id=current_user.id)
        return task
        
    except Exception as e:
        logger.error("Failed to create task", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to create task")

@router.post("/natural-language", response_model=TaskResponse)
async def create_task_from_natural_language(
    task_input: NaturalLanguageTaskCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create task from natural language input using AI"""
    try:
        # Get user context for better parsing
        user_context = {
            "timezone": current_user.timezone,
            "productivity_settings": current_user.productivity_settings,
            "ai_preferences": current_user.ai_preferences
        }
        
        # Parse natural language using Grok
        parsed_data = await grok_service.parse_natural_language_task(
            task_input.input_text,
            current_user.id,
            user_context
        )
        
        # Create task from parsed data
        task_data = TaskCreate(
            title=parsed_data.get("title", task_input.input_text[:100]),
            description=parsed_data.get("description"),
            priority=TaskPriority(parsed_data.get("priority", "medium")),
            due_date=parsed_data.get("due_date"),
            estimated_duration=parsed_data.get("estimated_duration"),
            tags=parsed_data.get("tags", []),
            ai_generated=True,
            ai_context=parsed_data
        )
        
        task_service = TaskService(db)
        task = await task_service.create_task(task_data, current_user.id)
        
        # Create subtasks if suggested
        if parsed_data.get("subtasks"):
            background_tasks.add_task(
                task_service.create_subtasks,
                task.id,
                parsed_data["subtasks"],
                current_user.id
            )
        
        logger.info(
            "Task created from natural language", 
            task_id=task.id, 
            user_id=current_user.id,
            original_input=task_input.input_text
        )
        return task
        
    except Exception as e:
        logger.error("Failed to create task from NL", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to parse and create task")

@router.get("/", response_model=TaskListResponse)
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TaskStatus] = None,
    priority: Optional[TaskPriority] = None,
    category: Optional[str] = None,
    project: Optional[str] = None,
    due_soon: bool = Query(False, description="Tasks due in next 7 days"),
    overdue: bool = Query(False, description="Overdue tasks"),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's tasks with filtering and pagination"""
    try:
        task_service = TaskService(db)
        
        filters = {
            "status": status,
            "priority": priority,
            "category": category,
            "project": project,
            "due_soon": due_soon,
            "overdue": overdue,
            "search": search
        }
        
        tasks, total = await task_service.get_user_tasks(
            current_user.id,
            skip=skip,
            limit=limit,
            filters=filters
        )
        
        return TaskListResponse(
            tasks=tasks,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        logger.error("Failed to get tasks", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")

@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get specific task by ID"""
    try:
        task_service = TaskService(db)
        task = await task_service.get_task(task_id, current_user.id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get task", error=str(e), task_id=task_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve task")

@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: int,
    task_update: TaskUpdate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update task"""
    try:
        task_service = TaskService(db)
        task = await task_service.update_task(task_id, task_update, current_user.id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Re-optimize schedule if task timing changed
        if task_update.due_date or task_update.estimated_duration:
            background_tasks.add_task(
                task_service.optimize_task_scheduling,
                task.id,
                current_user.id
            )
        
        logger.info("Task updated", task_id=task_id, user_id=current_user.id)
        return task
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update task", error=str(e), task_id=task_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to update task")

@router.delete("/{task_id}")
async def delete_task(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete task"""
    try:
        task_service = TaskService(db)
        success = await task_service.delete_task(task_id, current_user.id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Task not found")
        
        logger.info("Task deleted", task_id=task_id, user_id=current_user.id)
        return {"message": "Task deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete task", error=str(e), task_id=task_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to delete task")

@router.post("/{task_id}/complete")
async def complete_task(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Mark task as completed"""
    try:
        task_service = TaskService(db)
        task = await task_service.complete_task(task_id, current_user.id)
        
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Update productivity metrics in background
        background_tasks.add_task(
            task_service.update_productivity_metrics,
            current_user.id,
            task.id
        )
        
        logger.info("Task completed", task_id=task_id, user_id=current_user.id)
        return {"message": "Task completed successfully", "task": task}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to complete task", error=str(e), task_id=task_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to complete task")

@router.get("/{task_id}/dependencies")
async def get_task_dependencies(
    task_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task dependencies"""
    try:
        task_service = TaskService(db)
        dependencies = await task_service.get_task_dependencies(task_id, current_user.id)
        
        return {"dependencies": dependencies}
        
    except Exception as e:
        logger.error("Failed to get dependencies", error=str(e), task_id=task_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve dependencies")

@router.post("/{task_id}/dependencies/{depends_on_id}")
async def add_task_dependency(
    task_id: int,
    depends_on_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add task dependency"""
    try:
        task_service = TaskService(db)
        dependency = await task_service.add_task_dependency(
            task_id, 
            depends_on_id, 
            current_user.id
        )
        
        if not dependency:
            raise HTTPException(status_code=400, detail="Cannot create dependency")
        
        logger.info("Dependency added", task_id=task_id, depends_on_id=depends_on_id, user_id=current_user.id)
        return {"message": "Dependency added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to add dependency", error=str(e), task_id=task_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to add dependency")

@router.post("/{task_id}/ai-optimize")
async def optimize_task_with_ai(
    task_id: int,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimize task scheduling and priority using AI"""
    try:
        task_service = TaskService(db)
        
        # Run optimization in background
        background_tasks.add_task(
            task_service.ai_optimize_task,
            task_id,
            current_user.id
        )
        
        return {"message": "AI optimization started", "task_id": task_id}
        
    except Exception as e:
        logger.error("Failed to start AI optimization", error=str(e), task_id=task_id, user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to start optimization")

@router.get("/analytics/productivity")
async def get_task_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get task productivity analytics"""
    try:
        task_service = TaskService(db)
        analytics = await task_service.get_productivity_analytics(current_user.id, days)
        
        return analytics
        
    except Exception as e:
        logger.error("Failed to get analytics", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to retrieve analytics")
