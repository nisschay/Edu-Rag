#!/bin/bash

# Education RAG - Stop Script
# Stops both backend and frontend servers

echo "🛑 Stopping Education RAG System"
echo "================================="
echo ""

# Function to stop process by pattern
stop_process() {
    local pattern="$1"
    local name="$2"
    
    pids=$(pgrep -f "$pattern" 2>/dev/null)
    
    if [ -n "$pids" ]; then
        echo "Stopping $name (PIDs: $pids)..."
        pkill -f "$pattern" 2>/dev/null
        sleep 1
        
        # Force kill if still running
        pids=$(pgrep -f "$pattern" 2>/dev/null)
        if [ -n "$pids" ]; then
            echo "Force killing $name..."
            pkill -9 -f "$pattern" 2>/dev/null
        fi
        echo "✅ $name stopped"
    else
        echo "ℹ️  $name not running"
    fi
}

# Stop backend (uvicorn)
stop_process "uvicorn app.main:app" "Backend (uvicorn)"

# Stop frontend (vite)
stop_process "vite" "Frontend (vite)"

# Also try node for frontend
stop_process "node.*vite" "Frontend (node/vite)"

echo ""
echo "================================="
echo "✅ All Education RAG services stopped"
echo ""

# Verify nothing is running on the ports
if lsof -i :8000 > /dev/null 2>&1; then
    echo "⚠️  Warning: Something still running on port 8000"
    lsof -i :8000 | head -5
else
    echo "✅ Port 8000 is free"
fi

if lsof -i :5173 > /dev/null 2>&1; then
    echo "⚠️  Warning: Something still running on port 5173"
    lsof -i :5173 | head -5
else
    echo "✅ Port 5173 is free"
fi

echo ""
