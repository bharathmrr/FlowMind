from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    context_id: Optional[str] = None
    conversation_history: Optional[List[Dict[str, str]]] = None

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    tokens_used: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class ScheduleOptimizationRequest(BaseModel):
    date_range: Optional[Dict[str, str]] = None
    preferences: Optional[Dict[str, Any]] = None
    constraints: Optional[List[str]] = None

class ScheduleOptimizationResponse(BaseModel):
    optimized_schedule: List[Dict[str, Any]]
    conflicts_resolved: List[Dict[str, Any]]
    productivity_tips: List[str]
    focus_blocks: List[Dict[str, Any]]
    optimization_score: float = 0.0

class ProductivityInsightResponse(BaseModel):
    insights: List[Dict[str, Any]]
    recommendations: List[str]
    productivity_score: float
    trends: Dict[str, Any]
    focus_analysis: Dict[str, Any]
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class AIContextCreate(BaseModel):
    context_type: str
    context_key: Optional[str] = None
    context_data: Dict[str, Any] = Field(default_factory=dict)

class AIContextResponse(BaseModel):
    id: int
    uuid: str
    context_type: str
    context_key: Optional[str]
    context_data: Dict[str, Any]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
