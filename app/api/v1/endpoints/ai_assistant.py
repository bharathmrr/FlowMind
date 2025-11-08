from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import structlog

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User
from app.services.ai.grok_service import grok_service
from app.schemas.ai import (
    ChatRequest,
    ChatResponse,
    ScheduleOptimizationRequest,
    ScheduleOptimizationResponse,
    ProductivityInsightResponse
)

logger = structlog.get_logger()
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    chat_request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Chat with AI assistant"""
    try:
        # Prepare messages for Grok
        messages = [
            {"role": "system", "content": "You are a helpful AI productivity assistant. Help users manage their tasks, schedule, and productivity goals."},
            {"role": "user", "content": chat_request.message}
        ]
        
        # Add conversation history if provided
        if chat_request.conversation_history:
            messages = chat_request.conversation_history + messages[-1:]
        
        # Get AI response
        response = await grok_service.chat_completion(
            messages=messages,
            user_id=current_user.id,
            context_id=chat_request.context_id
        )
        
        ai_message = response["choices"][0]["message"]["content"]
        
        logger.info("AI chat completed", user_id=current_user.id, message_length=len(ai_message))
        
        return ChatResponse(
            message=ai_message,
            conversation_id=chat_request.context_id or "default",
            tokens_used=response.get("usage", {}).get("total_tokens", 0)
        )
        
    except Exception as e:
        logger.error("AI chat failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="AI chat service unavailable")

@router.post("/optimize-schedule", response_model=ScheduleOptimizationResponse)
async def optimize_schedule(
    request: ScheduleOptimizationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Optimize user's schedule using AI"""
    try:
        # Get user's tasks and events (simplified for demo)
        tasks_data = []
        events_data = []
        
        # Generate optimization using Grok
        optimization = await grok_service.generate_schedule_optimization(
            user_id=current_user.id,
            tasks=tasks_data,
            events=events_data,
            preferences=current_user.productivity_settings
        )
        
        logger.info("Schedule optimization completed", user_id=current_user.id)
        
        return ScheduleOptimizationResponse(
            optimized_schedule=optimization.get("optimized_schedule", []),
            conflicts_resolved=optimization.get("conflicts_resolved", []),
            productivity_tips=optimization.get("productivity_tips", []),
            focus_blocks=optimization.get("focus_blocks", [])
        )
        
    except Exception as e:
        logger.error("Schedule optimization failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Schedule optimization failed")

@router.get("/insights", response_model=ProductivityInsightResponse)
async def get_productivity_insights(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get AI-powered productivity insights"""
    try:
        # Prepare productivity data (simplified)
        productivity_data = {
            "user_id": current_user.id,
            "period_days": days,
            "tasks_completed": 0,
            "focus_sessions": 0,
            "productivity_patterns": {}
        }
        
        # Generate insights using Grok
        insights = await grok_service.generate_productivity_insights(
            user_id=current_user.id,
            productivity_data=productivity_data,
            time_period="week" if days <= 7 else "month"
        )
        
        logger.info("Productivity insights generated", user_id=current_user.id, period=days)
        
        return ProductivityInsightResponse(
            insights=insights.get("insights", []),
            recommendations=insights.get("recommendations", []),
            productivity_score=insights.get("productivity_score", 0),
            trends=insights.get("trends", {}),
            focus_analysis=insights.get("focus_analysis", {})
        )
        
    except Exception as e:
        logger.error("Productivity insights failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Failed to generate insights")

@router.post("/analyze-text")
async def analyze_text_for_tasks(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """Analyze text and extract potential tasks/actions"""
    try:
        # Use Grok to analyze text for actionable items
        parsed_data = await grok_service.parse_natural_language_task(
            text,
            current_user.id,
            {"timezone": current_user.timezone}
        )
        
        return {
            "extracted_tasks": [parsed_data] if parsed_data.get("title") else [],
            "suggested_actions": parsed_data.get("suggested_actions", []),
            "entities": parsed_data.get("entities", [])
        }
        
    except Exception as e:
        logger.error("Text analysis failed", error=str(e), user_id=current_user.id)
        raise HTTPException(status_code=500, detail="Text analysis failed")
