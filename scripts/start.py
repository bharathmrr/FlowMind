#!/usr/bin/env python3
"""
AI LifeOS FlowMind - Startup Script
"""

import asyncio
import sys
import os
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import DatabaseManager
from app.core.config import settings
import structlog

logger = structlog.get_logger()

async def initialize_database():
    """Initialize database tables"""
    try:
        await DatabaseManager.create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise

async def create_sample_data():
    """Create sample data for development"""
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.core.auth import AuthService
    
    async with AsyncSessionLocal() as db:
        try:
            # Check if sample user exists
            from sqlalchemy import select
            query = select(User).where(User.email == "demo@flowmind.ai")
            result = await db.execute(query)
            existing_user = result.scalar_one_or_none()
            
            if not existing_user:
                # Create demo user
                demo_user = User(
                    email="demo@flowmind.ai",
                    username="demo_user",
                    full_name="Demo User",
                    hashed_password=AuthService.get_password_hash("demo123456"),
                    is_active=True,
                    is_verified=True,
                    timezone="UTC",
                    ai_preferences={
                        "personality": "professional",
                        "communication_style": "concise",
                        "proactivity_level": "medium",
                        "focus_mode_enabled": True,
                        "auto_scheduling": True,
                        "smart_notifications": True
                    },
                    productivity_settings={
                        "work_hours_start": "09:00",
                        "work_hours_end": "17:00",
                        "break_duration": 15,
                        "focus_session_duration": 25,
                        "deep_work_blocks": 2,
                        "meeting_buffer": 5
                    }
                )
                
                db.add(demo_user)
                await db.commit()
                logger.info("Demo user created", email="demo@flowmind.ai")
            else:
                logger.info("Demo user already exists")
                
        except Exception as e:
            logger.error("Sample data creation failed", error=str(e))
            raise

def print_startup_info():
    """Print startup information"""
    print("\n" + "="*60)
    print("🧠 AI LifeOS - FlowMind Backend")
    print("="*60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'Not configured'}")
    print(f"Redis: {settings.REDIS_URL}")
    print(f"AI Model: {settings.AI_MODEL}")
    print("\n📡 API Endpoints:")
    print("  - Swagger UI: http://localhost:8000/docs")
    print("  - ReDoc: http://localhost:8000/redoc")
    print("  - Health Check: http://localhost:8000/health")
    print("\n🔧 Services:")
    print("  - Backend API: http://localhost:8000")
    print("  - Flower (Celery): http://localhost:5555")
    print("  - PostgreSQL: localhost:5432")
    print("  - Redis: localhost:6379")
    print("\n👤 Demo Account:")
    print("  - Email: demo@flowmind.ai")
    print("  - Password: demo123456")
    print("\n🚀 Ready to revolutionize productivity with AI!")
    print("="*60 + "\n")

async def main():
    """Main startup function"""
    try:
        print_startup_info()
        
        logger.info("Starting AI LifeOS FlowMind initialization...")
        
        # Initialize database
        await initialize_database()
        
        # Create sample data in development
        if settings.ENVIRONMENT == "development":
            await create_sample_data()
        
        logger.info("Initialization completed successfully")
        
        # Start the FastAPI server
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.ENVIRONMENT == "development",
            log_level=settings.LOG_LEVEL.lower()
        )
        
    except Exception as e:
        logger.error("Startup failed", error=str(e))
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
