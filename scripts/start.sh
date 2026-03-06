#!/bin/bash

# Detect project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( dirname "$SCRIPT_DIR" )"
cd "$PROJECT_ROOT"

# Setup environment
export PYTHONPATH=$PYTHONPATH:$(pwd)
source venv/bin/activate

echo "Starting Voice AI Agent from $PROJECT_ROOT..."

# Run database seeder
python3 scripts/seed_db.py

# Start the server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
