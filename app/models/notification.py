from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class NotificationType(str, enum.Enum):
    TASK_DUE = "task_due"
    TASK_OVERDUE = "task_overdue"
    MEETING_REMINDER = "meeting_reminder"
    MEETING_STARTED = "meeting_started"
    AI_INSIGHT = "ai_insight"
    CALENDAR_CONFLICT = "calendar_conflict"
    WORKSPACE_INVITE = "workspace_invite"
    SYSTEM_UPDATE = "system_update"
    PRODUCTIVITY_REPORT = "productivity_report"

class NotificationChannel(str, enum.Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"

class NotificationPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Notification content
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    priority = Column(Enum(NotificationPriority), default=NotificationPriority.MEDIUM)
    
    # Delivery
    channels = Column(JSON, default=["in_app"])  # List of channels to send to
    scheduled_for = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_sent = Column(Boolean, default=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    data = Column(JSON, default={})  # Additional data for the notification
    action_url = Column(String, nullable=True)  # URL to navigate to when clicked
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    
    def __repr__(self):
        return f"<Notification(id={self.id}, type='{self.notification_type}', user_id={self.user_id})>"

class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Preference settings
    notification_type = Column(Enum(NotificationType), nullable=False, index=True)
    channels = Column(JSON, default=["in_app"])  # Enabled channels for this type
    is_enabled = Column(Boolean, default=True)
    
    # Timing preferences
    quiet_hours_start = Column(String, nullable=True)  # "22:00"
    quiet_hours_end = Column(String, nullable=True)    # "08:00"
    timezone = Column(String, default="UTC")
    
    # Frequency settings
    digest_frequency = Column(String, default="immediate")  # immediate, hourly, daily, weekly
    max_per_day = Column(Integer, nullable=True)  # Rate limiting
    
    # Advanced settings
    conditions = Column(JSON, default={})  # Conditional notification rules
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<NotificationPreference(user_id={self.user_id}, type='{self.notification_type}')>"
