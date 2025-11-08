import httpx
import json
import structlog
from typing import Dict, List, Optional, Any, AsyncGenerator
from datetime import datetime
import asyncio

from app.core.config import settings
from app.models.ai_context import AIContext, ConversationHistory
from app.models.user import User

logger = structlog.get_logger()

class GrokService:
    """
    Grok LLM integration service for AI-powered productivity features
    """
    
    def __init__(self):
        self.api_key = settings.GROK_API_KEY
        self.api_url = settings.GROK_API_URL
        self.model = settings.AI_MODEL
        self.max_tokens = settings.AI_MAX_TOKENS
        self.temperature = settings.AI_TEMPERATURE
        
        if not self.api_key:
            logger.warning("Grok API key not configured, using fallback OpenAI")
            self.api_key = settings.OPENAI_API_KEY
            self.api_url = "https://api.openai.com/v1"
            self.model = "gpt-4-turbo-preview"
    
    async def _make_request(
        self, 
        messages: List[Dict[str, str]], 
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Make API request to Grok/OpenAI"""
        
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
            logger.error("Grok API request failed", error=str(e))
            raise Exception(f"AI service unavailable: {str(e)}")
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        user_id: int,
        context_id: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate chat completion with context awareness"""
        
        try:
            # Add system context if available
            if context_id:
                context_messages = await self._get_context_messages(context_id)
                messages = context_messages + messages
            
            # Make API request
            response = await self._make_request(messages, **kwargs)
            
            # Log conversation
            await self._log_conversation(
                user_id=user_id,
                context_id=context_id,
                messages=messages,
                response=response
            )
            
            return response
            
        except Exception as e:
            logger.error("Chat completion failed", error=str(e), user_id=user_id)
            raise
    
    async def parse_natural_language_task(
        self, 
        task_input: str, 
        user_id: int,
        user_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Parse natural language input into structured task data"""
        
        system_prompt = """
        You are an AI assistant specialized in parsing natural language task descriptions.
        Extract the following information from user input:
        
        - title: Clear, concise task title
        - description: Detailed description if provided
        - due_date: Parse any time/date references (return ISO format)
        - priority: low, medium, high, urgent (infer from context)
        - estimated_duration: Duration in minutes if mentioned
        - tags: Relevant tags/categories
        - dependencies: Any mentioned prerequisites
        - subtasks: Break down complex tasks if appropriate
        
        Return JSON format only. If information is not provided, use null.
        Consider user's timezone and current time for date parsing.
        """
        
        user_context_str = ""
        if user_context:
            user_context_str = f"\nUser context: {json.dumps(user_context, indent=2)}"
        
        messages = [
            {"role": "system", "content": system_prompt + user_context_str},
            {"role": "user", "content": f"Parse this task: {task_input}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.1)
            content = response["choices"][0]["message"]["content"]
            
            # Parse JSON response
            task_data = json.loads(content)
            
            logger.info("Task parsed successfully", user_id=user_id, input=task_input)
            return task_data
            
        except (json.JSONDecodeError, KeyError) as e:
            logger.error("Failed to parse task response", error=str(e), user_id=user_id)
            # Return basic fallback
            return {
                "title": task_input[:100],
                "description": task_input if len(task_input) > 100 else None,
                "priority": "medium"
            }
    
    async def generate_schedule_optimization(
        self,
        user_id: int,
        tasks: List[Dict],
        events: List[Dict],
        preferences: Dict
    ) -> Dict[str, Any]:
        """Generate optimized schedule suggestions"""
        
        system_prompt = """
        You are an AI scheduling optimizer. Analyze the user's tasks, existing events, 
        and preferences to suggest an optimal schedule.
        
        Consider:
        - Task priorities and deadlines
        - User's productivity patterns
        - Meeting conflicts
        - Break times and focus blocks
        - Travel time between locations
        - Energy levels throughout the day
        
        Return suggestions in JSON format with:
        - optimized_schedule: List of time slots with tasks/events
        - conflicts_resolved: List of conflicts and resolutions
        - productivity_tips: Personalized recommendations
        - focus_blocks: Suggested deep work periods
        """
        
        context_data = {
            "tasks": tasks,
            "events": events,
            "preferences": preferences,
            "current_time": datetime.utcnow().isoformat()
        }
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Optimize my schedule: {json.dumps(context_data, indent=2)}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.3)
            content = response["choices"][0]["message"]["content"]
            
            optimization_data = json.loads(content)
            
            logger.info("Schedule optimized", user_id=user_id)
            return optimization_data
            
        except Exception as e:
            logger.error("Schedule optimization failed", error=str(e), user_id=user_id)
            return {"error": "Optimization failed", "fallback": True}
    
    async def analyze_meeting_transcript(
        self,
        transcript: str,
        meeting_context: Dict,
        user_id: int
    ) -> Dict[str, Any]:
        """Analyze meeting transcript and extract insights"""
        
        system_prompt = """
        You are an AI meeting analyst. Analyze the meeting transcript and extract:
        
        - summary: Concise meeting summary
        - action_items: List of tasks with assignees and due dates
        - key_decisions: Important decisions made
        - follow_up_items: Items requiring follow-up
        - sentiment_analysis: Overall meeting sentiment and engagement
        - key_topics: Main topics discussed
        - participants_insights: Individual contribution analysis
        
        Return structured JSON format.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Meeting context: {json.dumps(meeting_context)}\n\nTranscript: {transcript}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.2)
            content = response["choices"][0]["message"]["content"]
            
            analysis = json.loads(content)
            
            logger.info("Meeting analyzed", user_id=user_id, meeting_id=meeting_context.get("id"))
            return analysis
            
        except Exception as e:
            logger.error("Meeting analysis failed", error=str(e), user_id=user_id)
            return {"error": "Analysis failed"}
    
    async def generate_productivity_insights(
        self,
        user_id: int,
        productivity_data: Dict,
        time_period: str = "week"
    ) -> Dict[str, Any]:
        """Generate personalized productivity insights"""
        
        system_prompt = f"""
        You are an AI productivity coach. Analyze the user's {time_period} productivity data 
        and provide actionable insights.
        
        Focus on:
        - Productivity patterns and trends
        - Time allocation analysis
        - Goal achievement progress
        - Efficiency improvements
        - Habit formation suggestions
        - Energy and focus optimization
        - Work-life balance recommendations
        
        Provide encouraging, actionable advice in JSON format.
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analyze my productivity: {json.dumps(productivity_data, indent=2)}"}
        ]
        
        try:
            response = await self._make_request(messages, temperature=0.4)
            content = response["choices"][0]["message"]["content"]
            
            insights = json.loads(content)
            
            logger.info("Productivity insights generated", user_id=user_id, period=time_period)
            return insights
            
        except Exception as e:
            logger.error("Productivity insights failed", error=str(e), user_id=user_id)
            return {"error": "Insights generation failed"}
    
    async def _get_context_messages(self, context_id: int) -> List[Dict[str, str]]:
        """Retrieve context messages for conversation continuity"""
        # This would typically query the database for context
        # For now, return empty list
        return []
    
    async def _log_conversation(
        self,
        user_id: int,
        context_id: Optional[int],
        messages: List[Dict],
        response: Dict
    ):
        """Log conversation for learning and context"""
        try:
            # Extract token usage
            usage = response.get("usage", {})
            
            # Log user message
            if messages:
                last_user_message = next(
                    (msg for msg in reversed(messages) if msg["role"] == "user"), 
                    None
                )
                if last_user_message:
                    # Here you would save to ConversationHistory model
                    logger.info(
                        "Conversation logged",
                        user_id=user_id,
                        context_id=context_id,
                        tokens=usage.get("total_tokens", 0)
                    )
        except Exception as e:
            logger.error("Failed to log conversation", error=str(e))

# Global instance
grok_service = GrokService()
