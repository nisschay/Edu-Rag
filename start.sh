#!/bin/bash

# Education RAG - Complete Startup Script
# Starts both backend and frontend servers

echo "🚀 Starting Education RAG System"
echo "================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment not found!"
    echo "   Please run: python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "   Creating .env from .env.example..."
    cp .env.example .env 2>/dev/null || echo "   Please create .env file with OPENAI_API_KEY"
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    cd frontend && npm install && cd ..
fi

# Kill existing servers
echo "🛑 Stopping any existing servers..."
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null
sleep 2

# Start backend
echo ""
echo "🔧 Starting backend server..."
source venv/bin/activate
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"
echo "   Log: backend.log"

# Wait for backend to start
echo "   Waiting for backend to be ready..."
sleep 3

# Test backend
if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
    echo "   ✅ Backend running at http://localhost:8000"
else
    echo "   ❌ Backend failed to start. Check backend.log"
    exit 1
fi

# Start frontend
echo ""
echo "🎨 Starting frontend server..."
cd frontend
nohup npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   Frontend PID: $FRONTEND_PID"
echo "   Log: frontend.log"

# Wait for frontend to start
echo "   Waiting for frontend to be ready..."
sleep 5

if tail -10 frontend.log | grep -q "Local:"; then
    echo "   ✅ Frontend running at http://localhost:5173"
else
    echo "   ⚠️  Frontend may still be starting. Check frontend.log"
fi

echo ""
echo "========================================="
echo "✅ Education RAG is running!"
echo ""
echo "📍 URLs:"
echo "   Frontend UI:  http://localhost:5173"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo ""
echo "📝 Process IDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "📊 Logs:"
echo "   Backend:  tail -f backend.log"
echo "   Frontend: tail -f frontend.log"
echo ""
echo "🛑 To stop:"
echo "   pkill -f uvicorn"
echo "   pkill -f vite"
echo ""
echo "🧪 To create test data:"
echo "   ./create_test_data.sh"
echo ""
