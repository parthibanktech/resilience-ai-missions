import sys
import os
# Ensure parent directory is in path for 'utils' and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Optional, TypedDict, Literal
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

try:
    from .utils import visualize_graph
except ImportError:
    from utils import visualize_graph

# Initialize environment and model
load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =========================================================================================
# 1. STRUCTURED OUTPUT MODELS (Pydantic)
# These models ensure the LLM returns data in a exact shape, preventing parsing errors.
# =========================================================================================

class EmployeePayload(BaseModel):
    """The JSON schema required by the employee backend."""
    employee_id: str = Field(description="The unique ID of the employee (e.g., E-102)")
    department: Optional[str] = Field(description="The department name (e.g., Sales, Engineering)")

class RecoveryDecision(BaseModel):
    """The strategic decision made by the router to fix a failure."""
    decision: Literal["payload_repair", "tool_call_repair", "prompt_repair", "hard_stop"] = Field(
        description="The chosen repair strategy based on the error analysis."
    )
    justification: str = Field(description="Educational reasoning for choosing this path.")

# =========================================================================================
# 2. GRAPH STATE DEFINITION
# This TypedDict defines the structure of our shared 'memory' across the workflow.
# =========================================================================================

class State(TypedDict):
    logs: list[str]
    user_input: str      # Original human request
    payload: dict        # The intermediate data built for the tool
    error: Optional[dict]# Captured error data if something goes wrong
    decision: Optional[str] # Strategic decision on how to repair
    result: Optional[dict]  # Final successful outcome

# =========================================================================================
# 3. BACKEND SIMULATOR (The "Tool")
# =========================================================================================

class BackendSchemaError(Exception):
    pass

def fake_employee_backend(payload: dict):
    # This backend strictly requires a 'department' field to be present
    if "department" not in payload or not payload["department"]:
        raise BackendSchemaError("500: Missing required field: department")

    return {
        "employee_id": payload["employee_id"],
        "department": payload["department"],
        "device_status": "Laptop assigned",
    }

# =========================================================================================
# 4. GRAPH NODES (Workflow Steps)
# =========================================================================================

def agent_node(state: State):
    """Turns user input into a structured payload."""
    # We use structured output here to ensure we get a valid dict
    structured_llm = llm.with_structured_output(EmployeePayload)
    
    prompt = f"Convert this request into a payload: {state['user_input']}. " \
             "DEMO CONSTRAINT: Leave out the department field on purpose."
             
    response = structured_llm.invoke(prompt)
    log = f"[AGENT] Generated initial Payload for: {response.employee_id}"
    print(log)
    return {"payload": response.model_dump(), "logs": state.get("logs", []) + [log]}

def tool_node(state: State):
    """Attempts to execute the backend tool and captures errors as data."""
    try:
        result = fake_employee_backend(state["payload"])
        log = f"[TOOL] Success: Backend lookup complete for {state['payload'].get('employee_id')}"
        return {"result": result, "error": None, "logs": state.get("logs", []) + [log]}
    except Exception as exc:
        # Instead of crashing the script, we save the error into the State
        error_context = {
            "error_type": "SchemaError",
            "message": str(exc),
            "repair_hint": "The backend requires the 'department' field."
        }
        log = f"[TOOL] Caught Error: {error_context['message']}"
        print(log)
        return {"error": error_context, "result": None, "logs": state.get("logs", []) + [log]}

def router_node(state: State):
    """Analyzes the error in the state and decides on a recovery strategy."""
    # Use Pydantic to force a valid decision from our list
    structured_llm = llm.with_structured_output(RecoveryDecision)
    
    prompt = f"""
    Analyze this failure:
    Error: {json.dumps(state['error'])}
    Payload: {json.dumps(state['payload'])}
    
    Route to:
    - payload_repair (if data is missing)
    - tool_call_repair (if the system name was wrong)
    - hard_stop (if you can't fix it)
    """
    
    outcome = structured_llm.invoke(prompt)
    log = f"[ROUTER] Strategic Decision: {outcome.decision.upper()}"
    reason_log = f"[ROUTER] Logic: {outcome.justification}"
    print(log)
    print(reason_log)
    
    return {"decision": outcome.decision, "logs": state.get("logs", []) + [log, reason_log]}

def finish_node(state: State):
    """Final visualization of the workflow outcome."""
    if state.get("result"):
        log = f"[SUCCESS] Tool Output: {state['result']}"
    else:
        log = f"[FAILED] Mission managed by Router. Final Route: {state['decision']}"
    print(log)
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Diagnostic Routing Complete",
            "details": {
                "Input": state.get("user_input"),
                "Result": state.get("result") or "N/A",
                "Recovery Path": state.get("decision")
            }
        }
    }

# =========================================================================================
# 5. GRAPH ROUTING LOGIC
# =========================================================================================

def route_after_tool(state: State):
    """Condition: If success -> Finish, If error -> Route to Brain."""
    if state.get("result"):
        return "finish"
    return "router"

# =========================================================================================
# 6. GRAPH CONSTRUCTION
# =========================================================================================

# Initialize the graph with our State schema
builder = StateGraph(State)

# 1. Add logic nodes
builder.add_node("agent", agent_node)
builder.add_node("tool", tool_node)
builder.add_node("router", router_node)
builder.add_node("finish", finish_node)

# 2. Define standard edges
builder.add_edge(START, "agent")
builder.add_edge("agent", "tool")

# 3. Define conditional edges (The "Divide and Conquer" logic)
builder.add_conditional_edges(
    "tool",
    route_after_tool,
    {
        "router": "router",   # Path for repair
        "finish": "finish"    # Path for success
    }
)

# Edge from router to finish (In this mission, we just stop after deciding)
builder.add_edge("router", "finish")
builder.add_edge("finish", END)

# 4. Compile the application
app = builder.compile()

def main():
    # Optional: Save a visualization of the brain loop
    visualize_graph(app, "03_recovery_decision_router.png")

    # 5. Execute with the test case
    print("\n--- Starting Mission 7 - Project 03 ---")
    app.invoke({
        "logs": [],
        "user_input": "Check device for employee E-102",
        "payload": {},
        "error": None,
        "decision": None,
        "result": None
    })

def run_agent(user_input: str):
    return app.invoke({
        "logs": [],
        "user_input": user_input,
        "payload": {},
        "error": None,
        "decision": None,
        "result": None
    })

if __name__ == "__main__":
    main()
