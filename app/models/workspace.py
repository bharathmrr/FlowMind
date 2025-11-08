from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class WorkspaceRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class PageType(str, enum.Enum):
    DOCUMENT = "document"
    KANBAN = "kanban"
    CALENDAR = "calendar"
    DATABASE = "database"
    DASHBOARD = "dashboard"

class Workspace(Base):
    __tablename__ = "workspaces"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String, nullable=True)
    color = Column(String, default="#3B82F6")
    
    # Settings
    is_public = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    settings = Column(JSON, default={
        "allow_guests": False,
        "default_permissions": "member",
        "ai_enabled": True,
        "integrations_enabled": True
    })
    
    # AI features
    ai_assistant_enabled = Column(Boolean, default=True)
    ai_context = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    members = relationship("WorkspaceMember", back_populates="workspace", cascade="all, delete-orphan")
    pages = relationship("Page", back_populates="workspace", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="workspace")
    meetings = relationship("Meeting", back_populates="workspace")
    
    def __repr__(self):
        return f"<Workspace(id={self.id}, name='{self.name}')>"

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Member information
    role = Column(Enum(WorkspaceRole), default=WorkspaceRole.MEMBER, index=True)
    permissions = Column(JSON, default={
        "can_edit": True,
        "can_delete": False,
        "can_invite": False,
        "can_manage_settings": False
    })
    
    # Status
    is_active = Column(Boolean, default=True)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    last_active = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="workspaces")
    workspace = relationship("Workspace", back_populates="members")
    
    def __repr__(self):
        return f"<WorkspaceMember(user_id={self.user_id}, workspace_id={self.workspace_id}, role='{self.role}')>"

class Page(Base):
    __tablename__ = "pages"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic information
    title = Column(String, nullable=False, index=True)
    content = Column(Text, nullable=True)
    page_type = Column(Enum(PageType), default=PageType.DOCUMENT, index=True)
    
    # Organization
    parent_page_id = Column(Integer, ForeignKey("pages.id"), nullable=True, index=True)
    order_index = Column(Integer, default=0)
    
    # Settings
    is_public = Column(Boolean, default=False)
    is_template = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    
    # Page configuration
    properties = Column(JSON, default={})
    layout_config = Column(JSON, default={})
    
    # AI features
    ai_summary = Column(Text, nullable=True)
    ai_tags = Column(JSON, default=[])
    ai_insights = Column(JSON, default={})
    
    # Relationships
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    workspace = relationship("Workspace", back_populates="pages")
    creator = relationship("User")
    parent_page = relationship("Page", remote_side=[id], backref="child_pages")
    tasks = relationship("Task", back_populates="page")
    
    def __repr__(self):
        return f"<Page(id={self.id}, title='{self.title}', type='{self.page_type}')>"
