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
    """Custom LLM wrapper supporting both Router API and Inference API."""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model or os.getenv("HUGGINGFACE_MODEL", "DeepHat/DeepHat-V1-7B")
        
        # Determine which API to use based on model
        if "DeepHat" in self.model:
            # Use Inference API for DeepHat model
            self.use_inference_api = True
            self.endpoint = f"https://api-inference.huggingface.co/models/{self.model}"
        else:
            # Use Router API for other models
            self.use_inference_api = False
            self.endpoint = "https://router.huggingface.co/v1/chat/completions"
        
        print(f"🤖 Using model: {self.model}")
        print(f"📡 API: {'Inference' if self.use_inference_api else 'Router'}")
    
    def invoke(self, prompt: str) -> str:
        """Call the HuggingFace API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        if self.use_inference_api:
            # Inference API format (for DeepHat)
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": 512,
                    "temperature": 0.7,
                    "top_p": 0.95,
                    "return_full_text": False
                }
            }
        else:
            # Router API format (for Llama, Mistral, etc.)
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
        
        try:
            response = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            
            if self.use_inference_api:
                # Inference API returns array of results
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("generated_text", "")
                return str(result)
            else:
                # Router API returns OpenAI-compatible format
                return result["choices"][0]["message"]["content"]
        
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
    
    # Run agent
    result = agent_executor.invoke({"messages": messages, "tool_calls": []})
    
    # Extract final response
    final_message = result["messages"][-1]
    
    # Clean up tool call syntax from final response
    content = final_message.content
    content = re.sub(r'TOOL_CALL:.*?\n', '', content, flags=re.IGNORECASE)
    content = re.sub(r'TOOL_RESULTS:.*?\n\n', '', content, flags=re.DOTALL)
    
    print('✅ Agent response:', content.strip())

    return content.strip()
