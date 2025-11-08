from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
import structlog

from app.models.task import Task, TaskStatus, TaskPriority, TaskDependency, TaskTemplate
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.ai.grok_service import grok_service

logger = structlog.get_logger()

class TaskService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_task(self, task_data: TaskCreate, user_id: int) -> TaskResponse:
        """Create a new task"""
        
        # Create task instance
        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            due_date=task_data.due_date,
            start_date=task_data.start_date,
            estimated_duration=task_data.estimated_duration,
            tags=task_data.tags,
            category=task_data.category,
            project=task_data.project,
            user_id=user_id,
            workspace_id=task_data.workspace_id,
            page_id=task_data.page_id,
            parent_task_id=task_data.parent_task_id,
            is_recurring=task_data.is_recurring,
            recurrence_pattern=task_data.recurrence_pattern,
            ai_generated=task_data.ai_generated,
            ai_context=task_data.ai_context or {}
        )
        
        # Calculate AI scores if not provided
        if task_data.ai_generated:
            task.ai_priority_score = await self._calculate_ai_priority_score(task)
            task.ai_complexity_score = await self._calculate_ai_complexity_score(task)
        
        self.db.add(task)
        await self.db.commit()
        await self.db.refresh(task)
        
        return await self._task_to_response(task)
    
    async def get_task(self, task_id: int, user_id: int) -> Optional[TaskResponse]:
        """Get task by ID"""
        
        query = select(Task).where(
            and_(Task.id == task_id, Task.user_id == user_id)
        ).options(selectinload(Task.subtasks))
        
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        return await self._task_to_response(task)
    
    async def get_user_tasks(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[TaskResponse], int]:
        """Get user's tasks with filtering"""
        
        # Base query
        query = select(Task).where(Task.user_id == user_id)
        count_query = select(func.count(Task.id)).where(Task.user_id == user_id)
        
        # Apply filters
        if filters:
            conditions = []
            
            if filters.get("status"):
                conditions.append(Task.status == filters["status"])
            
            if filters.get("priority"):
                conditions.append(Task.priority == filters["priority"])
            
            if filters.get("category"):
                conditions.append(Task.category == filters["category"])
            
            if filters.get("project"):
                conditions.append(Task.project == filters["project"])
            
            if filters.get("due_soon"):
                week_from_now = datetime.utcnow() + timedelta(days=7)
                conditions.append(
                    and_(
                        Task.due_date.isnot(None),
                        Task.due_date <= week_from_now,
                        Task.status != TaskStatus.COMPLETED
                    )
                )
            
            if filters.get("overdue"):
                now = datetime.utcnow()
                conditions.append(
                    and_(
                        Task.due_date.isnot(None),
                        Task.due_date < now,
                        Task.status != TaskStatus.COMPLETED
                    )
                )
            
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                conditions.append(
                    or_(
                        Task.title.ilike(search_term),
                        Task.description.ilike(search_term)
                    )
                )
            
            if conditions:
                query = query.where(and_(*conditions))
                count_query = count_query.where(and_(*conditions))
        
        # Apply ordering
        query = query.order_by(
            desc(Task.priority == TaskPriority.URGENT),
            desc(Task.priority == TaskPriority.HIGH),
            asc(Task.due_date),
            desc(Task.created_at)
        )
        
        # Apply pagination
        query = query.offset(skip).limit(limit)
        
        # Execute queries
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        # Convert to response objects
        task_responses = []
        for task in tasks:
            task_response = await self._task_to_response(task)
            task_responses.append(task_response)
        
        return task_responses, total
    
    async def update_task(
        self, 
        task_id: int, 
        task_update: TaskUpdate, 
        user_id: int
    ) -> Optional[TaskResponse]:
        """Update task"""
        
        query = select(Task).where(
            and_(Task.id == task_id, Task.user_id == user_id)
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            return None
        
        # Update fields
        update_data = task_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)
        
        # Update completion timestamp
        if task_update.status == TaskStatus.COMPLETED and not task.completed_at:
            task.completed_at = datetime.utcnow()
        elif task_update.status != TaskStatus.COMPLETED:
            task.completed_at = None
        
        task.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(task)
        
        return await self._task_to_response(task)
    
    async def delete_task(self, task_id: int, user_id: int) -> bool:
        """Delete task"""
        
        query = select(Task).where(
            and_(Task.id == task_id, Task.user_id == user_id)
        )
        result = await self.db.execute(query)
        task = result.scalar_one_or_none()
        
        if not task:
            return False
        
        await self.db.delete(task)
        await self.db.commit()
        
        return True
    
    async def complete_task(self, task_id: int, user_id: int) -> Optional[TaskResponse]:
        """Mark task as completed"""
        
        task_update = TaskUpdate(
            status=TaskStatus.COMPLETED,
            completed_at=datetime.utcnow()
        )
        
        return await self.update_task(task_id, task_update, user_id)
    
    async def get_task_dependencies(self, task_id: int, user_id: int) -> List[Dict]:
        """Get task dependencies"""
        
        # Verify task ownership
        task_query = select(Task).where(
            and_(Task.id == task_id, Task.user_id == user_id)
        )
        task_result = await self.db.execute(task_query)
        if not task_result.scalar_one_or_none():
            return []
        
        # Get dependencies
        query = select(TaskDependency).where(
            TaskDependency.task_id == task_id
        ).options(selectinload(TaskDependency.depends_on))
        
        result = await self.db.execute(query)
        dependencies = result.scalars().all()
        
        return [
            {
                "id": dep.id,
                "depends_on_task": {
                    "id": dep.depends_on.id,
                    "title": dep.depends_on.title,
                    "status": dep.depends_on.status
                },
                "dependency_type": dep.dependency_type
            }
            for dep in dependencies
        ]
    
    async def add_task_dependency(
        self, 
        task_id: int, 
        depends_on_id: int, 
        user_id: int
    ) -> Optional[TaskDependency]:
        """Add task dependency"""
        
        # Verify both tasks belong to user
        tasks_query = select(Task).where(
            and_(
                Task.id.in_([task_id, depends_on_id]),
                Task.user_id == user_id
            )
        )
        result = await self.db.execute(tasks_query)
        tasks = result.scalars().all()
        
        if len(tasks) != 2:
            return None
        
        # Check for circular dependency
        if await self._would_create_circular_dependency(task_id, depends_on_id):
            return None
        
        # Create dependency
        dependency = TaskDependency(
            task_id=task_id,
            depends_on_id=depends_on_id
        )
        
        self.db.add(dependency)
        await self.db.commit()
        await self.db.refresh(dependency)
        
        return dependency
    
    async def create_subtasks(
        self, 
        parent_task_id: int, 
        subtask_titles: List[str], 
        user_id: int
    ):
        """Create subtasks for a parent task"""
        
        for title in subtask_titles:
            subtask_data = TaskCreate(
                title=title,
                parent_task_id=parent_task_id,
                priority=TaskPriority.MEDIUM,
                ai_generated=True
            )
            await self.create_task(subtask_data, user_id)
    
    async def optimize_task_scheduling(self, task_id: int, user_id: int):
        """Optimize task scheduling using AI"""
        
        try:
            # Get task and user context
            task = await self.get_task(task_id, user_id)
            if not task:
                return
            
            # Get user's other tasks and events for context
            user_tasks, _ = await self.get_user_tasks(user_id, limit=50)
            
            # Use Grok to optimize scheduling
            optimization_data = await grok_service.generate_schedule_optimization(
                user_id=user_id,
                tasks=[task.dict()],
                events=[],  # Would get from calendar service
                preferences={}  # Would get from user preferences
            )
            
            # Apply optimization suggestions
            if optimization_data.get("suggested_time_slot"):
                await self.update_task(
                    task_id,
                    TaskUpdate(ai_suggested_time_slot=optimization_data["suggested_time_slot"]),
                    user_id
                )
            
            logger.info("Task scheduling optimized", task_id=task_id, user_id=user_id)
            
        except Exception as e:
            logger.error("Task optimization failed", error=str(e), task_id=task_id)
    
    async def ai_optimize_task(self, task_id: int, user_id: int):
        """AI-powered task optimization"""
        
        # This would implement comprehensive AI optimization
        # including priority adjustment, time estimation, etc.
        await self.optimize_task_scheduling(task_id, user_id)
    
    async def update_productivity_metrics(self, user_id: int, task_id: int):
        """Update productivity metrics after task completion"""
        
        # This would update productivity analytics
        # Implementation would depend on analytics models
        logger.info("Productivity metrics updated", user_id=user_id, task_id=task_id)
    
    async def get_productivity_analytics(self, user_id: int, days: int) -> Dict[str, Any]:
        """Get productivity analytics for user"""
        
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get tasks in date range
        query = select(Task).where(
            and_(
                Task.user_id == user_id,
                Task.created_at >= start_date
            )
        )
        result = await self.db.execute(query)
        tasks = result.scalars().all()
        
        # Calculate metrics
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == TaskStatus.COMPLETED])
        overdue_tasks = len([
            t for t in tasks 
            if t.due_date and t.due_date < datetime.utcnow() and t.status != TaskStatus.COMPLETED
        ])
        
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return {
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": total_tasks - completed_tasks,
            "overdue_tasks": overdue_tasks,
            "completion_rate": completion_rate,
            "productivity_score": min(completion_rate, 100),
            "period_days": days
        }
    
    async def _task_to_response(self, task: Task) -> TaskResponse:
        """Convert task model to response schema"""
        
        # Calculate computed fields
        now = datetime.utcnow()
        is_overdue = (
            task.due_date is not None and 
            task.due_date < now and 
            task.status != TaskStatus.COMPLETED
        )
        is_due_soon = (
            task.due_date is not None and 
            task.due_date <= now + timedelta(days=3) and
            task.status != TaskStatus.COMPLETED
        )
        
        # Get subtask count
        subtask_count_query = select(func.count(Task.id)).where(
            Task.parent_task_id == task.id
        )
        subtask_result = await self.db.execute(subtask_count_query)
        subtask_count = subtask_result.scalar() or 0
        
        return TaskResponse(
            id=task.id,
            uuid=task.uuid,
            title=task.title,
            description=task.description,
            status=task.status,
            priority=task.priority,
            due_date=task.due_date,
            start_date=task.start_date,
            estimated_duration=task.estimated_duration,
            tags=task.tags,
            category=task.category,
            project=task.project,
            user_id=task.user_id,
            workspace_id=task.workspace_id,
            page_id=task.page_id,
            parent_task_id=task.parent_task_id,
            created_at=task.created_at,
            updated_at=task.updated_at,
            completed_at=task.completed_at,
            ai_generated=task.ai_generated,
            ai_priority_score=task.ai_priority_score,
            ai_complexity_score=task.ai_complexity_score,
            ai_suggested_time_slot=task.ai_suggested_time_slot,
            ai_context=task.ai_context,
            is_recurring=task.is_recurring,
            recurrence_pattern=task.recurrence_pattern,
            next_occurrence=task.next_occurrence,
            is_overdue=is_overdue,
            is_due_soon=is_due_soon,
            subtask_count=subtask_count,
            completion_percentage=100.0 if task.status == TaskStatus.COMPLETED else 0.0
        )
    
    async def _calculate_ai_priority_score(self, task: Task) -> int:
        """Calculate AI priority score (0-100)"""
        
        score = 50  # Base score
        
        # Adjust based on priority
        priority_scores = {
            TaskPriority.LOW: 25,
            TaskPriority.MEDIUM: 50,
            TaskPriority.HIGH: 75,
            TaskPriority.URGENT: 95
        }
        score = priority_scores.get(task.priority, 50)
        
        # Adjust based on due date
        if task.due_date:
            days_until_due = (task.due_date - datetime.utcnow()).days
            if days_until_due <= 1:
                score += 20
            elif days_until_due <= 3:
                score += 10
            elif days_until_due <= 7:
                score += 5
        
        return min(max(score, 0), 100)
    
    async def _calculate_ai_complexity_score(self, task: Task) -> int:
        """Calculate AI complexity score (0-100)"""
        
        score = 30  # Base score
        
        # Adjust based on estimated duration
        if task.estimated_duration:
            if task.estimated_duration > 240:  # > 4 hours
                score += 40
            elif task.estimated_duration > 120:  # > 2 hours
                score += 25
            elif task.estimated_duration > 60:  # > 1 hour
                score += 15
        
        # Adjust based on description length
        if task.description:
            if len(task.description) > 500:
                score += 20
            elif len(task.description) > 200:
                score += 10
        
        return min(max(score, 0), 100)
    
    async def _would_create_circular_dependency(
        self, 
        task_id: int, 
        depends_on_id: int
    ) -> bool:
        """Check if adding dependency would create circular reference"""
        
        # Simple implementation - check direct reverse dependency
        reverse_query = select(TaskDependency).where(
            and_(
                TaskDependency.task_id == depends_on_id,
                TaskDependency.depends_on_id == task_id
            )
        )
        result = await self.db.execute(reverse_query)
        return result.scalar_one_or_none() is not None
