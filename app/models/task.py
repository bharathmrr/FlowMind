from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ON_HOLD = "on_hold"

class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic task information
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    
    # Scheduling
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    start_date = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # in minutes
    actual_duration = Column(Integer, nullable=True)  # in minutes
    
    # Organization
    tags = Column(JSON, default=[])
    category = Column(String, nullable=True, index=True)
    project = Column(String, nullable=True, index=True)
    
    # AI-enhanced fields
    ai_generated = Column(Boolean, default=False)
    ai_priority_score = Column(Integer, nullable=True)  # 0-100
    ai_complexity_score = Column(Integer, nullable=True)  # 0-100
    ai_suggested_time_slot = Column(DateTime(timezone=True), nullable=True)
    ai_context = Column(JSON, default={})
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    page_id = Column(Integer, ForeignKey("pages.id"), nullable=True, index=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(JSON, nullable=True)  # cron-like pattern
    next_occurrence = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="tasks")
    workspace = relationship("Workspace", back_populates="tasks")
    page = relationship("Page", back_populates="tasks")
    parent_task = relationship("Task", remote_side=[id], backref="subtasks")
    dependencies = relationship("TaskDependency", foreign_keys="TaskDependency.task_id", back_populates="task")
    dependents = relationship("TaskDependency", foreign_keys="TaskDependency.depends_on_id", back_populates="depends_on")
    
    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"

class TaskDependency(Base):
    __tablename__ = "task_dependencies"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    depends_on_id = Column(Integer, ForeignKey("tasks.id"), nullable=False, index=True)
    dependency_type = Column(String, default="finish_to_start")  # finish_to_start, start_to_start, etc.
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    task = relationship("Task", foreign_keys=[task_id], back_populates="dependencies")
    depends_on = relationship("Task", foreign_keys=[depends_on_id], back_populates="dependents")
    
    def __repr__(self):
        return f"<TaskDependency(task_id={self.task_id}, depends_on_id={self.depends_on_id})>"

class TaskTemplate(Base):
    __tablename__ = "task_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)
    
    # Template fields
    default_priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    default_duration = Column(Integer, nullable=True)  # in minutes
    default_tags = Column(JSON, default=[])
    
    # AI template data
    ai_prompt_template = Column(Text, nullable=True)
    suggested_subtasks = Column(JSON, default=[])
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    is_public = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Usage statistics
    usage_count = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<TaskTemplate(id={self.id}, name='{self.name}')>"
