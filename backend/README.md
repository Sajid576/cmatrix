# DeepHat Agent Backend

Python backend with LangGraph for agentic AI behavior with tool calling capabilities.

## Features

- **LangGraph Agent**: Autonomous agent with tool calling
- **Custom Tools**: Security scanning, system monitoring, log analysis, deployment
- **FastAPI**: High-performance async API
- **Streaming Support**: Real-time response streaming
- **HuggingFace Integration**: Uses DeepHat model
- **Hot Reload**: Auto-reload on code changes during development

## Quick Start

### Development Mode (with hot reload)
```bash
cd backend
./dev.sh
```

### Production Mode
```bash
cd backend
./start.sh
```

The server will start on `http://localhost:8000`

## Development

### Hot Reload
When running in dev mode (`./dev.sh`), the server automatically reloads when you:
- Edit `agent.py` (modify tools, agent logic)
- Edit `app.py` (modify API endpoints)
- Change any Python file in the directory

No need to restart the server manually!

### API Documentation
Visit `http://localhost:8000/docs` for interactive API documentation (Swagger UI)

## API Endpoints

- `GET /` - API info and available endpoints
- `GET /health` - Health check
- `POST /chat` - Non-streaming chat
- `POST /chat/stream` - Streaming chat (used by frontend)

## Available Tools

The agent has access to these tools:

1. **security_scan(target)** - Perform security scans on systems
2. **check_system_status(service_name)** - Monitor system services
3. **analyze_logs(log_source)** - Analyze logs for errors and anomalies
4. **deploy_config(environment, config_name)** - Deploy configurations

## Adding New Tools

Edit `backend/agent.py` and add to the `TOOLS` dictionary:

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

## Example Requests

### Using curl
```bash
# Non-streaming
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Scan my web application for vulnerabilities"}'

# Streaming
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "Check nginx status"}' \
  --no-buffer
```

### Example Queries
Try these to see the agent use tools:

- "Scan my web application for vulnerabilities"
- "Check the status of the nginx service"
- "Analyze the application logs for errors"
- "Deploy the production config to staging environment"

## Project Structure

```
backend/
├── app.py              # FastAPI server with hot reload
├── agent.py            # LangGraph agent and tools
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── dev.sh             # Development startup script
├── start.sh           # Production startup script
└── README.md          # This file
```

## Environment Variables

Create a `.env` file:

```env
HUGGINGFACE_API_KEY=your_key_here
PORT=8000

# Choose your model (optional, defaults to Llama-3.2-3B-Instruct)
HUGGINGFACE_MODEL=meta-llama/Llama-3.2-3B-Instruct
```

### Supported Models

The backend uses HuggingFace's router API which supports various models:

- `meta-llama/Llama-3.2-3B-Instruct` (default) - Fast and efficient
- `meta-llama/Llama-3.1-8B-Instruct` - More capable, slower
- `mistralai/Mistral-7B-Instruct-v0.3` - Good balance
- `Qwen/Qwen2.5-7B-Instruct` - Alternative option

You can change the model by updating `HUGGINGFACE_MODEL` in `.env`

## Troubleshooting

### Port already in use
```bash
# Find and kill process on port 8000
lsof -ti:8000 | xargs kill -9
```

### Hot reload not working
- Make sure you're using `./dev.sh` not `./start.sh`
- Check that uvicorn is installed: `pip install uvicorn[standard]`

### Agent not responding
- Check HuggingFace API key in `.env`
- View logs in the terminal for error messages
- Test the `/health` endpoint: `curl http://localhost:8000/health`

### Dependencies issues
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
