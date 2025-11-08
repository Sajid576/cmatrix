# DeepHat Project Setup Guide

This project consists of a Next.js frontend and a Python backend with LangGraph for agentic AI behavior.

## Architecture

```
┌─────────────────┐                    ┌──────────────────┐                    ┌─────────────────┐
│   Next.js App   │ ──────────────────► │  Python Backend  │ ──────────────────► │  HuggingFace    │
│   (Frontend)    │   HTTP/SSE          │   (LangGraph)    │   HTTPS API         │     API         │
│   Port 3000     │                     │   Port 8000      │                     │                 │
└─────────────────┘                    └──────────────────┘                    └─────────────────┘

🔒 Frontend ONLY talks to Python Backend (never directly to HuggingFace)
```

## Quick Start

### 1. Start Python Backend (Required)

```bash
cd backend
./dev.sh
```

Or manually:
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

The backend will start on `http://localhost:8000`

### 2. Start Next.js Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend will start on `http://localhost:3000`

## Configuration

### Frontend Environment Variables

**File**: `frontend/.env`

```env
# Python Backend URL (required)
PYTHON_BACKEND_URL=http://localhost:8000
```

**Note**: The frontend does NOT need a HuggingFace API key. All AI requests go through the Python backend.

### Backend Environment Variables

**File**: `backend/.env`

```env
# HuggingFace API Key (required)
HUGGINGFACE_API_KEY=your_key_here

# Model to use
HUGGINGFACE_MODEL=DeepHat/DeepHat-V1-7B

# Server port
PORT=8000
```

## How It Works

### Request Flow

1. **User** sends message in browser
2. **Next.js Frontend** receives message at `/api/chat`
3. **Frontend** forwards to Python backend at `http://localhost:8000/chat/stream`
4. **Python Backend** processes with LangGraph agent
5. **Agent** calls HuggingFace API with tools
6. **Backend** streams response back to frontend
7. **Frontend** displays response to user

### Why This Architecture?

✅ **Security**: API keys never exposed to browser  
✅ **Tool Calling**: Advanced AI capabilities with LangGraph  
✅ **Flexibility**: Easy to add new tools without frontend changes  
✅ **Monitoring**: Centralized logging and error handling  
✅ **Rate Limiting**: Control API usage in one place  

## Python Backend Features

### LangGraph Agent with Tools

The agent has access to these tools:

1. **security_scan(target)** - Perform security scans
2. **check_system_status(service_name)** - Monitor system services  
3. **analyze_logs(log_source)** - Analyze logs for errors
4. **deploy_config(environment, config_name)** - Deploy configurations

### Example Queries

Try these to see the agent use tools:

- "Scan my web application for vulnerabilities"
- "Check the status of the nginx service"
- "Analyze the application logs for errors"
- "Deploy the production config to staging"

## API Endpoints

### Python Backend (Port 8000)

- `GET /` - API information
- `GET /health` - Health check
- `POST /chat` - Non-streaming chat
- `POST /chat/stream` - Streaming chat (used by frontend)
- `GET /docs` - Interactive API documentation

### Next.js Frontend (Port 3000)

- `POST /api/chat` - Chat endpoint (proxies to Python backend)

## Development

### Hot Reload

Both frontend and backend support hot reload:

- **Frontend**: Edit any file in `frontend/` and see changes instantly
- **Backend**: Edit `agent.py` or `app.py` and server auto-reloads

### Adding New Tools

Edit `backend/agent.py`:

```python
TOOLS = {
    "your_tool": {
        "description": "What your tool does",
        "parameters": ["param1", "param2"],
        "function": lambda param1, param2: f"Result: {param1}, {param2}"
    }
}
```

The agent will automatically have access to the new tool!

### Testing Backend Directly

```bash
# Health check
curl http://localhost:8000/health

# Chat request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check nginx status"}'

# Streaming chat
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Scan my app"}' \
  --no-buffer
```

## Troubleshooting

### Frontend shows "Cannot connect to Python backend"

**Solution**:
1. Ensure backend is running: `cd backend && ./dev.sh`
2. Check backend is on port 8000: `curl http://localhost:8000/health`
3. Verify `PYTHON_BACKEND_URL` in `frontend/.env`

### Backend won't start

**Solution**:
- Ensure Python 3.8+ is installed: `python3 --version`
- Check if port 8000 is available: `lsof -ti:8000`
- Verify HuggingFace API key in `backend/.env`
- Check dependencies: `cd backend && pip install -r requirements.txt`

### "Model is loading" error

**Solution**:
- First request may take 15-30 seconds (cold start)
- Backend automatically retries with increasing delays
- Subsequent requests will be fast
- Wait for the model to load, then try again

### Agent not using tools

**Solution**:
- Check tool descriptions are clear in `backend/agent.py`
- Verify LangGraph installation: `pip list | grep langgraph`
- Review backend logs for errors
- Try more explicit queries: "Use the security_scan tool on example.com"

### CORS errors

**Solution**:
- Backend CORS is configured for `localhost:3000` and `localhost:3001`
- If using different port, update `backend/app.py` CORS settings

## Project Structure

```
cmatrix/
├── frontend/                 # Next.js application
│   ├── app/
│   │   └── api/
│   │       └── chat/
│   │           └── route.ts  # Proxies to Python backend
│   ├── .env                  # Frontend config (backend URL only)
│   └── package.json
│
└── backend/                  # Python application
    ├── app.py               # FastAPI server
    ├── agent.py             # LangGraph agent with tools
    ├── requirements.txt     # Python dependencies
    ├── .env                 # Backend config (API keys)
    ├── dev.sh              # Development startup script
    └── README.md
```

## Additional Resources

- **Backend API Docs**: http://localhost:8000/docs (when backend is running)
- **Architecture Details**: See `ARCHITECTURE.md`
- **Backend README**: See `backend/README.md`

## Security Notes

🔒 **API Key Security**:
- HuggingFace API key is ONLY in `backend/.env`
- Never commit `.env` files to git
- Frontend has no access to API keys
- All AI requests go through backend

🔒 **CORS Protection**:
- Backend only accepts requests from localhost:3000/3001
- Update CORS settings for production deployment
