import sys
import os
# Ensure parent directory is in path for 'utils' and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json  # Import for handling JSON data strings

from dotenv import load_dotenv  # Load environment variables from .env file
from langchain_openai import ChatOpenAI  # OpenAI's LangChain wrapper for the LLM
from langgraph.graph import END, START, StateGraph  # Core LangGraph primitives
from typing_extensions import TypedDict  # Native-like types for the Graph State

try:
    from .utils import visualize_graph  # Local utility to save the graph image
except ImportError:
    from utils import visualize_graph  # Local utility to save the graph image

load_dotenv()  # Execute the loading of .env variables (like API keys)
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)  # Initialize LLM


# This class defines the "schema" for the shared memory (State) of the graph
class State(TypedDict):
    logs: list[str]
    user_input: str  # The original request from the human
    payload: dict  # The JSON data the agent builds for the backend
    result: dict  # The final response from the backend system


# Custom Exception to simulate a "500 Internal Server Error" when data is wrong
class BackendSchemaError(Exception):
    pass


# Helper to print pretty section headers in the console
def title(text):
    print()
    print("=" * 80)
    print(text)
    print("=" * 80)


# Helper to clean triple-backticks (```json) from LLM output before parsing
def parse_json(text):
    cleaned = text.strip()
    cleaned = cleaned.replace("```json", "")
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.strip()
    return json.loads(cleaned)


# Simulator: A backend function that strictly requires a 'department' field
def fake_employee_backend(payload):
    # This backend raises an error when 'department' is missing
    if "department" not in payload or not payload["department"]:
        raise BackendSchemaError("500: Missing required field: department")

    return {
        "employee_id": payload["employee_id"],
        "department": payload["department"],
        "device_status": "Laptop assigned",
    }


# Node 1: The 'Agent' logic. Transforms user input into a tool payload.
def agent_node(state):
    # The agent uses the LLM to create a payload from the user_input in state.
    prompt = f"""
You are a payload generator.
The user wants to: {state["user_input"]}

Task: Create a JSON payload for this employee device lookup.
Return only valid JSON.

Demo Constraint:
Leave out 'department' on purpose to trigger a failure.
"""
    response = llm.invoke(prompt)
    payload = parse_json(response.content)
    log = f"[AGENT] Generated payload for: {payload.get('employee_id', 'UNKNOWN')}"
    print(log)
    # The return value is merged into the global Graph State
    return {"payload": payload, "logs": state.get("logs", []) + [log]}


# Node 2: The 'Backend' logic. Executes the actual tool call.
def backend_node(state):
    # This node takes the payload from the state and calls our simulator
    # If the simulator raises an error, the entire graph will crash here!
    log = f"[BACKEND] Contacting resource for ID: {state['payload'].get('employee_id')}"
    print(log)
    result = fake_employee_backend(state["payload"])
    success_log = "[BACKEND] Lookup successful."
    return {"result": result, "logs": state.get("logs", []) + [log, success_log]}


# --- Build the Graph at Module Level ---
builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_node("backend", backend_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", "backend")
builder.add_edge("backend", END)
app = builder.compile()

def main():
    title("Mission 7 - 01 Fragile Agent Failure Demo")
    visualize_graph(app, "01_fragile_agent_failure_demo.png")
    try:
        app.invoke({
            "logs": [],
            "user_input": "Check device for employee E-102",
            "payload": {},
            "result": {}
        })
    except Exception as exc:
        print("[FRAGILE FAILURE]", exc)

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "payload": {}, "result": {}})
