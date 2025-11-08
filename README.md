# DeepHat - AI Agent for Cybersecurity & DevOps

An intelligent AI assistant powered by LangGraph and the DeepHat model, specialized in cybersecurity and DevOps tasks with autonomous tool calling capabilities.

## 🏗️ Architecture

```
User Browser
     ↓
Next.js Frontend (Port 3000)
     ↓ HTTP/SSE
Python Backend (Port 8000)
     ↓ LangGraph Agent + Tools
HuggingFace API (DeepHat Model)
```

**Key Feature**: Frontend exclusively communicates with Python backend - no direct HuggingFace API calls from the browser.

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and pnpm
- Python 3.8+
- HuggingFace API key

### 1. Start Backend

```bash
cd backend
./dev.sh
```

Backend will start on http://localhost:8000

### 2. Start Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Frontend will start on http://localhost:3000

### 3. Test Integration

```bash
./test-integration.sh
```

## 🔧 Configuration

### Backend (`backend/.env`)
```env
HUGGINGFACE_API_KEY=your_key_here
HUGGINGFACE_MODEL=DeepHat/DeepHat-V1-7B
PORT=8000
```

### Frontend (`frontend/.env`)
```env
PYTHON_BACKEND_URL=http://localhost:8000
```

## 🛠️ Features

### AI Agent Capabilities
- **Autonomous Tool Calling**: Agent decides when to use tools
- **Security Scanning**: Vulnerability assessment
- **System Monitoring**: Service status checks
- **Log Analysis**: Error detection and analysis
- **Configuration Deployment**: Automated deployments

### Technical Features
- **Hot Reload**: Both frontend and backend support live reloading
- **Streaming Responses**: Real-time SSE streaming
- **Retry Logic**: Automatic retry for model loading
- **Error Handling**: User-friendly error messages
- **API Documentation**: Interactive docs at `/docs`

## 📚 Documentation

- **[SETUP.md](frontend/SETUP.md)** - Detailed setup instructions
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture details
- **[backend/README.md](backend/README.md)** - Backend documentation

## 🧪 Testing

### Test Backend Directly
```bash
# Health check
curl http://localhost:8000/health

# Chat request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Scan my web application"}'
```

### Test Full Integration
```bash
./test-integration.sh
```

## 🔐 Security

- ✅ API keys stored only in backend
- ✅ Frontend never accesses HuggingFace directly
- ✅ CORS protection enabled
- ✅ Environment variables for sensitive data

## 🎯 Example Queries

Try these to see the agent in action:

- "Scan my web application for vulnerabilities"
- "Check the status of the nginx service"
- "Analyze the application logs for errors"
- "Deploy the production config to staging environment"

## 🛠️ Development

### Adding New Tools

Edit `backend/agent.py`:

```python
TOOLS = {
    "your_tool": {
        "description": "What your tool does",
        "parameters": ["param1"],
        "function": lambda param1: f"Result: {param1}"
    }
}
```

### Project Structure

```
cmatrix/
├── frontend/              # Next.js app
│   ├── app/api/chat/     # API route (proxies to backend)
│   └── .env              # Frontend config
├── backend/              # Python app
│   ├── app.py           # FastAPI server
│   ├── agent.py         # LangGraph agent
│   └── .env             # Backend config (API keys)
├── ARCHITECTURE.md      # Architecture details
└── README.md           # This file
```

## 🐛 Troubleshooting

### "Cannot connect to Python backend"
- Ensure backend is running: `cd backend && ./dev.sh`
- Check: `curl http://localhost:8000/health`

### "Model is loading"
- First request takes 15-30 seconds (cold start)
- Backend automatically retries
- Subsequent requests are fast

### Port conflicts
```bash
# Kill process on port 8000
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

## 📊 API Endpoints

### Backend (Port 8000)
- `GET /` - API info
- `GET /health` - Health check
- `POST /chat` - Non-streaming chat
- `POST /chat/stream` - Streaming chat
- `GET /docs` - Interactive API docs

### Frontend (Port 3000)
- `POST /api/chat` - Chat endpoint (proxies to backend)

## 🌟 Tech Stack

- **Frontend**: Next.js 16, React 19, TypeScript
- **Backend**: FastAPI, Python 3.11
- **AI Framework**: LangGraph, LangChain
- **Model**: DeepHat-V1-7B (via HuggingFace)
- **Streaming**: Server-Sent Events (SSE)

## 📝 License

This project is for educational and development purposes.

## 🤝 Contributing

1. Add new tools in `backend/agent.py`
2. Update frontend UI as needed
3. Test with `./test-integration.sh`
4. Document changes

## 🔗 Links

- **Backend API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **HuggingFace Model**: DeepHat/DeepHat-V1-7B

---

Built with ❤️ using LangGraph, FastAPI, and Next.js
