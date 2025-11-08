import httpx
import json
import structlog
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime, timedelta
import asyncio
import re
from dataclasses import dataclass

from app.core.config import settings
from app.models.ai_context import AIContext, ConversationHistory
from app.models.user import User
from app.models.task import Task
from app.models.meeting import Meeting

logger = structlog.get_logger()

@dataclass
class TaskParsing:
    title: str
    description: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[datetime] = None
    estimated_duration: Optional[int] = None
    tags: List[str] = None
    dependencies: List[str] = None
    subtasks: List[str] = None
    ai_confidence: float = 0.0
    reasoning: str = ""

@dataclass
class ScheduleOptimization:
    optimized_schedule: List[Dict]
    conflicts_resolved: List[Dict]
    productivity_tips: List[str]
    focus_blocks: List[Dict]
    optimization_score: float
    reasoning: str

@dataclass
class ProductivityInsight:
    type: str
    title: str
    description: str
    impact_score: float
    recommendations: List[str]
    data_points: Dict
    confidence: float

class EnhancedGrokService:
    """
    Enhanced Grok LLM integration service with advanced AI capabilities
    """
    
    def __init__(self):
        self.api_key = settings.GROK_API_KEY
        self.api_url = settings.GROK_API_URL
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        
        # Fallback to OpenAI if Grok not available
        if not self.api_key:
            logger.warning("Grok API key not configured, using fallback OpenAI")
            self.api_key = settings.OPENAI_API_KEY
            self.api_url = "https://api.openai.com/v1"
            self.model = "gpt-4-turbo-preview"
    
    async def parse_natural_language_task(
        self, 
        task_input: str, 
        user_id: int,
        user_context: Optional[Dict] = None
    ) -> TaskParsing:
        """Enhanced natural language task parsing with context awareness"""
        
        system_prompt = f"""
        You are an advanced AI task understanding system. Parse natural language task descriptions with high accuracy.
        
        Extract and infer:
        1. Core task information (title, description, priority)
        2. Temporal information (due dates, time estimates)
        3. Contextual information (tags, categories, dependencies)
        4. Subtask breakdown for complex tasks
        
        User Context: {json.dumps(user_context or {}, indent=2)}
        Current Time: {datetime.utcnow().isoformat()}
        
        Rules:
        - Infer priority from urgency indicators (ASAP, urgent, important, etc.)
        - Parse relative dates ("tomorrow", "next week", "in 3 days")
        - Estimate duration based on task complexity
        - Identify dependencies ("after X", "once Y is done")
        - Break down complex tasks into subtasks
        - Extract relevant tags from context
        
        Return JSON with confidence score and reasoning.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Parse this task: {task_input}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.1)
            content = response["choices"][0]["message"]["content"]
            
            # Parse JSON response
            parsed_data = json.loads(content)
            
            # Convert to TaskParsing object
            task_parsing = TaskParsing(
                title=parsed_data.get("title", task_input[:100]),
                description=parsed_data.get("description"),
                priority=parsed_data.get("priority", "medium"),
                due_date=self._parse_datetime(parsed_data.get("due_date")),
                estimated_duration=parsed_data.get("estimated_duration"),
                tags=parsed_data.get("tags", []),
                dependencies=parsed_data.get("dependencies", []),
                subtasks=parsed_data.get("subtasks", []),
                ai_confidence=parsed_data.get("confidence", 0.8),
                reasoning=parsed_data.get("reasoning", "AI parsed task from natural language")
            )
            
            logger.info("Enhanced task parsing completed", 
                       user_id=user_id, 
                       confidence=task_parsing.ai_confidence)
            return task_parsing
            
        except Exception as e:
            logger.error("Enhanced task parsing failed", error=str(e), user_id=user_id)
            # Return basic fallback
            return TaskParsing(
                title=task_input[:100],
                description=task_input if len(task_input) > 100 else None,
                priority="medium",
                ai_confidence=0.3,
                reasoning="Fallback parsing due to AI service error"
            )
    
    async def generate_schedule_optimization(
        self,
        user_id: int,
        tasks: List[Dict],
        events: List[Dict],
        preferences: Dict,
        constraints: List[str] = None
    ) -> ScheduleOptimization:
        """Advanced schedule optimization with AI reasoning"""
        
        system_prompt = f"""
        You are an expert AI scheduling optimizer. Create optimal schedules considering:
        
        1. Task priorities and deadlines
        2. User productivity patterns and preferences
        3. Meeting conflicts and travel time
        4. Energy levels and focus patterns
        5. Break times and wellness
        6. External factors (weather, location)
        
        Optimization Goals:
        - Maximize productivity and task completion
        - Minimize context switching
        - Respect energy patterns and preferences
        - Ensure adequate breaks and focus time
        - Resolve conflicts intelligently
        
        User Preferences: {json.dumps(preferences, indent=2)}
        Constraints: {constraints or []}
        
        Return detailed optimization with reasoning and confidence scores.
        """
        
        context_data = {
            "tasks": tasks,
            "events": events,
            "preferences": preferences,
            "constraints": constraints,
            "current_time": datetime.utcnow().isoformat(),
            "optimization_goals": [
                "maximize_productivity",
                "minimize_conflicts",
                "respect_energy_patterns",
                "ensure_focus_time"
            ]
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Optimize schedule: {json.dumps(context_data, indent=2)}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.3)
            content = response["choices"][0]["message"]["content"]
            
            optimization_data = json.loads(content)
            
            optimization = ScheduleOptimization(
                optimized_schedule=optimization_data.get("optimized_schedule", []),
                conflicts_resolved=optimization_data.get("conflicts_resolved", []),
                productivity_tips=optimization_data.get("productivity_tips", []),
                focus_blocks=optimization_data.get("focus_blocks", []),
                optimization_score=optimization_data.get("optimization_score", 0.0),
                reasoning=optimization_data.get("reasoning", "AI-generated schedule optimization")
            )
            
            logger.info("Schedule optimization completed", 
                       user_id=user_id, 
                       score=optimization.optimization_score)
            return optimization
            
        except Exception as e:
            logger.error("Schedule optimization failed", error=str(e), user_id=user_id)
            return ScheduleOptimization(
                optimized_schedule=[],
                conflicts_resolved=[],
                productivity_tips=["Unable to generate optimization at this time"],
                focus_blocks=[],
                optimization_score=0.0,
                reasoning="Optimization failed due to service error"
            )
    
    async def analyze_productivity_patterns(
        self,
        user_id: int,
        historical_data: Dict,
        time_period: str = "month"
    ) -> List[ProductivityInsight]:
        """Deep productivity pattern analysis with actionable insights"""
        
        system_prompt = f"""
        You are an AI productivity analyst. Analyze user behavior patterns and generate insights.
        
        Analysis Areas:
        1. Task completion patterns (time, priority, category)
        2. Focus and energy patterns throughout day/week
        3. Procrastination and distraction patterns
        4. Efficiency trends and bottlenecks
        5. Goal achievement and habit formation
        6. Work-life balance indicators
        
        Generate specific, actionable insights with:
        - Clear impact assessment
        - Data-driven recommendations
        - Confidence scores
        - Implementation suggestions
        
        Time Period: {time_period}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze productivity: {json.dumps(historical_data, indent=2)}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.4)
            content = response["choices"][0]["message"]["content"]
            
            insights_data = json.loads(content)
            
            insights = []
            for insight_data in insights_data.get("insights", []):
                insight = ProductivityInsight(
                    type=insight_data.get("type", "general"),
                    title=insight_data.get("title", ""),
                    description=insight_data.get("description", ""),
                    impact_score=insight_data.get("impact_score", 0.0),
                    recommendations=insight_data.get("recommendations", []),
                    data_points=insight_data.get("data_points", {}),
                    confidence=insight_data.get("confidence", 0.0)
                )
                insights.append(insight)
            
            logger.info("Productivity analysis completed", 
                       user_id=user_id, 
                       insights_count=len(insights))
            return insights
            
        except Exception as e:
            logger.error("Productivity analysis failed", error=str(e), user_id=user_id)
            return []
    
    async def generate_smart_notifications(
        self,
        user_id: int,
        context: Dict
    ) -> List[Dict]:
        """Generate contextually aware smart notifications"""
        
        system_prompt = f"""
        You are an AI notification system. Generate smart, contextual notifications that help users stay productive.
        
        Notification Types:
        1. Proactive task reminders based on deadlines and patterns
        2. Meeting preparation suggestions
        3. Break and wellness reminders
        4. Weather and travel alerts
        5. Productivity tips and insights
        6. Focus mode suggestions
        
        Context Factors:
        - Current time and user timezone
        - User's schedule and workload
        - Weather and location
        - Historical patterns and preferences
        - Quiet hours and notification preferences
        
        Generate notifications that are:
        - Timely and relevant
        - Actionable with clear next steps
        - Respectful of user preferences
        - Personalized to user patterns
        
        Context: {json.dumps(context, indent=2)}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Generate smart notifications for current context"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.5)
            content = response["choices"][0]["message"]["content"]
            
            notifications_data = json.loads(content)
            
            logger.info("Smart notifications generated", 
                       user_id=user_id, 
                       count=len(notifications_data.get("notifications", [])))
            return notifications_data.get("notifications", [])
            
        except Exception as e:
            logger.error("Smart notification generation failed", error=str(e), user_id=user_id)
            return []
    
    async def process_voice_command(
        self,
        command: str,
        user_id: int,
        context: Dict
    ) -> Dict:
        """Process voice commands with intent recognition and action extraction"""
        
        system_prompt = f"""
        You are an AI voice command processor. Parse voice commands and extract actionable intents.
        
        Command Types:
        1. Task management (create, complete, update, schedule)
        2. Calendar operations (schedule, reschedule, view)
        3. Information queries (schedule, tasks, insights)
        4. Focus and productivity commands
        5. General assistance and navigation
        
        For each command:
        - Identify primary intent and confidence
        - Extract relevant parameters and entities
        - Determine required actions
        - Generate appropriate response
        - Handle ambiguity gracefully
        
        Context: {json.dumps(context, indent=2)}
        
        Return structured response with intent, actions, and natural language response.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Process voice command: '{command}'"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.3)
            content = response["choices"][0]["message"]["content"]
            
            command_data = json.loads(content)
            
            logger.info("Voice command processed", 
                       user_id=user_id, 
                       intent=command_data.get("intent"),
                       confidence=command_data.get("confidence"))
            return command_data
            
        except Exception as e:
            logger.error("Voice command processing failed", error=str(e), user_id=user_id)
            return {
                "intent": "error",
                "confidence": 0.0,
                "response": "I'm sorry, I couldn't understand that command.",
                "success": False
            }
    
    async def generate_meeting_insights(
        self,
        meeting_transcript: str,
        meeting_context: Dict,
        user_id: int
    ) -> Dict:
        """Advanced meeting analysis with action item extraction and insights"""
        
        system_prompt = f"""
        You are an AI meeting analyst. Analyze meeting transcripts and extract comprehensive insights.
        
        Analysis Areas:
        1. Meeting summary and key topics
        2. Action items with owners and deadlines
        3. Decisions made and next steps
        4. Follow-up requirements
        5. Participant engagement and contributions
        6. Meeting effectiveness assessment
        7. Improvement suggestions
        
        Extract:
        - Clear, actionable items with assignees
        - Important decisions and rationale
        - Unresolved issues requiring follow-up
        - Meeting quality metrics
        - Recommendations for future meetings
        
        Meeting Context: {json.dumps(meeting_context, indent=2)}
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze meeting: {meeting_transcript}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.2)
            content = response["choices"][0]["message"]["content"]
            
            analysis = json.loads(content)
            
            logger.info("Meeting analysis completed", 
                       user_id=user_id, 
                       meeting_id=meeting_context.get("id"),
                       action_items=len(analysis.get("action_items", [])))
            return analysis
            
        except Exception as e:
            logger.error("Meeting analysis failed", error=str(e), user_id=user_id)
            return {"error": "Analysis failed", "summary": "Unable to analyze meeting at this time"}
    
    async def _make_request(
        self, 
        messages: List[Dict[str, str]], 
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request to Grok/OpenAI with enhanced error handling"""
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": kwargs.get("max_tokens", self.max_tokens),
            "temperature": kwargs.get("temperature", self.temperature),
            "stream": stream
        }
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPError as e:
            logger.error("Enhanced Grok API request failed", error=str(e))
            raise Exception(f"AI service unavailable: {str(e)}")
    
    def _parse_datetime(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse various date string formats"""
        if not date_str:
            return None
        
        try:
            # Try ISO format first
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%m/%d/%Y", "%d/%m/%Y"]:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
            except:
                pass
        
        return None

# Global enhanced instance
enhanced_grok_service = EnhancedGrokService()
