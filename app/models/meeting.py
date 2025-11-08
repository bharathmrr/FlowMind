from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class MeetingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class MeetingType(str, enum.Enum):
    ONE_ON_ONE = "one_on_one"
    TEAM_MEETING = "team_meeting"
    CLIENT_CALL = "client_call"
    INTERVIEW = "interview"
    PRESENTATION = "presentation"
    STANDUP = "standup"
    RETROSPECTIVE = "retrospective"
    BRAINSTORMING = "brainstorming"

class ParticipantStatus(str, enum.Enum):
    INVITED = "invited"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"
    ATTENDED = "attended"
    NO_SHOW = "no_show"

class Meeting(Base):
    __tablename__ = "meetings"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic meeting information
    title = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    agenda = Column(Text, nullable=True)
    
    # Meeting details
    meeting_type = Column(Enum(MeetingType), default=MeetingType.TEAM_MEETING)
    status = Column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED, index=True)
    
    # Timing
    scheduled_start = Column(DateTime(timezone=True), nullable=False, index=True)
    scheduled_end = Column(DateTime(timezone=True), nullable=False, index=True)
    actual_start = Column(DateTime(timezone=True), nullable=True)
    actual_end = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String, default="UTC")
    
    # Meeting platform integration
    platform = Column(String, nullable=True)  # zoom, meet, teams, etc.
    meeting_url = Column(String, nullable=True)
    meeting_id = Column(String, nullable=True, index=True)
    meeting_password = Column(String, nullable=True)
    dial_in_number = Column(String, nullable=True)
    
    # Recording and transcription
    recording_enabled = Column(Boolean, default=False)
    recording_url = Column(String, nullable=True)
    transcription_enabled = Column(Boolean, default=True)
    transcription_text = Column(Text, nullable=True)
    
    # AI enhancements
    ai_summary = Column(Text, nullable=True)
    ai_action_items = Column(JSON, default=[])
    ai_key_decisions = Column(JSON, default=[])
    ai_sentiment_analysis = Column(JSON, nullable=True)
    ai_engagement_score = Column(Float, nullable=True)  # 0.0 to 1.0
    ai_follow_up_suggestions = Column(JSON, default=[])
    
    # Meeting preparation
    preparation_notes = Column(Text, nullable=True)
    required_documents = Column(JSON, default=[])
    pre_meeting_tasks = Column(JSON, default=[])
    
    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String, nullable=True)
    recurrence_group_id = Column(String, nullable=True, index=True)
    
    # Relationships
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    organizer = relationship("User", back_populates="meetings")
    workspace = relationship("Workspace", back_populates="meetings")
    participants = relationship("MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan")
    notes = relationship("MeetingNote", back_populates="meeting", cascade="all, delete-orphan")
    event = relationship("Event", back_populates="meeting", uselist=False)
    
    def __repr__(self):
        return f"<Meeting(id={self.id}, title='{self.title}', status='{self.status}')>"
    
    @property
    def duration_minutes(self):
        """Calculate actual or scheduled meeting duration"""
        if self.actual_start and self.actual_end:
            delta = self.actual_end - self.actual_start
            return int(delta.total_seconds() / 60)
        elif self.scheduled_start and self.scheduled_end:
            delta = self.scheduled_end - self.scheduled_start
            return int(delta.total_seconds() / 60)
        return 0

class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Participant information
    email = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    role = Column(String, nullable=True)  # organizer, presenter, attendee, optional
    
    # Participation status
    status = Column(Enum(ParticipantStatus), default=ParticipantStatus.INVITED, index=True)
    response_time = Column(DateTime(timezone=True), nullable=True)
    
    # Attendance tracking
    joined_at = Column(DateTime(timezone=True), nullable=True)
    left_at = Column(DateTime(timezone=True), nullable=True)
    attendance_duration = Column(Integer, nullable=True)  # minutes
    
    # AI insights
    engagement_score = Column(Float, nullable=True)  # 0.0 to 1.0
    speaking_time = Column(Integer, nullable=True)  # seconds
    questions_asked = Column(Integer, default=0)
    
    # Relationships
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User")
    
    def __repr__(self):
        return f"<MeetingParticipant(id={self.id}, email='{self.email}', status='{self.status}')>"

class MeetingNote(Base):
    __tablename__ = "meeting_notes"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Note content
    title = Column(String, nullable=True)
    content = Column(Text, nullable=False)
    note_type = Column(String, default="general")  # general, action_item, decision, question
    
    # Timing within meeting
    timestamp = Column(DateTime(timezone=True), nullable=True)  # When during meeting
    speaker = Column(String, nullable=True)  # Who said/did this
    
    # AI enhancements
    ai_generated = Column(Boolean, default=False)
    ai_confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    ai_tags = Column(JSON, default=[])
    
    # Organization
    is_action_item = Column(Boolean, default=False)
    is_decision = Column(Boolean, default=False)
    assigned_to = Column(String, nullable=True)  # Email of assignee
    due_date = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False, index=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    meeting = relationship("Meeting", back_populates="notes")
    author = relationship("User")
    
    def __repr__(self):
        return f"<MeetingNote(id={self.id}, type='{self.note_type}', meeting_id={self.meeting_id})>"
