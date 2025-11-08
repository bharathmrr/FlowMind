-- AI LifeOS FlowMind Database Initialization
-- This script sets up the initial database configuration

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create indexes for better performance
-- These will be created by SQLAlchemy, but we can add custom ones here

-- Full-text search indexes
-- CREATE INDEX IF NOT EXISTS idx_tasks_search ON tasks USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
-- CREATE INDEX IF NOT EXISTS idx_meetings_search ON meetings USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Performance indexes
-- CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(user_id, status);
-- CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date) WHERE due_date IS NOT NULL;
-- CREATE INDEX IF NOT EXISTS idx_events_time_range ON events(start_time, end_time);

-- Initial data setup will be handled by the application
SELECT 'AI LifeOS FlowMind database initialized' as message;
