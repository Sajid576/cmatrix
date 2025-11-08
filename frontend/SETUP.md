# DeepHat Project Setup Guide

This project consists of a Next.js frontend and a Python backend with LangGraph for agentic AI behavior.

## Architecture

```
┌─────────────────┐      HTTP/SSE      ┌──────────────────┐
│   Next.js App   │ ◄─────────────────► │  Python Backend  │
│   (Frontend)    │                     │   (LangGraph)    │
└─────────────────┘                     └──────────────────┘
        │                                        │
        │                                        │
        ▼                                        ▼
  Port 3000                              Port 8000
                                    (FastAPI + LangGraph)
```

## Quick Start

### 1. Start Python Backend

```bash
cd backend
./start.sh
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
# From project root
pnpm install
pnpm dev
```

The frontend will start on `http://localhost:3000`

## Configuration

### Environment Variables

The `.env` file controls the backend connection:

```env
HUGGINGFACE_API_KEY=your_key_here
USE_PYTHON_BACKEND=true          # Set to false to use direct HuggingFace API
PYTHON_BACKEND_URL=http://localhost:8000
```

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

### Python Backend

- `GET /` - API information
- `GET /health` - Health check
- `POST /chat` - Non-streaming chat
- `POST /chat/stream` - Streaming chat (used by frontend)

### Next.js API

- `POST /api/chat` - Proxies to Python backend or HuggingFace

## Development

### Adding New Tools

Edit `backend/agent.py`:

```python
@tool
def your_tool(param: str) -> str:
    """Tool description for the LLM."""
    # Your logic here
    return "Result"

# Add to tools list
tools = [security_scan, check_system_status, analyze_logs, deploy_config, your_tool]
```

### Testing Backend Directly

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Check nginx status"}'
```

## Troubleshooting

### Backend won't start
- Ensure Python 3.8+ is installed
- Check if port 8000 is available
- Verify HuggingFace API key in `backend/.env`

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check `USE_PYTHON_BACKEND=true` in `.env`
- Verify CORS settings in `backend/app.py`

### Agent not using tools
- Check tool descriptions are clear
- Verify LangGraph installation
- Review backend logs for errors
