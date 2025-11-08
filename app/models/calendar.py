from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class EventStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    RESCHEDULED = "rescheduled"

class EventType(str, enum.Enum):
    MEETING = "meeting"
    TASK = "task"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    BREAK = "break"
    FOCUS_TIME = "focus_time"
    PERSONAL = "personal"

class Calendar(Base):
    __tablename__ = "calendars"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String, default="#3B82F6")  # Hex color code
    
    # Calendar settings
    is_default = Column(Boolean, default=False)
    is_visible = Column(Boolean, default=True)
    timezone = Column(String, default="UTC")
    
    # External integration
    external_calendar_id = Column(String, nullable=True, index=True)
    integration_type = Column(String, nullable=True)  # google, outlook, etc.
    sync_enabled = Column(Boolean, default=False)
    last_sync = Column(DateTime(timezone=True), nullable=True)
    
    # Ownership
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    events = relationship("Event", back_populates="calendar", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Calendar(id={self.id}, name='{self.name}')>"

class Event(Base):
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic event information
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String, nullable=True)
    
    # Timing
    start_time = Column(DateTime(timezone=True), nullable=False, index=True)
    end_time = Column(DateTime(timezone=True), nullable=False, index=True)
    all_day = Column(Boolean, default=False)
    timezone = Column(String, default="UTC")
    
    # Event properties
    status = Column(Enum(EventStatus), default=EventStatus.SCHEDULED, index=True)
    event_type = Column(Enum(EventType), default=EventType.APPOINTMENT, index=True)
    priority = Column(String, default="medium")  # low, medium, high, urgent
    
    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_rule = Column(String, nullable=True)  # RRULE format
    recurrence_id = Column(String, nullable=True, index=True)  # Group recurring events
    
    # External integration
    external_event_id = Column(String, nullable=True, index=True)
    meeting_url = Column(String, nullable=True)
    meeting_id = Column(String, nullable=True)
    
    # AI enhancements
    ai_generated = Column(Boolean, default=False)
    ai_optimized_time = Column(Boolean, default=False)
    ai_conflict_resolution = Column(JSON, nullable=True)
    ai_preparation_suggestions = Column(JSON, default=[])
    
    # Notifications
    reminder_minutes = Column(JSON, default=[15, 5])  # Minutes before event
    notification_sent = Column(Boolean, default=False)
    
    # Attendees and collaboration
    attendees = Column(JSON, default=[])  # List of email addresses
    organizer_email = Column(String, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    calendar_id = Column(Integer, ForeignKey("calendars.id"), nullable=False, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True, index=True)
    meeting_id_rel = Column(Integer, ForeignKey("meetings.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="events")
    calendar = relationship("Calendar", back_populates="events")
    task = relationship("Task")
    meeting = relationship("Meeting", back_populates="event")
    
    def __repr__(self):
        return f"<Event(id={self.id}, title='{self.title}', start='{self.start_time}')>"
    
    @property
    def duration_minutes(self):
        """Calculate event duration in minutes"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0
