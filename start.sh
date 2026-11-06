#!/bin/bash
set -e

echo "=================================================="
echo " Starting FixLoop Operations & Repair Platform    "
echo "=================================================="

# Check Python environment
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtualenv..."
    python3 -m venv backend/venv
    ./backend/venv/bin/pip install -r backend/requirements.txt
fi

# Seed DB if not present
if [ ! -f "backend/fixloop.db" ]; then
    echo "Seeding initial benchmark demo database..."
    cd backend && ./venv/bin/python3 -m app.seed_data && cd ..
fi

echo "1. Starting FastAPI backend on http://localhost:8000..."
(cd backend && PYTHONPATH=. ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

echo "2. Starting Vite React frontend on http://localhost:5173..."
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID" EXIT

wait
