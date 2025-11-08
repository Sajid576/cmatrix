#!/bin/bash

echo "🔥 Starting DeepHat Agent Backend in DEV MODE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "📥 Checking dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies ready"
echo ""

# Start the server with hot reload
echo "🚀 Server starting on http://localhost:8000"
echo "📚 API docs at http://localhost:8000/docs"
echo "💡 Hot reload is ACTIVE - edit agent.py or app.py to see changes"
echo "🛑 Press Ctrl+C to stop"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run with uvicorn directly for better hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000 --log-level info
