#!/bin/bash

echo "🚀 Starting DeepHat Agent Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt

# Start the server with hot reload
echo "🔥 Starting FastAPI server with hot reload on port 8000..."
echo "💡 Make changes to agent.py or app.py and they'll auto-reload!"
echo ""
python app.py
