from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Profile information
    avatar_url = Column(String, nullable=True)
    timezone = Column(String, default="UTC")
    language = Column(String, default="en")
    theme = Column(String, default="light")
    
    # Account status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_premium = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True), nullable=True)
    
    # AI Preferences
    ai_preferences = Column(JSON, default={
        "personality": "professional",
        "communication_style": "concise",
        "proactivity_level": "medium",
        "focus_mode_enabled": True,
        "auto_scheduling": True,
        "smart_notifications": True
    })
    
    # Productivity Settings
    productivity_settings = Column(JSON, default={
        "work_hours_start": "09:00",
        "work_hours_end": "17:00",
        "break_duration": 15,
        "focus_session_duration": 25,
        "deep_work_blocks": 2,
        "meeting_buffer": 5
    })
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    meetings = relationship("Meeting", back_populates="organizer")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    workspaces = relationship("WorkspaceMember", back_populates="user")
    ai_contexts = relationship("AIContext", back_populates="user", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="user", cascade="all, delete-orphan")
    productivity_metrics = relationship("ProductivityMetric", back_populates="user", cascade="all, delete-orphan")
    focus_sessions = relationship("FocusSession", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"
