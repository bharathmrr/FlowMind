from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class ProductivityMetric(Base):
    __tablename__ = "productivity_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Metric details
    metric_type = Column(String, nullable=False, index=True)  # tasks_completed, focus_time, etc.
    metric_name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=True)  # hours, count, percentage, etc.
    
    # Time period
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String, default="daily")  # hourly, daily, weekly, monthly
    
    # Context
    context = Column(JSON, default={})  # Additional context data
    tags = Column(JSON, default=[])
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="productivity_metrics")
    
    def __repr__(self):
        return f"<ProductivityMetric(id={self.id}, type='{self.metric_type}', value={self.value})>"

class FocusSession(Base):
    __tablename__ = "focus_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Session details
    session_type = Column(String, default="pomodoro")  # pomodoro, deep_work, break
    planned_duration = Column(Integer, nullable=False)  # minutes
    actual_duration = Column(Integer, nullable=True)  # minutes
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, index=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    
    # Session data
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    interruptions = Column(Integer, default=0)
    productivity_score = Column(Float, nullable=True)  # 0.0 to 1.0
    
    # AI insights
    ai_analysis = Column(JSON, default={})
    mood_before = Column(String, nullable=True)  # energetic, focused, tired, etc.
    mood_after = Column(String, nullable=True)
    
    # Environment
    location = Column(String, nullable=True)
    ambient_noise = Column(String, nullable=True)
    distractions = Column(JSON, default=[])
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="focus_sessions")
    task = relationship("Task")
    
    def __repr__(self):
        return f"<FocusSession(id={self.id}, type='{self.session_type}', duration={self.actual_duration})>"

class HabitTracker(Base):
    __tablename__ = "habit_trackers"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Habit details
    habit_name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(String, nullable=True, index=True)  # productivity, health, learning, etc.
    
    # Tracking
    target_frequency = Column(String, default="daily")  # daily, weekly, monthly
    target_value = Column(Float, default=1.0)  # How much/many times
    unit = Column(String, nullable=True)  # times, minutes, pages, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    streak_count = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    
    # AI insights
    ai_recommendations = Column(JSON, default=[])
    success_patterns = Column(JSON, default={})
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    entries = relationship("HabitEntry", back_populates="habit", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<HabitTracker(id={self.id}, name='{self.habit_name}', streak={self.streak_count})>"

class HabitEntry(Base):
    __tablename__ = "habit_entries"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Entry details
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    value = Column(Float, nullable=False)  # Actual value achieved
    completed = Column(Boolean, default=False)
    
    # Context
    notes = Column(Text, nullable=True)
    mood = Column(String, nullable=True)
    context = Column(JSON, default={})
    
    # Relationships
    habit_id = Column(Integer, ForeignKey("habit_trackers.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    habit = relationship("HabitTracker", back_populates="entries")
    
    def __repr__(self):
        return f"<HabitEntry(id={self.id}, habit_id={self.habit_id}, value={self.value})>"
