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

# Initialize
load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =========================================================================================
# 1. TEMPLATE MODELS (Pydantic)
# =========================================================================================

class PayloadSchema(BaseModel):
    """Generic payload schema - easily swappable for any tool."""
    employee_id: str
    department: Optional[str]

class RepairDecision(BaseModel):
    """The brain's choice on how to fix the current failure."""
    strategy: Literal["repair", "hard_stop"]
    justification: str

# =========================================================================================
# 2. TEMPLATE STATE
# =========================================================================================

class State(TypedDict):
    logs: list[str]
    user_input: str
    payload: dict
    attempts: int
    error: Optional[dict]
    strategy: Optional[str]
    result: Optional[dict]
    is_complete: bool

# =========================================================================================
# 3. BACKEND (Simulator)
# =========================================================================================

def tool_provider(payload: dict):
    if not payload.get("department"):
        raise ValueError("Missing 'department' field.")
    return {"status": "success", "msg": f"Provisioned for {payload['employee_id']}"}

# =========================================================================================
# 4. TEMPLATE NODES
# =========================================================================================

def init_node(state: State):
    """Initial Step: Create data (with intentional error for the demo)."""
    user_req = state.get("user_input", "E-102")
    log = f"[INIT] Generating provisioning payload for: {user_req}"
    print(log)
    
    # Extract ID from input or use default
    emp_id = user_req.split()[-1] if "E-" in user_req else "E-102"
    
    return {
        "payload": {"employee_id": emp_id}, # No department - triggers demo repair
        "attempts": 0,
        "is_complete": False,
        "logs": state.get("logs", []) + [log]
    }

def execute_node(state: State):
    """Execution Step: Run tool and capture errors."""
    it = state.get("attempts", 0) + 1
    print(f"[EXECUTE] Attempt #{it}")
    
    try:
        res = tool_provider(state["payload"])
        print(f"[SUCCESS] Tool response: {res}")
        return {"result": res, "is_complete": True, "attempts": it, "error": None}
    except Exception as e:
        error_msg = str(e)
        print(f"[ERROR] Caught: {error_msg}")
        return {"error": {"msg": error_msg}, "is_complete": False, "attempts": it}

def diagnose_node(state: State):
    """Diagnostic Step: Decide how to heal."""
    print("[DIAGNOSE] Analyzing the failure...")
    structured_llm = llm.with_structured_output(RepairDecision)
    
    prompt = f"Failure: {state['error']['msg']}. Attempts: {state['attempts']}. Should we repair or stop?"
    outcome = structured_llm.invoke(prompt)
    
    print(f"[STRATEGY] {outcome.strategy} | Reason: {outcome.justification}")
    return {"strategy": outcome.strategy}

def repair_node(state: State):
    """Repair Step: Fix the data based on the error."""
    print("[REPAIR] AI is fixing the data...")
    structured_llm = llm.with_structured_output(PayloadSchema)
    
    prompt = f"Fix this payload: {json.dumps(state['payload'])}. Error: {state['error']['msg']}"
    fixed = structured_llm.invoke(prompt)
    
    return {"payload": fixed.model_dump()}

# =========================================================================================
# 5. TEMPLATE ROUTING logic
# =========================================================================================

def route_after_execute(state: State):
    if state["is_complete"]: return "finish"
    return "diagnose"

def route_after_diagnose(state: State):
    if state["strategy"] == "hard_stop": return "finish"
    return "repair"

# =========================================================================================
# 6. GRAPH ASSEMBLY
# =========================================================================================

# --- Build the Graph at Module Level ---
builder = StateGraph(State)
builder.add_node("init", init_node)
builder.add_node("execute", execute_node)
builder.add_node("diagnose", diagnose_node)
builder.add_node("repair", repair_node)
def finish_node(state: State):
    """Final summary for the UI."""
    log = "[FINISH] Process loop exited successfully."
    print(log)
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Agentic Loop Resolved",
            "details": {
                "Final Result": state.get("result"),
                "Autonomous Path": state.get("strategy") or "Direct Success",
                "Total Attempts": state.get("attempts")
            }
        }
    }

builder.add_node("finish", finish_node)
builder.add_edge(START, "init")
builder.add_edge("init", "execute")
builder.add_edge("repair", "execute")
builder.add_conditional_edges("execute", route_after_execute, {"diagnose": "diagnose", "finish": "finish"})
builder.add_conditional_edges("diagnose", route_after_diagnose, {"repair": "repair", "finish": "finish"})
builder.add_edge("finish", END)
app = builder.compile()

def main():
    visualize_graph(app, "11_self_healing_template.png")
    print("\n--- Starting Mission 7 - Project 11 ---")
    app.invoke({
        "logs": [],
        "payload": {},
        "attempts": 0,
        "error": None,
        "strategy": None,
        "result": None,
        "is_complete": False
    })

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "payload": {}, "attempts": 0, "error": None, "strategy": None, "result": None, "is_complete": False})
