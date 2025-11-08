from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class IntegrationType(str, enum.Enum):
    GOOGLE_CALENDAR = "google_calendar"
    GOOGLE_MEET = "google_meet"
    OUTLOOK_CALENDAR = "outlook_calendar"
    MICROSOFT_TEAMS = "microsoft_teams"
    ZOOM = "zoom"
    SLACK = "slack"
    NOTION = "notion"
    TRELLO = "trello"
    ASANA = "asana"
    GITHUB = "github"
    ZAPIER = "zapier"

class IntegrationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    PENDING = "pending"
    EXPIRED = "expired"

class Integration(Base):
    __tablename__ = "integrations"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Integration details
    integration_type = Column(Enum(IntegrationType), nullable=False, index=True)
    name = Column(String, nullable=False)  # User-friendly name
    description = Column(Text, nullable=True)
    
    # Status
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.PENDING, index=True)
    is_enabled = Column(Boolean, default=True)
    
    # Authentication
    access_token = Column(Text, nullable=True)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Configuration
    config = Column(JSON, default={})
    sync_settings = Column(JSON, default={
        "auto_sync": True,
        "sync_interval": 300,  # seconds
        "sync_direction": "bidirectional"  # import, export, bidirectional
    })
    
    # Sync status
    last_sync = Column(DateTime(timezone=True), nullable=True)
    next_sync = Column(DateTime(timezone=True), nullable=True)
    sync_errors = Column(JSON, default=[])
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="integrations")
    configs = relationship("IntegrationConfig", back_populates="integration", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Integration(id={self.id}, type='{self.integration_type}', status='{self.status}')>"

class IntegrationConfig(Base):
    __tablename__ = "integration_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Configuration details
    config_key = Column(String, nullable=False, index=True)
    config_value = Column(Text, nullable=True)
    config_type = Column(String, default="string")  # string, number, boolean, json
    
    # Metadata
    is_sensitive = Column(Boolean, default=False)  # Should be encrypted
    is_required = Column(Boolean, default=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    integration_id = Column(Integer, ForeignKey("integrations.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    integration = relationship("Integration", back_populates="configs")
    
    def __repr__(self):
        return f"<IntegrationConfig(integration_id={self.integration_id}, key='{self.config_key}')>"
