import os
import re
import requests
from typing import TypedDict, Sequence, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END

# Define tools for the agent
def port_scan(target, ports="1-1024"):
    """Perform a port scan on a target using nmap."""
    try:
        import subprocess
        import re

        # Use subprocess to run nmap directly
        cmd = ['nmap', '-p', ports, '-T4', '--open', target]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode != 0:
            return f"Port scan failed: nmap returned error code {result.returncode}. Make sure nmap is installed."

        output = result.stdout

        # Parse the output to extract open ports
        lines = output.split('\n')
        open_ports = []

        for line in lines:
            # Look for lines like "22/tcp open  ssh"
            if '/tcp' in line and 'open' in line:
                parts = line.split()
                if len(parts) >= 3:
                    port = parts[0].split('/')[0]
                    service = parts[2] if len(parts) > 2 else 'unknown'
                    open_ports.append(f"Port {port}: open ({service})")

        if open_ports:
            return f"Port scan results for {target}:\n" + "\n".join(open_ports)
        else:
            return f"No open ports found on {target} in range {ports}"

    except subprocess.TimeoutExpired:
        return f"Port scan timed out for {target}"
    except FileNotFoundError:
        return "Port scan failed: nmap not found. Please install nmap."
    except Exception as e:
        return f"Port scan failed: {str(e)}"

def vulnerability_assessment(target):
    """Perform basic vulnerability assessment on a target system."""
    try:
        import subprocess

        # First, do a basic port scan to identify services
        port_cmd = ['nmap', '-p-', '--open', '-T4', target]
        port_result = subprocess.run(port_cmd, capture_output=True, text=True, timeout=120)

        results = [f"Basic Vulnerability Assessment for {target}:"]
        open_ports = []

        if port_result.returncode == 0:
            # Parse open ports
            for line in port_result.stdout.split('\n'):
                if '/tcp' in line and 'open' in line:
                    parts = line.split()
                    if len(parts) >= 3:
                        port = parts[0].split('/')[0]
                        service = parts[2] if len(parts) > 2 else 'unknown'
                        open_ports.append((port, service))

                        # Basic vulnerability checks based on service
                        port_num = int(port)
                        if port_num == 21 and 'ftp' in service.lower():
                            results.append("⚠️  WARNING: FTP service detected on port 21 - consider using SFTP (secure)")
                        elif port_num == 23 and 'telnet' in service.lower():
                            results.append("🚨 CRITICAL: Telnet service detected on port 23 - insecure, use SSH")
                        elif port_num == 80 and 'http' in service.lower():
                            results.append("ℹ️  INFO: HTTP detected on port 80 - check for HTTPS support")
                        elif port_num == 445 and 'smb' in service.lower():
                            results.append("⚠️  WARNING: SMB service detected - check for known vulnerabilities")
                        elif port_num == 3389 and 'rdp' in service.lower():
                            results.append("⚠️  WARNING: RDP service detected - ensure NLA is enabled")

        # Check for common misconfigurations
        if open_ports:
            results.append(f"\nOpen ports found: {len(open_ports)}")
            for port, service in open_ports:
                results.append(f"  - Port {port}: {service}")
        else:
            results.append("No open ports detected")

        # Additional checks
        results.append("\nGeneral Recommendations:")
        results.append("• Ensure all services are up-to-date")
        results.append("• Use strong authentication mechanisms")
        results.append("• Implement proper firewall rules")
        results.append("• Regularly scan for vulnerabilities")

        return "\n".join(results)

    except subprocess.TimeoutExpired:
        return f"Vulnerability assessment timed out for {target}"
    except FileNotFoundError:
        return "Vulnerability assessment failed: nmap not found. Please install nmap."
    except Exception as e:
        return f"Vulnerability assessment failed: {str(e)}"

def web_app_security_test(url):
    """Perform basic web application security testing."""
    try:
        response = requests.get(url, timeout=10, verify=False)

        results = []
        results.append(f"Web Application Security Test for {url}")
        results.append(f"Status Code: {response.status_code}")
        results.append(f"Server: {response.headers.get('Server', 'Unknown')}")
        results.append(f"Content-Type: {response.headers.get('Content-Type', 'Unknown')}")

        # Check for security headers
        security_headers = {
            'X-Frame-Options': 'Missing X-Frame-Options header (Clickjacking vulnerability)',
            'X-Content-Type-Options': 'Missing X-Content-Type-Options header (MIME sniffing vulnerability)',
            'X-XSS-Protection': 'Missing X-XSS-Protection header (XSS vulnerability)',
            'Strict-Transport-Security': 'Missing Strict-Transport-Security header (No HTTPS enforcement)',
            'Content-Security-Policy': 'Missing Content-Security-Policy header (XSS/injection vulnerabilities)'
        }

        results.append("\nSecurity Headers Check:")
        for header, warning in security_headers.items():
            if header not in response.headers:
                results.append(f"❌ {warning}")
            else:
                results.append(f"✅ {header}: {response.headers[header]}")

        # Check for common vulnerabilities
        results.append("\nCommon Vulnerability Checks:")

        # Check for exposed admin panels
        admin_paths = ['/admin', '/admin.php', '/administrator', '/wp-admin', '/login', '/signin']
        for path in admin_paths:
            try:
                admin_response = requests.get(url.rstrip('/') + path, timeout=5, verify=False)
                if admin_response.status_code == 200:
                    results.append(f"⚠️  Potential admin panel found at {path} (status: {admin_response.status_code})")
            except:
                pass

        # Check for directory listing
        try:
            dir_response = requests.get(url.rstrip('/') + '/', timeout=5, verify=False)
            if 'Index of' in dir_response.text or 'Directory listing' in dir_response.text:
                results.append("⚠️  Directory listing enabled (information disclosure)")
        except:
            pass

        # Check for outdated software versions
        server = response.headers.get('Server', '').lower()
        if 'apache' in server and '2.4' not in server:
            results.append("⚠️  Potentially outdated Apache version")
        elif 'nginx' in server and '1.2' not in server:
            results.append("⚠️  Potentially outdated Nginx version")

        return "\n".join(results)

    except Exception as e:
        return f"Web application security test failed: {str(e)}"

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
    },
    "port_scan": {
        "description": "Perform a port scan on a target IP or hostname to discover open ports and services",
        "parameters": ["target", "ports"],
        "function": lambda target, ports="1-1024": port_scan(target, ports)
    },
    "vulnerability_assessment": {
        "description": "Perform vulnerability assessment on a target system using nmap scripts",
        "parameters": ["target"],
        "function": vulnerability_assessment
    },
    "web_app_security_test": {
        "description": "Perform basic web application security testing including header checks and common vulnerabilities",
        "parameters": ["url"],
        "function": web_app_security_test
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
