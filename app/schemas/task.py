from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_duration: Optional[int] = Field(None, ge=1, le=1440)  # 1 minute to 24 hours
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=100)
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.strip().lower() for tag in v if tag.strip()]

class TaskCreate(TaskBase):
    workspace_id: Optional[int] = None
    page_id: Optional[int] = None
    parent_task_id: Optional[int] = None
    is_recurring: bool = False
    recurrence_pattern: Optional[Dict[str, Any]] = None
    ai_generated: bool = False
    ai_context: Optional[Dict[str, Any]] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    due_date: Optional[datetime] = None
    start_date: Optional[datetime] = None
    estimated_duration: Optional[int] = Field(None, ge=1, le=1440)
    actual_duration: Optional[int] = Field(None, ge=1)
    tags: Optional[List[str]] = None
    category: Optional[str] = Field(None, max_length=100)
    project: Optional[str] = Field(None, max_length=100)
    
    @validator('tags')
    def validate_tags(cls, v):
        if v is not None and len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.strip().lower() for tag in v if tag.strip()] if v else v

class TaskResponse(TaskBase):
    id: int
    uuid: str
    status: TaskStatus
    user_id: int
    workspace_id: Optional[int]
    page_id: Optional[int]
    parent_task_id: Optional[int]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # AI fields
    ai_generated: bool
    ai_priority_score: Optional[int]
    ai_complexity_score: Optional[int]
    ai_suggested_time_slot: Optional[datetime]
    ai_context: Optional[Dict[str, Any]]
    
    # Recurrence
    is_recurring: bool
    recurrence_pattern: Optional[Dict[str, Any]]
    next_occurrence: Optional[datetime]
    
    # Computed fields
    is_overdue: bool = False
    is_due_soon: bool = False
    subtask_count: int = 0
    completion_percentage: float = 0.0
    
    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    tasks: List[TaskResponse]
    total: int
    skip: int
    limit: int
    
    class Config:
        from_attributes = True

class NaturalLanguageTaskCreate(BaseModel):
    input_text: str = Field(..., min_length=1, max_length=1000)
    context: Optional[Dict[str, Any]] = None

class TaskDependencyResponse(BaseModel):
    id: int
    task_id: int
    depends_on_id: int
    dependency_type: str
    created_at: datetime
    
    class Config:
        from_attributes = True

class TaskTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Optional[str] = Field(None, max_length=100)
    default_priority: TaskPriority = TaskPriority.MEDIUM
    default_duration: Optional[int] = Field(None, ge=1, le=1440)
    default_tags: List[str] = Field(default_factory=list)
    suggested_subtasks: List[str] = Field(default_factory=list)
    is_public: bool = False

class TaskTemplateResponse(TaskTemplateCreate):
    id: int
    uuid: str
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True

class TaskAnalytics(BaseModel):
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    completion_rate: float
    average_completion_time: Optional[float]  # hours
    productivity_score: float  # 0-100
    most_productive_hours: List[int]
    task_distribution_by_priority: Dict[str, int]
    task_distribution_by_category: Dict[str, int]
    weekly_completion_trend: List[Dict[str, Any]]
    
class TaskBulkOperation(BaseModel):
    task_ids: List[int] = Field(..., min_items=1, max_items=100)
    operation: str = Field(..., regex="^(complete|delete|update_priority|update_category|add_tags)$")
    parameters: Optional[Dict[str, Any]] = None

class TaskBulkResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: List[str] = Field(default_factory=list)
    updated_tasks: List[int] = Field(default_factory=list)
