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

# Import internal utils
try:
    from .utils import visualize_graph
except (ImportError, ValueError):
    from utils import visualize_graph

# Initialize
load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# 1. MODELS
class InitialParse(BaseModel):
    employee_id: str
    action: str

class ITPayload(BaseModel):
    employee_id: str
    department: str

class ToolQuery(BaseModel):
    query: str

class FinalAnswer(BaseModel):
    summary: str
    status: str
    details: str

# 2. STATE
class State(TypedDict):
    user_input: str
    parsed_request: Optional[dict]
    payload: Optional[dict]
    policy_query: Optional[str]
    backend_result: Optional[dict]
    policy_result: Optional[str]
    error: Optional[dict]
    attempts: int
    logs: list[str]

# 3. TOOLS
def employee_database_api(payload: dict):
    if not payload.get("department"):
        raise ValueError("API Error: Missing 'department'.")
    return {"status": "Active", "emp_id": payload["employee_id"], "dept": payload["department"]}

def legal_policy_engine(query: str):
    q = query.lower()
    if "policy" not in q and "device" not in q:
        raise RuntimeError("POLICY Error: Query is missing 'policy' or 'device' keywords.")
    return "SUCCESS: User is eligible for a hardware upgrade per Engineering policy."

# 4. NODES
def parse_node(state: State):
    slm = llm.with_structured_output(InitialParse)
    res = slm.invoke(state["user_input"])
    log = f"[INIT] Parsed request: {res.action} for {res.employee_id}"
    return {"parsed_request": res.model_dump(), "attempts": 0, "logs": [log]}

def prepare_node(state: State):
    log = "[INIT] Preparing initial data payloads..."
    return {
        "payload": {"employee_id": state["parsed_request"]["employee_id"]},
        "policy_query": "check status",
        "logs": state.get("logs", []) + [log]
    }

def backend_node(state: State):
    it = state["attempts"] + 1
    log = f"[BACKEND] Attempting database sync: {state['payload'].get('department', 'MISSING')}"
    try:
        res = employee_database_api(state["payload"])
        success_log = "[BACKEND] Data verified."
        return {"backend_result": res, "error": None, "attempts": it, "logs": state.get("logs", []) + [log, success_log]}
    except Exception as e:
        fail_log = f"[BACKEND FAILURE] Error: {str(e)}"
        return {"error": {"type": "payload", "msg": str(e)}, "attempts": it, "logs": state.get("logs", []) + [log, fail_log]}

def policy_node(state: State):
    it = state["attempts"] + 1
    log = f"[POLICY] Verifying eligibility: {state['policy_query']}"
    try:
        res = legal_policy_engine(state["policy_query"])
        success_log = "[POLICY] Compliance reached."
        return {"policy_result": res, "error": None, "attempts": it, "logs": state.get("logs", []) + [log, success_log]}
    except Exception as e:
        fail_log = f"[POLICY FAILURE] Error: {str(e)}"
        return {"error": {"type": "policy", "msg": str(e)}, "attempts": it, "logs": state.get("logs", []) + [log, fail_log]}

def repair_node(state: State):
    etype = state["error"]["type"]
    diag_log = f"[HEALING] Autonomous Diagnostic identified {etype} mismatch."
    repair_log = "[HEALING] Re-writing internal logic paths..."
    
    if etype == "payload":
        slm = llm.with_structured_output(ITPayload)
        res = slm.invoke(f"Add a department to this data: {state['payload']}. Intent: {state['user_input']}")
        update_log = f"[HEALING] Payload recovered. New Dept: {res.department}"
        return {"payload": res.model_dump(), "logs": state.get("logs", []) + [diag_log, repair_log, update_log]}
    else:
        slm = llm.with_structured_output(ToolQuery)
        res = slm.invoke(f"Rewrite this query so it mentions 'policy' or 'device': '{state['policy_query']}'")
        update_log = f"[HEALING] Query recovered: {res.query}"
        return {"policy_query": res.query, "logs": state.get("logs", []) + [diag_log, repair_log, update_log]}

def finish_node(state: State):
    slm = llm.with_structured_output(FinalAnswer)
    prompt = f"Summarize: Emp {state['backend_result']['emp_id']} in {state['backend_result']['dept']} passed policy: {state['policy_result']}"
    res = slm.invoke(prompt)
    log = "[FINISH] Task synthesized and closed."
    return {"final_outcome": res.model_dump(), "logs": state.get("logs", []) + [log]}

# 5. LOGIC
def route_backend(state: State):
    if state.get("backend_result"): return "policy"
    return "repair" if state["attempts"] < 5 else "end"

def route_policy(state: State):
    if state.get("policy_result"): return "finish"
    return "repair" if state["attempts"] < 5 else "end"

# 6. EXTERNAL API WRAPPER
def run_agent(user_input: str):
    builder = StateGraph(State)
    builder.add_node("parse", parse_node)
    builder.add_node("prepare", prepare_node)
    builder.add_node("backend", backend_node)
    builder.add_node("policy", policy_node)
    builder.add_node("repair", repair_node)
    builder.add_node("finish", finish_node)

    builder.add_edge(START, "parse")
    builder.add_edge("parse", "prepare")
    builder.add_edge("prepare", "backend")
    builder.add_conditional_edges("backend", route_backend, {"policy": "policy", "repair": "repair", "end": END})
    builder.add_conditional_edges("policy", route_policy, {"finish": "finish", "repair": "repair", "end": END})
    builder.add_conditional_edges("repair", lambda s: "backend" if s["error"]["type"] == "payload" else "policy", {"backend": "backend", "policy": "policy"})
    builder.add_edge("finish", END)

    app = builder.compile()
    final_state = app.invoke({"user_input": user_input, "attempts": 0, "logs": []})
    return final_state
