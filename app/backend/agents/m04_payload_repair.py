import sys
import os
# Ensure parent directory is in path for 'utils' and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Optional, TypedDict
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph

try:
    from .utils import visualize_graph
except ImportError:
    from utils import visualize_graph

# Initialize
load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =========================================================================================
# 1. MODELS & STATE
# =========================================================================================

class EmployeePayload(BaseModel):
    """The structured data for the IT backend."""
    employee_id: str = Field(description="ID of the employee (E-102)")
    department: Optional[str] = Field(description="Department name (Engineering, Sales, etc.)")

class State(TypedDict):
    user_input: str
    payload: dict
    error: Optional[dict]
    result: Optional[dict]
    iterations: int
    logs: list[str]  # Added for real-time trace

# =========================================================================================
# 2. BACKEND SIMULATOR
# =========================================================================================

def fake_employee_backend(payload: dict):
    # This tool FAILS if department is missing
    if not payload.get("department"):
        raise ValueError("Missing mandatory field: 'department'")
    
    return {
        "status": "Success",
        "assigned_laptop": "MacBook Pro",
        "employee_id": payload["employee_id"],
        "department": payload["department"]
    }

# =========================================================================================
# 3. GRAPH NODES
# =========================================================================================

def agent_node(state: State):
    """Generates the initial (and intentionally incomplete) payload."""
    structured_llm = llm.with_structured_output(EmployeePayload)
    prompt = f"Convert to JSON: {state['user_input']}. Leave 'department' as None for now."
    
    response = structured_llm.invoke(prompt)
    log = f"[AGENT] Generated initial payload for: {response.employee_id}"
    print(log)
    
    return {"payload": response.model_dump(), "iterations": 0, "logs": [log]}

def tool_node(state: State):
    """Executes the tool call and captures errors."""
    log = f"[TOOL] Attempting backend sync with: {state['payload'].get('department', 'MISSING_DEPT')}"
    print(log)
    try:
        result = fake_employee_backend(state["payload"])
        success_log = "[TOOL] Connection Successful. Data synchronized."
        return {"result": result, "error": None, "logs": state.get("logs", []) + [log, success_log]}
    except Exception as e:
        error_msg = str(e)
        fail_log = f"[TOOL FAILURE] Blocked by: {error_msg}"
        return {"error": {"msg": error_msg}, "result": None, "logs": state.get("logs", []) + [log, fail_log]}

def repair_node(state: State):
    """FIXES the payload based on the error feedback."""
    diag_log = "[REPAIR] Internal Diagnostic identified missing 'department' field."
    repair_log = "[REPAIR] AI is autonomously re-constructing the missing data payload..."
    print(repair_log)
    
    structured_llm = llm.with_structured_output(EmployeePayload)
    prompt = f"""
    The previous call failed because of this error: {state['error']['msg']}
    Original Payload: {json.dumps(state['payload'])}
    Initial Request: '{state['user_input']}'
    
    Fix the payload by adding a valid department. 
    Try to infer it from the request (e.g. if they say 'hiring', use 'HR'). 
    If you can't infer it, use 'General IT'.
    """
    
    fixed_payload = structured_llm.invoke(prompt)
    success_log = f"[REPAIR] Payload successfully healed. New department: {fixed_payload.department}"
    
    return {
        "payload": fixed_payload.model_dump(), 
        "iterations": state["iterations"] + 1,
        "logs": state.get("logs", []) + [diag_log, repair_log, success_log]
    }

# =========================================================================================
# 4. CONDITIONAL LOGIC (The Cyclic Edge)
# =========================================================================================

def route_next(state: State):
    # If success -> Stop
    if state.get("result"):
        return "end"
    
    # If error and we haven't looped too many times -> Repair
    if state["iterations"] < 2:
        return "repair"
    
    return "end"

def finish_node(state: State):
    """Summarizes success for the UI."""
    log = "[DONE] Payload processing loop complete."
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Data Payload Healed Successfully",
            "details": {
                "Final Payload": state.get("payload"),
                "Attempts": state.get("iterations"),
                "Sync Result": state.get("result")
            }
        }
    }

# =========================================================================================
# 5. GRAPH CONSTRUCTION
# =========================================================================================

builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_node("tool", tool_node)
builder.add_node("repair", repair_node)
builder.add_node("finish", finish_node)

builder.add_edge(START, "agent")
builder.add_edge("agent", "tool")
builder.add_edge("repair", "tool")
builder.add_conditional_edges("tool", route_next, {"repair": "repair", "end": "finish"})
builder.add_edge("finish", END)

app = builder.compile()

def main():
    # Save the visualization
    visualize_graph(app, "04_payload_repair_cyclic.png")

    print("\n--- Starting Mission 7 - Project 04 (Cyclic Healing) ---")
    app.invoke({
        "logs": [],
        "user_input": "Onboard employee E-555",
        "payload": {},
        "error": None,
        "result": None,
        "iterations": 0
    })

def run_agent(user_input: str):
    return app.invoke({
        "logs": [],
        "user_input": user_input,
        "payload": {},
        "error": None,
        "result": None,
        "iterations": 0
    })

if __name__ == "__main__":
    main()
