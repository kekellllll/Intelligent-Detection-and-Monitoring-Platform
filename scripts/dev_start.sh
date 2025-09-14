#!/bin/bash

# Development startup script

echo "Starting Intelligent Detection and Monitoring Platform in development mode..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Set development environment
export ENV_FILE=.env.dev

# Start development services
echo "Starting development services (Redis, Kafka, PostgreSQL)..."
docker-compose up -d db redis kafka zookeeper

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 10

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

# Start the application
echo "Starting the application..."
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000