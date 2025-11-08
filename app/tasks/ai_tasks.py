from celery import current_app as celery_app
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import asyncio
import structlog
from datetime import datetime, timedelta

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task
from app.models.meeting import Meeting
from app.services.ai.grok_service import grok_service

logger = structlog.get_logger()

@celery_app.task(bind=True, max_retries=3)
def generate_daily_productivity_insights(self):
    """Generate daily productivity insights for all users"""
    
    async def _generate_insights():
        async with AsyncSessionLocal() as db:
            try:
                # Get all active users
                query = select(User).where(User.is_active == True)
                result = await db.execute(query)
                users = result.scalars().all()
                
                insights_generated = 0
                
                for user in users:
                    try:
                        # Get user's productivity data for the last 7 days
                        end_date = datetime.utcnow()
                        start_date = end_date - timedelta(days=7)
                        
                        # Get tasks data
                        tasks_query = select(Task).where(
                            Task.user_id == user.id,
                            Task.created_at >= start_date
                        )
                        tasks_result = await db.execute(tasks_query)
                        tasks = tasks_result.scalars().all()
                        
                        # Prepare productivity data
                        productivity_data = {
                            "user_id": user.id,
                            "period": "7_days",
                            "tasks": [
                                {
                                    "id": task.id,
                                    "title": task.title,
                                    "status": task.status.value,
                                    "priority": task.priority.value,
                                    "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                                    "estimated_duration": task.estimated_duration,
                                    "actual_duration": task.actual_duration
                                }
                                for task in tasks
                            ],
                            "user_preferences": user.productivity_settings,
                            "timezone": user.timezone
                        }
                        
                        # Generate insights using Grok
                        insights = await grok_service.generate_productivity_insights(
                            user_id=user.id,
                            productivity_data=productivity_data,
                            time_period="week"
                        )
                        
                        # Store insights (would save to AIInsight model)
                        logger.info(
                            "Productivity insights generated",
                            user_id=user.id,
                            insights_count=len(insights.get("recommendations", []))
                        )
                        
                        insights_generated += 1
                        
                    except Exception as e:
                        logger.error(
                            "Failed to generate insights for user",
                            user_id=user.id,
                            error=str(e)
                        )
                        continue
                
                logger.info(
                    "Daily productivity insights completed",
                    total_users=len(users),
                    insights_generated=insights_generated
                )
                
            except Exception as e:
                logger.error("Failed to generate daily insights", error=str(e))
                raise
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_generate_insights())
    finally:
        loop.close()

@celery_app.task(bind=True, max_retries=3)
def process_meeting_recordings(self):
    """Process meeting recordings and generate summaries"""
    
    async def _process_recordings():
        async with AsyncSessionLocal() as db:
            try:
                # Get meetings with recordings that haven't been processed
                query = select(Meeting).where(
                    Meeting.recording_url.isnot(None),
                    Meeting.ai_summary.is_(None),
                    Meeting.status == "completed"
                )
                result = await db.execute(query)
                meetings = result.scalars().all()
                
                processed_count = 0
                
                for meeting in meetings:
                    try:
                        # For now, simulate transcript processing
                        # In production, you'd download and transcribe the recording
                        mock_transcript = f"Meeting transcript for: {meeting.title}"
                        
                        meeting_context = {
                            "id": meeting.id,
                            "title": meeting.title,
                            "duration": meeting.duration_minutes,
                            "participants": len(meeting.participants),
                            "type": meeting.meeting_type.value
                        }
                        
                        # Analyze transcript using Grok
                        analysis = await grok_service.analyze_meeting_transcript(
                            transcript=mock_transcript,
                            meeting_context=meeting_context,
                            user_id=meeting.organizer_id
                        )
                        
                        # Update meeting with AI analysis
                        meeting.ai_summary = analysis.get("summary")
                        meeting.ai_action_items = analysis.get("action_items", [])
                        meeting.ai_key_decisions = analysis.get("key_decisions", [])
                        
                        await db.commit()
                        
                        logger.info(
                            "Meeting recording processed",
                            meeting_id=meeting.id,
                            action_items=len(analysis.get("action_items", []))
                        )
                        
                        processed_count += 1
                        
                    except Exception as e:
                        logger.error(
                            "Failed to process meeting recording",
                            meeting_id=meeting.id,
                            error=str(e)
                        )
                        continue
                
                logger.info(
                    "Meeting recordings processing completed",
                    total_meetings=len(meetings),
                    processed_count=processed_count
                )
                
            except Exception as e:
                logger.error("Failed to process meeting recordings", error=str(e))
                raise
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_process_recordings())
    finally:
        loop.close()

@celery_app.task(bind=True, max_retries=3)
def optimize_user_schedules(self):
    """Optimize schedules for all active users"""
    
    async def _optimize_schedules():
        async with AsyncSessionLocal() as db:
            try:
                # Get users who have AI optimization enabled
                query = select(User).where(
                    User.is_active == True,
                    User.ai_preferences["auto_scheduling"].astext.cast(bool) == True
                )
                result = await db.execute(query)
                users = result.scalars().all()
                
                optimized_count = 0
                
                for user in users:
                    try:
                        # Get user's pending tasks
                        tasks_query = select(Task).where(
                            Task.user_id == user.id,
                            Task.status.in_(["pending", "in_progress"]),
                            Task.due_date.isnot(None)
                        ).limit(20)
                        
                        tasks_result = await db.execute(tasks_query)
                        tasks = tasks_result.scalars().all()
                        
                        if not tasks:
                            continue
                        
                        # Prepare data for optimization
                        tasks_data = [
                            {
                                "id": task.id,
                                "title": task.title,
                                "priority": task.priority.value,
                                "due_date": task.due_date.isoformat(),
                                "estimated_duration": task.estimated_duration
                            }
                            for task in tasks
                        ]
                        
                        # Generate schedule optimization
                        optimization = await grok_service.generate_schedule_optimization(
                            user_id=user.id,
                            tasks=tasks_data,
                            events=[],  # Would get from calendar
                            preferences=user.productivity_settings
                        )
                        
                        # Apply optimizations (update suggested time slots)
                        for suggestion in optimization.get("optimized_schedule", []):
                            task_id = suggestion.get("task_id")
                            suggested_time = suggestion.get("suggested_time")
                            
                            if task_id and suggested_time:
                                # Update task with AI suggestion
                                task = next((t for t in tasks if t.id == task_id), None)
                                if task:
                                    task.ai_suggested_time_slot = datetime.fromisoformat(suggested_time)
                        
                        await db.commit()
                        
                        logger.info(
                            "Schedule optimized for user",
                            user_id=user.id,
                            tasks_optimized=len(tasks)
                        )
                        
                        optimized_count += 1
                        
                    except Exception as e:
                        logger.error(
                            "Failed to optimize schedule for user",
                            user_id=user.id,
                            error=str(e)
                        )
                        continue
                
                logger.info(
                    "Schedule optimization completed",
                    total_users=len(users),
                    optimized_count=optimized_count
                )
                
            except Exception as e:
                logger.error("Failed to optimize schedules", error=str(e))
                raise
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_optimize_schedules())
    finally:
        loop.close()

@celery_app.task(bind=True)
def analyze_user_productivity_patterns(self, user_id: int):
    """Analyze individual user's productivity patterns"""
    
    async def _analyze_patterns():
        async with AsyncSessionLocal() as db:
            try:
                # Get user's historical data
                user_query = select(User).where(User.id == user_id)
                user_result = await db.execute(user_query)
                user = user_result.scalar_one_or_none()
                
                if not user:
                    logger.warning("User not found for pattern analysis", user_id=user_id)
                    return
                
                # Get tasks from last 30 days
                start_date = datetime.utcnow() - timedelta(days=30)
                tasks_query = select(Task).where(
                    Task.user_id == user_id,
                    Task.created_at >= start_date
                )
                tasks_result = await db.execute(tasks_query)
                tasks = tasks_result.scalars().all()
                
                # Analyze patterns
                patterns = {
                    "most_productive_hours": [],
                    "completion_patterns": {},
                    "priority_handling": {},
                    "task_duration_accuracy": 0.0
                }
                
                # Calculate completion patterns by day of week
                for task in tasks:
                    if task.completed_at:
                        day_of_week = task.completed_at.strftime("%A")
                        if day_of_week not in patterns["completion_patterns"]:
                            patterns["completion_patterns"][day_of_week] = 0
                        patterns["completion_patterns"][day_of_week] += 1
                
                logger.info(
                    "Productivity patterns analyzed",
                    user_id=user_id,
                    patterns=patterns
                )
                
                return patterns
                
            except Exception as e:
                logger.error(
                    "Failed to analyze productivity patterns",
                    user_id=user_id,
                    error=str(e)
                )
                raise
    
    # Run async function
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_analyze_patterns())
    finally:
        loop.close()
