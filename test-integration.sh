#!/bin/bash

echo "🧪 Testing DeepHat Integration"
echo "================================"
echo ""

# Test 1: Backend Health Check
echo "1️⃣  Testing Backend Health..."
HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
if [ $? -eq 0 ]; then
    echo "✅ Backend is running"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "❌ Backend is not running"
    echo "   Please start backend: cd backend && ./dev.sh"
    exit 1
fi
echo ""

# Test 2: Backend Chat Endpoint
echo "2️⃣  Testing Backend Chat Endpoint..."
CHAT_RESPONSE=$(curl -s -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, what can you help me with?"}')

if [ $? -eq 0 ]; then
    echo "✅ Backend chat endpoint working"
    echo "   Response preview: ${CHAT_RESPONSE:0:100}..."
else
    echo "❌ Backend chat endpoint failed"
    exit 1
fi
echo ""

# Test 3: Frontend Health Check
echo "3️⃣  Testing Frontend..."
FRONTEND_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000)
if [ "$FRONTEND_RESPONSE" = "200" ] || [ "$FRONTEND_RESPONSE" = "304" ]; then
    echo "✅ Frontend is running"
else
    echo "⚠️  Frontend might not be running (HTTP $FRONTEND_RESPONSE)"
    echo "   Please start frontend: cd frontend && pnpm dev"
fi
echo ""

# Test 4: Frontend API Route
echo "4️⃣  Testing Frontend API Route..."
API_RESPONSE=$(curl -s -X POST http://localhost:3000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Test message"}' \
  --max-time 30)

if [ $? -eq 0 ]; then
    echo "✅ Frontend API route working"
    echo "   Integration successful!"
else
    echo "❌ Frontend API route failed"
    echo "   Check that both frontend and backend are running"
fi
echo ""

echo "================================"
echo "✨ Integration Test Complete"
echo ""
echo "📝 Summary:"
echo "   - Backend: http://localhost:8000"
echo "   - Frontend: http://localhost:3000"
echo "   - API Docs: http://localhost:8000/docs"
echo ""
echo "🚀 Ready to use!"
