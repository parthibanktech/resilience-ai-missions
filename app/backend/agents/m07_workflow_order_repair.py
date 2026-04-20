import sys
import os
# Ensure parent directory is in path for 'utils' and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import List, Optional, TypedDict
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
# 1. THE LOGIC SCHEMA
# =========================================================================================

class WorkflowPlan(BaseModel):
    """The structured sequence of IT operations."""
    workflow_steps: List[str] = Field(description="Order of steps: e.g. ['validate_request', 'submit_request']")
    reasoning: str = Field(description="Internal logic for this order.")

# =========================================================================================
# 2. THE GRAPH STATE
# =========================================================================================

class State(TypedDict):
    logs: list[str]
    user_input: str
    workflow_steps: List[str]
    error: Optional[dict]
    result: Optional[str]
    iterations: int

# =========================================================================================
# 3. WORKFLOW ENGINE (Simulator)
# =========================================================================================

def execute_workflow_engine(steps: List[str]):
    # Simulation Rule: Validation MUST happen before submission
    validated = False
    for step in steps:
        if step == "validate_request":
            validated = True
        if step == "submit_request" and not validated:
            raise RuntimeError("CRITICAL ERROR: 'submit_request' detected before 'validate_request'. Logic order violation.")
    
    return "SUCCESS: Request validated and submitted in the correct IT order."

# =========================================================================================
# 4. GRAPH NODES
# =========================================================================================

def plan_node(state: State):
    """Initial Planning: Tries to sequence the steps."""
    log = "[PLAN] Designing the initial IT workflow..."
    print(log)
    # Force a 'vague' or 'illogical' start for the demo
    return {
        "workflow_steps": ["submit_request", "validate_request"], 
        "iterations": 0,
        "logs": state.get("logs", []) + [log]
    }

def execute_node(state: State):
    """Execution: Runs the workflow engine and catches logic errors."""
    log = f"[EXECUTE] Running steps: {state['workflow_steps']}"
    print(log)
    try:
        msg = execute_workflow_engine(state["workflow_steps"])
        success_log = f"[PROCESS SUCCESS] {msg}"
        print(success_log)
        return {"result": msg, "error": None, "logs": state.get("logs", []) + [log, success_log]}
    except Exception as e:
        error_msg = str(e)
        fail_log = f"[PROCESS FAILURE] {error_msg}"
        print(fail_log)
        return {"error": {"msg": error_msg}, "result": None, "logs": state.get("logs", []) + [log, fail_log]}

def repair_node(state: State):
    """The Re-Planner Node: Analyzes the logic error and re-sequences the workflow."""
    print("[REPAIR] AI is analyzing the logic violation and re-ordering steps...")
    structured_llm = llm.with_structured_output(WorkflowPlan)
    
    prompt = f"""
    You are a Workflow Architect. The current plan failed.
    Current Steps: {state['workflow_steps']}
    Engine Error: {state['error']['msg']}
    
    Refer to the user intent: {state['user_input']}
    Re-order the steps to make it logical. Remember: Validation must come before Submission.
    """
    
    fixed_plan = structured_llm.invoke(prompt)
    log = f"[REPAIR] AI re-ordered the steps to maintain compliance."
    repair_log = f"[REPAIR] New Plan: {fixed_plan.workflow_steps}"
    print(repair_log)
    
    return {
        "workflow_steps": fixed_plan.workflow_steps, 
        "iterations": state["iterations"] + 1,
        "logs": state.get("logs", []) + [log, repair_log]
    }

# =========================================================================================
# 5. CYCLIC ROUTING
# =========================================================================================

def route_next(state: State):
    if state.get("result"):
        return "end"
    if state["iterations"] < 2:
        return "repair"
    return "end"

# =========================================================================================
# 6. ASSEMBLY
# =========================================================================================

# --- Build the Graph at Module Level ---
builder = StateGraph(State)
def finish_node(state: State):
    """Final summary for the UI."""
    log = "[DONE] Workflow repair mission synchronized."
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "IT Workflow Order Healed",
            "details": {
                "User Request": state.get("user_input"),
                "Logical Sequence": " -> ".join(state["workflow_steps"]),
                "Status": state.get("result")
            }
        }
    }

builder.add_node("plan", plan_node)
builder.add_node("execute", execute_node)
builder.add_node("repair", repair_node)
builder.add_node("finish", finish_node)
builder.add_edge(START, "plan")
builder.add_edge("plan", "execute")
builder.add_edge("repair", "execute")
builder.add_conditional_edges("execute", route_next, {"repair": "repair", "end": "finish"})
builder.add_edge("finish", END)
app = builder.compile()

def main():
    visualize_graph(app, "07_workflow_repair_modern.png")
    print("\n--- Starting Mission 7 - Project 07 ---")
    app.invoke({
        "logs": [],
        "user_input": "Onboard employee E-102 and request a laptop.",
        "workflow_steps": [],
        "error": None,
        "result": None,
        "iterations": 0
    })

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "workflow_steps": [], "error": None, "result": None, "iterations": 0})
