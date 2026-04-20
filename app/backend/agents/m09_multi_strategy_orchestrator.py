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

# Initialize components
load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =========================================================================================
# 1. SPECIALIZED MODELS (Pydantic)
# =========================================================================================

class InitialData(BaseModel):
    """The starting set of data generated from the user's request."""
    employee_id: str = Field(description="Employee ID (E-102)")
    vague_query: str = Field(description="A policy query that might be too simple.")

class DiagnosticStrategy(BaseModel):
    """The choice made by the Master Brain regarding which specialist to call."""
    strategy: Literal["payload_repair", "tool_call_repair", "hard_stop"] = Field(
        description="Choose the specialist based on the error type."
    )
    justification: str = Field(description="Brief explanation of current diagnostic logic.")

class EmployeePayload(BaseModel):
    """Fixed data structure for the backend."""
    employee_id: str
    department: str = Field(description="The department name (IT, HR, etc.)")

class ToolQuery(BaseModel):
    """Fixed text query for the policy tool."""
    query: str = Field(description="Must contain policy or device keywords.")

# =========================================================================================
# 2. GRAPH STATE
# =========================================================================================

class State(TypedDict):
    logs: list[str]
    user_input: str
    payload: dict
    policy_query: str
    attempts: int
    error: Optional[dict]
    strategy: Optional[str]
    backend_result: Optional[dict]
    policy_result: Optional[str]

# =========================================================================================
# 3. BACKEND SIMULATORS (Tools)
# =========================================================================================

def employee_backend(payload: dict):
    if not payload.get("department"):
        raise ValueError("BACKEND ERROR: Missing 'department' field.")
    return {"status": "Found", "id": payload["employee_id"], "dept": payload["department"]}

def policy_tool(query: str):
    if "policy" not in query.lower() and "device" not in query.lower():
        raise RuntimeError("TOOL ERROR: Query must mention 'policy' or 'device'.")
    return "SUCCESS: Manager approval required for new hardware."

# =========================================================================================
# 4. GRAPH NODES (The Orchestration)
# =========================================================================================

def create_inputs_node(state: State):
    """Node 1: The Planner. Creates intentionally imperfect starting data."""
    log = "[PLANNER] Initializing IT request orchestration..."
    print(log)
    user_req = state.get("user_input", "E-102")
    emp_id = user_req.split()[-1] if "E-" in user_req else "E-102"
    
    # Force an imperfect start for the demo
    return {
        "payload": {"employee_id": emp_id}, # Missing department
        "policy_query": "approval",           # Vague/Missing keywords
        "attempts": 0,
        "logs": state.get("logs", []) + [log]
    }

def execute_node(state: State):
    """Node 2: The Multi-Executor. Tries all required tool calls."""
    it = state.get("attempts", 0) + 1
    print(f"\n[EXECUTION] Multi-Tool Cycle #{it}")
    
    try:
        # 1. Attempt Backend Call (If not already successful)
        b_res = state.get("backend_result") or employee_backend(state["payload"])
        
        # 2. Attempt Policy Tool (If not already successful)
        p_res = state.get("policy_result") or policy_tool(state["policy_query"])
        
        # If we get here, everything worked!
        log = "[SUCCESS] Tool synchronization complete."
        print(log)
        return {"backend_result": b_res, "policy_result": p_res, "error": None, "attempts": it, "logs": state.get("logs", []) + [log]}
    
    except Exception as e:
        # Determine error origin
        error_type = "payload_problem" if "BACKEND" in str(e) else "tool_query_problem"
        log = f"[CRASH] {str(e)}"
        print(log)
        return {"error": {"type": error_type, "msg": str(e)}, "attempts": it, "logs": state.get("logs", []) + [log]}

def diagnose_node(state: State):
    """Node 3: THE MASTER BRAIN. Diagnoes the failure and picks a specialist."""
    print("[DIAGNOSE] Master Brain is analyzing the failure context...")
    structured_llm = llm.with_structured_output(DiagnosticStrategy)
    
    prompt = f"""
    ANALYSIS NEEDED:
    Current Error: {state['error']['msg']}
    Error Type: {state['error']['type']}
    
    Decide whether to fix the Payload, fix the Query, or Stop.
    """
    
    outcome = structured_llm.invoke(prompt)
    log = f"[DIAGNOSE] Master Brain identified: {outcome.strategy.replace('_', ' ').upper()}"
    print(log)
    return {"strategy": outcome.strategy, "logs": state.get("logs", []) + [log]}

def repair_payload_node(state: State):
    """Specialist 1: Fixes JSON Data."""
    print("[REPAIR] Specialist Agent fixing Data Payload...")
    structured_llm = llm.with_structured_output(EmployeePayload)
    
    prompt = f"Fix this payload: {json.dumps(state['payload'])}. Error: {state['error']['msg']}"
    fixed = structured_llm.invoke(prompt)
    log = f"[REPAIR] Specialist recovered missing department: {fixed.department}"
    return {"payload": fixed.model_dump(), "logs": state.get("logs", []) + [log]}

def repair_tool_node(state: State):
    """Specialist 2: Fixes Tool Queries."""
    log = "[REPAIR] Specialist Agent refining the tool call query..."
    print(log)
    structured_llm = llm.with_structured_output(ToolQuery)
    
    prompt = f"Fix this query: '{state['policy_query']}'. Error: {state['error']['msg']}"
    fixed = structured_llm.invoke(prompt)
    repair_log = f"[REPAIR] Optimized Query: '{fixed.query}'"
    print(repair_log)
    return {"policy_query": fixed.query, "logs": state.get("logs", []) + [log, repair_log]}

# =========================================================================================
# 5. CYCLIC ROUTING LOGIC
# =========================================================================================

def route_next_steps(state: State):
    # Success path
    if state.get("backend_result") and state.get("policy_result"):
        return "finish"
    
    # Failure path
    if state["attempts"] < 5:
        return "diagnose"
    
    return "finish"

def route_strategy(state: State):
    # Specialized branching based on AI decision
    if state["strategy"] == "hard_stop": return "finish"
    if state["strategy"] == "payload_repair": return "repair_payload"
    return "repair_tool"

# =========================================================================================
# 6. GRAPH ASSEMBLY
# =========================================================================================

# --- Build the Graph at Module Level ---
builder = StateGraph(State)
builder.add_node("create_inputs", create_inputs_node)
builder.add_node("execute", execute_node)
builder.add_node("diagnose", diagnose_node)
builder.add_node("repair_payload", repair_payload_node)
builder.add_node("repair_tool", repair_tool_node)
def finish_node(state: State):
    """Final Node: Summarizes the multi-step outcome for the UI."""
    log = "[FINISH] All IT orchestration tasks completed."
    print(log)
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Multi-Step IT Orchestration Success",
            "details": {
                "Backend Status": state.get("backend_result"),
                "Policy Compliance": state.get("policy_result"),
                "Attempts Required": state.get("attempts")
            }
        }
    }

builder.add_node("finish", finish_node)
builder.add_edge(START, "create_inputs")
builder.add_edge("create_inputs", "execute")
builder.add_edge("repair_payload", "execute")
builder.add_edge("repair_tool", "execute")
builder.add_conditional_edges("execute", route_next_steps, {"diagnose": "diagnose", "finish": "finish"})
builder.add_conditional_edges("diagnose", route_strategy, {"repair_payload": "repair_payload", "repair_tool": "repair_tool", "finish": "finish"})
app = builder.compile()

def main():
    visualize_graph(app, "09_master_brain_cyclic.png")
    print("\n--- Starting Mission 7 - Project 09 ---")
    app.invoke({
        "logs": [],
        "user_input": "Request laptop for E-102 in the Engineering department.",
        "payload": {},
        "policy_query": "",
        "attempts": 0,
        "error": None,
        "strategy": None,
        "backend_result": None,
        "policy_result": None
    })

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "payload": {}, "policy_query": "", "attempts": 0, "error": None, "strategy": None, "backend_result": None, "policy_result": None})
