import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import json
import asyncio
import importlib

load_dotenv()

app = FastAPI(
    title="DeepHat Agent API",
    description="AI Agent with LangGraph and tool calling",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: list = []

class ChatResponse(BaseModel):
    response: str

def get_agent():
    """Dynamically import agent to support hot reloading."""
    import agent
    importlib.reload(agent)
    return agent.run_agent

@app.get("/")
async def root():
    return {
        "message": "DeepHat Agent API is running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/chat",
            "stream": "/chat/stream"
        }
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "DeepHat Agent API"
    }

@app.post("/chat")
async def chat(request: ChatRequest):
    """Non-streaming chat endpoint."""
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        run_agent = get_agent()
        response = run_agent(request.message, request.history)
        return ChatResponse(response=response)
    
    except Exception as e:
        print(f"Error in /chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streaming chat endpoint."""
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        async def generate():
            try:
                run_agent = get_agent()
                response = run_agent(request.message, request.history)
                
                print('response:', response)
                
                # Simulate streaming by sending chunks
                words = response.split()
                for i, word in enumerate(words):
                    chunk = word + (" " if i < len(words) - 1 else "")
                    yield f"data: {json.dumps({'token': chunk})}\n\n"
                    await asyncio.sleep(0.05)
                
                yield "data: [DONE]\n\n"
            
            except Exception as e:
                print(f"Error in /chat/stream: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
    
    except Exception as e:
        print(f"Error in /chat/stream endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    
    print(f"🚀 Starting DeepHat Agent API on port {port}")
    print(f"📝 Hot reload enabled - code changes will auto-reload")
    print(f"🔗 API docs available at http://localhost:{port}/docs")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        reload_dirs=["./"],
        log_level="info"
    )
