#!/bin/bash
# Quick start script for NBA Analytics

echo "🚀 Starting NBA Analytics Platform..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Create it with: python3 -m venv venv"
    exit 1
fi

# Start backend
echo "📡 Starting backend server..."
source venv/bin/activate
uvicorn app.main:app --reload &
BACKEND_PID=$!
echo "   Backend running at http://127.0.0.1:8000 (PID: $BACKEND_PID)"
echo ""

# Wait a moment for backend to start
sleep 2

# Start frontend
echo "🎨 Starting frontend server..."
cd frontend
npm run dev &
FRONTEND_PID=$!
echo "   Frontend running at http://localhost:5173 (PID: $FRONTEND_PID)"
echo ""

echo "✅ Both servers started!"
echo ""
echo "To stop both servers, run:"
echo "  kill $BACKEND_PID $FRONTEND_PID"
echo ""
echo "Or press Ctrl+C and manually stop each server"
