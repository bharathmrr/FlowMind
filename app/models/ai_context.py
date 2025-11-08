from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class AIContext(Base):
    __tablename__ = "ai_contexts"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Context identification
    context_type = Column(String, nullable=False, index=True)  # task, meeting, general, planning
    context_key = Column(String, nullable=True, index=True)  # Reference to related entity
    
    # Context data
    context_data = Column(JSON, default={})
    conversation_history = Column(JSON, default=[])
    user_preferences = Column(JSON, default={})
    
    # Memory and learning
    long_term_memory = Column(JSON, default={})
    patterns_learned = Column(JSON, default={})
    user_behavior_data = Column(JSON, default={})
    
    # AI model information
    model_version = Column(String, default="grok-beta")
    last_model_update = Column(DateTime(timezone=True), nullable=True)
    
    # Context metadata
    is_active = Column(Boolean, default=True)
    priority_score = Column(Float, default=0.5)  # 0.0 to 1.0
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_accessed = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="ai_contexts")
    insights = relationship("AIInsight", back_populates="context", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<AIContext(id={self.id}, type='{self.context_type}', user_id={self.user_id})>"

class AIInsight(Base):
    __tablename__ = "ai_insights"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Insight information
    insight_type = Column(String, nullable=False, index=True)  # productivity, scheduling, habit, prediction
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    
    # Insight data
    data = Column(JSON, default={})
    metrics = Column(JSON, default={})
    recommendations = Column(JSON, default=[])
    
    # Confidence and validation
    confidence_score = Column(Float, nullable=False)  # 0.0 to 1.0
    validation_score = Column(Float, nullable=True)  # User feedback score
    is_validated = Column(Boolean, default=False)
    
    # Actionability
    is_actionable = Column(Boolean, default=True)
    action_taken = Column(Boolean, default=False)
    action_data = Column(JSON, nullable=True)
    
    # Timing
    valid_from = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    context_id = Column(Integer, ForeignKey("ai_contexts.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    context = relationship("AIContext", back_populates="insights")
    user = relationship("User")
    
    def __repr__(self):
        return f"<AIInsight(id={self.id}, type='{self.insight_type}', confidence={self.confidence_score})>"

class ConversationHistory(Base):
    __tablename__ = "conversation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Conversation metadata
    session_id = Column(String, nullable=False, index=True)
    conversation_type = Column(String, default="chat")  # chat, voice, command
    
    # Message data
    message_role = Column(String, nullable=False)  # user, assistant, system
    message_content = Column(Text, nullable=False)
    message_metadata = Column(JSON, default={})
    
    # AI processing
    intent_detected = Column(String, nullable=True)
    entities_extracted = Column(JSON, default=[])
    sentiment_score = Column(Float, nullable=True)  # -1.0 to 1.0
    
    # Context and memory
    context_used = Column(JSON, default={})
    memory_updated = Column(Boolean, default=False)
    
    # Token usage
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    context_id = Column(Integer, ForeignKey("ai_contexts.id"), nullable=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User")
    context = relationship("AIContext")
    
    def __repr__(self):
        return f"<ConversationHistory(id={self.id}, role='{self.message_role}', session='{self.session_id}')>"
