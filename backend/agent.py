import os
import re
import requests
from typing import TypedDict, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Define tools for the agent
TOOLS = {
    "security_scan": {
        "description": "Perform a security scan on a target system or application",
        "parameters": ["target"],
        "function": lambda target: f"Security scan completed for {target}. Found 3 medium-risk vulnerabilities: outdated dependencies, missing CORS headers, weak password policy."
    },
    "check_system_status": {
        "description": "Check the status of a system service or application",
        "parameters": ["service_name"],
        "function": lambda service_name: f"Service '{service_name}' is running. CPU: 45%, Memory: 2.3GB, Uptime: 7 days."
    },
    "analyze_logs": {
        "description": "Analyze logs from a specified source for errors or anomalies",
        "parameters": ["log_source"],
        "function": lambda log_source: f"Analyzed logs from {log_source}. Found 12 errors in the last hour, mostly connection timeouts to external API."
    },
    "deploy_config": {
        "description": "Deploy a configuration to a specified environment",
        "parameters": ["environment", "config_name"],
        "function": lambda environment, config_name: f"Configuration '{config_name}' successfully deployed to {environment} environment. Rollback available if needed."
    }
}

# Agent state
class AgentState(TypedDict):
    messages: Sequence[BaseMessage]
    tool_calls: list

def create_tool_prompt():
    """Create a prompt describing available tools."""
    tool_descriptions = []
    for name, info in TOOLS.items():
        params = ", ".join(info["parameters"])
        tool_descriptions.append(f"- {name}({params}): {info['description']}")
    
    return f"""You have access to the following tools:

{chr(10).join(tool_descriptions)}

To use a tool, respond with: TOOL_CALL: tool_name(param1, param2, ...)
You can call multiple tools by using multiple TOOL_CALL lines.
After tool results, provide your final answer to the user."""

def parse_tool_calls(text: str) -> list:
    """Parse tool calls from LLM response."""
    tool_calls = []
    pattern = r'TOOL_CALL:\s*(\w+)\((.*?)\)'
    matches = re.findall(pattern, text, re.IGNORECASE)
    
    for tool_name, params_str in matches:
        if tool_name in TOOLS:
            # Parse parameters
            params = [p.strip().strip('"\'') for p in params_str.split(',') if p.strip()]
            tool_calls.append({"name": tool_name, "params": params})
    
    return tool_calls

def execute_tools(tool_calls: list) -> str:
    """Execute tool calls and return results."""
    results = []
    for call in tool_calls:
        tool_name = call["name"]
        params = call["params"]
        
        if tool_name in TOOLS:
            try:
                result = TOOLS[tool_name]["function"](*params)
                results.append(f"[{tool_name}] {result}")
            except Exception as e:
                results.append(f"[{tool_name}] Error: {str(e)}")
    
    return "\n".join(results) if results else "No tools executed."

class HuggingFaceLLM:
    """Custom LLM wrapper for HuggingFace Router API with chat completions."""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        model_name = model or os.getenv("HUGGINGFACE_MODEL", "DeepHat/DeepHat-V1-7B")
        
        # Add provider suffix for DeepHat model if not present
        if "DeepHat" in model_name and ":featherless-ai" not in model_name:
            self.model = f"{model_name}:featherless-ai"
        else:
            self.model = model_name
        
        # Use chat completions endpoint for all models
        self.endpoint = "https://router.huggingface.co/v1/chat/completions"
        
        print(f"🤖 Using model: {self.model}")
        print(f"📡 Endpoint: {self.endpoint}")
    
    def invoke(self, prompt: str, max_retries: int = 3) -> str:
        """Call the HuggingFace API using chat completions format with retry logic."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Use chat completions format for all models
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are DeepHat, created by Kindo.ai. You are a helpful assistant that is an expert in Cybersecurity and DevOps."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 512,
            "temperature": 0.7,
            "stream": False
        }
        
        import time
        
        for attempt in range(max_retries):
            try:
                response = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                
                result = response.json()
                
                # OpenAI-compatible format
                return result["choices"][0]["message"]["content"]
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 503:
                    # Model is loading, wait and retry
                    wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                    print(f"⏳ Model loading... Retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                    
                    if attempt < max_retries - 1:
                        time.sleep(wait_time)
                        continue
                    else:
                        print(f"❌ Model still unavailable after {max_retries} attempts")
                        raise Exception("Model is loading. Please try again in a moment.")
                else:
                    print(f"❌ HTTP Error {e.response.status_code}: {str(e)}")
                    if hasattr(e, 'response') and e.response is not None:
                        print(f"Response: {e.response.text}")
                    raise
            
            except requests.exceptions.RequestException as e:
                print(f"❌ Error calling HuggingFace API: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    print(f"Response: {e.response.text}")
                raise

# Initialize LLM
def create_agent():
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    if not api_key:
        raise ValueError("HUGGINGFACE_API_KEY not found in environment variables")
    
    llm = HuggingFaceLLM(api_key=api_key)
    
    def should_continue(state: AgentState) -> Literal["tools", "end"]:
        """Decide whether to use tools or end."""
        last_message = state["messages"][-1]
        if isinstance(last_message, AIMessage):
            tool_calls = parse_tool_calls(last_message.content)
            if tool_calls:
                return "tools"
        return "end"
    
    def call_model(state: AgentState):
        """Call the LLM."""
        messages = state["messages"]
        
        # Build prompt with tool information
        if len(messages) == 1 or not any("TOOL_RESULT" in str(m.content) for m in messages):
            tool_prompt = create_tool_prompt()
            system_msg = SystemMessage(content=f"You are DeepHat, created by Kindo.ai. You are a helpful assistant that is an expert in Cybersecurity and DevOps.\n\n{tool_prompt}")
            prompt_messages = [system_msg] + list(messages)
        else:
            prompt_messages = messages
        
        # Convert to string prompt for HuggingFace
        prompt_text = "\n".join([f"{m.type}: {m.content}" for m in prompt_messages])
        response = llm.invoke(prompt_text)
        
        return {"messages": [AIMessage(content=response)]}
    
    def call_tools(state: AgentState):
        """Execute tools and add results to messages."""
        last_message = state["messages"][-1]
        tool_calls = parse_tool_calls(last_message.content)
        
        if tool_calls:
            results = execute_tools(tool_calls)
            return {"messages": [HumanMessage(content=f"TOOL_RESULTS:\n{results}\n\nNow provide your final answer based on these results.")]}
        
        return {"messages": []}
    
    # Build graph
    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", call_tools)
    
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

# Create agent instance
agent_executor = create_agent()

def clean_response(content: str) -> str:
    """Clean up the response by removing tool call syntax and extra whitespace."""
    if not content:
        return ""
    
    # Remove TOOL_CALL lines
    lines = content.split('\n')
    cleaned_lines = []
    skip_next = False
    
    for line in lines:
        # Skip TOOL_CALL lines
        if re.match(r'^\s*TOOL_CALL:', line, re.IGNORECASE):
            continue
        # Skip TOOL_RESULTS section header
        if re.match(r'^\s*TOOL_RESULTS:', line, re.IGNORECASE):
            skip_next = True
            continue
        # Skip the instruction line after TOOL_RESULTS
        if skip_next and "provide your final answer" in line.lower():
            skip_next = False
            continue
        
        cleaned_lines.append(line)
    
    # Join and clean up extra whitespace
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n{3,}', '\n\n', result)  # Max 2 consecutive newlines
    result = result.strip()
    
    return result

def run_agent(message: str, history: list = None):
    """Run the agent with a message and optional history."""
    messages = []
    
    # Add history
    if history:
        for msg in history:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
    
    # Add current message
    messages.append(HumanMessage(content=message))
    
    try:
        # Run agent
        result = agent_executor.invoke({"messages": messages, "tool_calls": []})
        
        # Extract final response
        final_message = result["messages"][-1]
        content = final_message.content if hasattr(final_message, 'content') else str(final_message)
        
        # Clean up the response
        cleaned_content = clean_response(content)
        
        print('✅ Agent response:', cleaned_content[:200] + '...' if len(cleaned_content) > 200 else cleaned_content)
        
        return cleaned_content
    
    except Exception as e:
        print(f"❌ Error in run_agent: {str(e)}")
        raise
