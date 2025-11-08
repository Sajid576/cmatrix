# DeepHat Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         User Browser                         │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ HTTP/WebSocket
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Next.js Frontend (Port 3000)              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  /app/api/chat/route.ts                              │   │
│  │  - Receives user messages                            │   │
│  │  - Forwards to Python backend                        │   │
│  │  - Streams responses back to user                    │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ HTTP POST /chat/stream
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Python Backend (Port 8000)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (app.py)                             │   │
│  │  - Receives requests from frontend                   │   │
│  │  - Manages agent execution                           │   │
│  │  - Streams responses                                 │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  LangGraph Agent (agent.py)                          │   │
│  │  - Processes user queries                            │   │
│  │  - Decides when to use tools                         │   │
│  │  - Executes tool calls                               │   │
│  │  - Formats responses                                 │   │
│  └────────────────────┬─────────────────────────────────┘   │
│                       │                                      │
│                       ▼                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Tools                                               │   │
│  │  - security_scan()                                   │   │
│  │  - check_system_status()                             │   │
│  │  - analyze_logs()                                    │   │
│  │  - deploy_config()                                   │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
                             │ HTTPS API Call
                             ▼
┌─────────────────────────────────────────────────────────────┐
│              HuggingFace Router API                          │
│  Model: DeepHat/DeepHat-V1-7B:featherless-ai                │
└─────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. User Sends Message
```
User → Next.js Frontend → /api/chat (POST)
```

### 2. Frontend Forwards to Backend
```
Next.js → Python Backend → /chat/stream (POST)
Payload: { message: string, history: array }
```

### 3. Backend Processes with Agent
```
Python Backend → LangGraph Agent
  ├─ Analyzes message
  ├─ Decides if tools needed
  ├─ Calls HuggingFace API
  └─ Returns formatted response
```

### 4. Response Streams Back
```
Python Backend → Next.js → User Browser
Format: Server-Sent Events (SSE)
```

## Key Components

### Frontend (Next.js)
- **Location**: `frontend/`
- **Port**: 3000
- **Role**: User interface and API proxy
- **Key File**: `frontend/app/api/chat/route.ts`
- **Environment**: `frontend/.env`

### Backend (Python)
- **Location**: `backend/`
- **Port**: 8000
- **Role**: AI agent orchestration and tool execution
- **Key Files**:
  - `backend/app.py` - FastAPI server
  - `backend/agent.py` - LangGraph agent with tools
- **Environment**: `backend/.env`

## Security & Configuration

### API Keys
- **HuggingFace API Key**: Only stored in `backend/.env`
- **Frontend**: No API keys needed (proxies through backend)

### CORS
- Backend allows requests from `localhost:3000` and `localhost:3001`
- Configured in `backend/app.py`

### Environment Variables

**Frontend** (`frontend/.env`):
```env
PYTHON_BACKEND_URL=http://localhost:8000
```

**Backend** (`backend/.env`):
```env
HUGGINGFACE_API_KEY=your_key_here
HUGGINGFACE_MODEL=DeepHat/DeepHat-V1-7B
PORT=8000
```

## Starting the Application

### Development Mode

1. **Start Backend** (Terminal 1):
```bash
cd backend
./dev.sh
```

2. **Start Frontend** (Terminal 2):
```bash
cd frontend
pnpm dev
```

3. **Access Application**:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Communication Protocol

### Request Format
```json
{
  "message": "User's question",
  "history": [
    { "role": "user", "content": "Previous message" },
    { "role": "assistant", "content": "Previous response" }
  ]
}
```

### Response Format (SSE)
```
data: {"token": "word "}
data: {"token": "by "}
data: {"token": "word"}
data: [DONE]
```

### Error Format
```
data: {"error": "Error message"}
```

## Agent Workflow

1. **Receive Message**: User query arrives at agent
2. **Analyze Intent**: Determine if tools are needed
3. **Tool Execution**: If needed, execute relevant tools
4. **Generate Response**: Call LLM with context
5. **Format Output**: Clean and format response
6. **Stream Back**: Send to frontend via SSE

## Benefits of This Architecture

✅ **Security**: API keys never exposed to frontend
✅ **Flexibility**: Easy to add new tools without frontend changes
✅ **Scalability**: Backend can be deployed independently
✅ **Monitoring**: Centralized logging in backend
✅ **Caching**: Can add caching layer in backend
✅ **Rate Limiting**: Control API usage in backend
✅ **Tool Calling**: Advanced AI capabilities with LangGraph

## Troubleshooting

### Frontend can't connect to backend
- Ensure backend is running on port 8000
- Check `PYTHON_BACKEND_URL` in `frontend/.env`
- Verify CORS settings in `backend/app.py`

### Backend errors
- Check HuggingFace API key in `backend/.env`
- View logs in backend terminal
- Test backend directly: `curl http://localhost:8000/health`

### Model loading slowly
- First request may take 15-30 seconds (cold start)
- Subsequent requests are fast
- Backend has automatic retry logic
