# FlowMind
# AI LifeOS - FlowMind Backend

**A gentler way to get things done** — AI-powered productivity and scheduling platform with Grok LLM integration.

## Core Features

### AI-Powered Task Management
- **Natural Language Processing**: Create tasks using natural language ("Finish AI report by next Friday 5 PM")
- **Smart Auto-Scheduler**: Dynamically adjusts schedules based on meeting lengths, task complexity, and personal focus patterns
- **Adaptive Prioritization**: Grok LLM ranks tasks by importance, urgency, and historical completion behavior
- **Habit-Based Scheduling**: Learns user productivity cycles and recommends optimal task timing

### Intelligent Calendar & Meetings
- **Unified Calendar**: Integrates with Google Calendar, Outlook, and other platforms
- **AI Meeting Summarizer**: Grok transcribes and summarizes meetings, generating actionable to-do items
- **Smart Conflict Resolution**: Automatically detects and suggests solutions for scheduling conflicts
- **Meeting Preparation**: AI-powered agenda suggestions and pre-meeting briefs

### AI Cognitive Layer
- **Grok-Powered Insights**: Analyzes productivity trends and provides personalized recommendations
- **Context Awareness**: Maintains long-term conversation memory and project context
- **Predictive Planning**: Anticipates task collisions and suggests optimizations
- **Focus Mode**: AI-driven distraction blocking and productivity optimization

## Technical Architecture

### Backend Stack
- **FastAPI**: High-performance Python web framework
- **PostgreSQL**: Primary database with async support
- **Redis**: Caching and message broker
- **Celery**: Background task processing
- **SQLAlchemy**: ORM with async support

### AI Integration
- **Grok LLM**: Primary AI model for reasoning and insights
- **LangChain**: AI workflow orchestration
- **OpenAI Fallback**: Backup AI service
- **Whisper**: Speech-to-text processing

### Infrastructure
- **Docker**: Containerized deployment
- **Kubernetes**: Scalable orchestration
- **Structured Logging**: JSON-based logging with correlation IDs
- **Monitoring**: Prometheus metrics and health checks

## Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd FlowMind
```

2. **Set up environment**
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. **Start services with Docker**
```bash
docker-compose up -d
```

4. **Install dependencies (for local development)**
```bash
pip install -r requirements.txt
```

5. **Run database migrations**
```bash
alembic upgrade head
```

6. **Start the development server**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Services Overview

### Core Services
- **Backend API**: `http://localhost:8000`
- **Celery Worker**: Background task processing
- **Celery Beat**: Scheduled task execution
- **Flower**: Celery monitoring at `http://localhost:5555`

### Database Services
- **PostgreSQL**: `localhost:5432`
- **Redis**: `localhost:6379`

## Configuration

### Environment Variables
Key configuration options in `.env`:

```env
# AI Configuration
GROK_API_KEY=your-grok-api-key
OPENAI_API_KEY=your-openai-fallback-key
AI_MODEL=grok-beta

# Database
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/flowmind_db

# External Integrations
GOOGLE_CLIENT_ID=your-google-client-id
ZOOM_API_KEY=your-zoom-api-key
```

### AI Model Configuration
- **Primary**: Grok LLM for advanced reasoning
- **Fallback**: OpenAI GPT-4 for reliability
- **Local**: Offline mode capability (planned)

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/refresh` - Token refresh

### Tasks
- `GET /api/v1/tasks` - List tasks with filtering
- `POST /api/v1/tasks` - Create task
- `POST /api/v1/tasks/natural-language` - Create task from natural language
- `PUT /api/v1/tasks/{id}` - Update task
- `POST /api/v1/tasks/{id}/complete` - Complete task

### AI Assistant
- `POST /api/v1/ai/chat` - Chat with AI assistant
- `POST /api/v1/ai/optimize-schedule` - AI schedule optimization
- `GET /api/v1/ai/insights` - Get productivity insights

### Calendar & Meetings
- `GET /api/v1/calendar/events` - List calendar events
- `POST /api/v1/meetings` - Create meeting
- `POST /api/v1/meetings/{id}/analyze` - AI meeting analysis

## AI Features

### Grok LLM Integration
```python
# Natural language task creation
task_data = await grok_service.parse_natural_language_task(
    "Prepare presentation for client meeting next Tuesday at 2 PM",
    user_id=user.id,
    user_context=user_preferences
)

# Schedule optimization
optimization = await grok_service.generate_schedule_optimization(
    user_id=user.id,
    tasks=user_tasks,
    events=calendar_events,
    preferences=user_settings
)
```

### Background AI Tasks
- **Daily Insights**: Productivity analysis and recommendations
- **Schedule Optimization**: Continuous schedule improvement
- **Meeting Analysis**: Automatic transcript processing
- **Habit Tracking**: Pattern recognition and suggestions

## Background Tasks

### Celery Tasks
- **AI Insights**: `generate_daily_productivity_insights`
- **Notifications**: `send_task_due_reminders`
- **Sync**: `sync_external_calendars`
- **Analytics**: `update_productivity_metrics`

### Scheduled Jobs
```python
# Every 15 minutes - Task reminders
"send-task-reminders": {
    "task": "app.tasks.notification_tasks.send_task_due_reminders",
    "schedule": crontab(minute="*/15"),
}

# Daily at 8 AM - AI insights
"generate-daily-insights": {
    "task": "app.tasks.ai_tasks.generate_daily_productivity_insights",
    "schedule": crontab(hour=8, minute=0),
}
```

## Security

### Authentication
- JWT tokens with refresh mechanism
- Password hashing with bcrypt
- Rate limiting and request validation

### Data Protection
- Encrypted sensitive data
- SQL injection prevention
- CORS and security headers
- Input validation and sanitization

## Monitoring & Analytics

### Logging
- Structured JSON logging
- Request correlation IDs
- Performance metrics
- Error tracking

### Health Checks
- Database connectivity
- Redis availability
- AI service status
- Background task monitoring

## Deployment

### Docker Deployment
```bash
# Production build
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up --scale celery_worker=3
```

### Kubernetes
```bash
# Deploy to Kubernetes
kubectl apply -f k8s/
```

## Testing

### Run Tests
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# API tests
pytest tests/api/
```

### Test Coverage
```bash
pytest --cov=app tests/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: GitHub Issues
- **Discord**: [Community Server](#)

---

**Built with ❤️ using FastAPI, Grok LLM, and modern Python**
