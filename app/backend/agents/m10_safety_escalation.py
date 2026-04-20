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
# 1. MODELS & STATE
# =========================================================================================

class EscalationDecision(BaseModel):
    """The AI's choice to either keep trying or escalate to a human."""
    decision: Literal["retry", "hard_stop"] = Field(description="Decision to retry or halt.")
    reasoning: str = Field(description="Internal logic for escalation.")

class State(TypedDict):
    logs: list[str]
    user_input: str
    attempts: int
    error: Optional[dict]
    decision: Optional[str]

# =========================================================================================
# 2. THE "UNREPAIRABLE" BACKEND
# =========================================================================================

def security_locked_backend():
    # This represents a fatal error that an AI cannot fix (e.g., human-only approval needed).
    raise PermissionError("403: CRITICAL AUTH FAILURE. Identity verification required by Human Admin.")

# =========================================================================================
# 3. GRAPH NODES
# =========================================================================================

def execute_node(state: State):
    """Attempts the dangerous call and records the inevitable failure."""
    it = state.get("attempts", 0) + 1
    user_req = state.get("user_input", "Admin Action")
    log = f"\n[SECURITY ALERT] User requested: {user_req}. This action requires root access."
    print(f"\n[EXECUTE] Attempt #{it}")
    
    try:
        security_locked_backend()
        return {"attempts": it, "error": None, "logs": state.get("logs", []) + [log]}
    except Exception as e:
        error_msg = str(e)
        fail_log = f"[SYSTEM BLOCK] {error_msg}"
        print(f"[SECURITY ALERT] {error_msg}")
        return {"attempts": it, "error": {"msg": error_msg}, "logs": state.get("logs", []) + [log, fail_log]}

def diagnose_node(state: State):
    """The Brain: Decides if this error is 'beyond AI capability'."""
    print("[DIAGNOSE] Analyzing the severity of the failure...")
    structured_llm = llm.with_structured_output(EscalationDecision)
    
    prompt = f"""
    Security Incident Detected!
    Action Attempted: {state.get('user_input', 'Unknown')}
    Last Error: {state['error']['msg']}
    Total Attempts: {state['attempts']}
    
    Should you retry or STOP and escalate to a HUMAN admin?
    If the error mentions 'Identity Verification' or 'Human Admin', you MUST hard_stop.
    """
    
    outcome = structured_llm.invoke(prompt)
    log = f"[DECISION] Action: {outcome.decision} | Reason: {outcome.reasoning}"
    print(log)
    
    return {"decision": outcome.decision, "logs": state.get("logs", []) + [log]}

def finish_node(state: State):
    """The final outcome: Escalating to a real administrator."""
    if state["decision"] == "hard_stop":
        log = "[ESCALATION COMPLETE] Security protocol triggered. Human administrator notified."
    else:
        log = "[END] Protocol terminated. System stabilized."
    print(log)
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Safety Protocols Engaged" if state["decision"] == "hard_stop" else "Mission Terminated",
            "details": {
                "Security Status": "ESCALATED" if state["decision"] == "hard_stop" else "STABILIZED",
                "Diagnostic Reasoning": state.get("decision"),
                "Attempts": state.get("attempts")
            }
        }
    }

# =========================================================================================
# 4. ROUTING LOGIC
# =========================================================================================

def route_after_decide(state: State):
    if state["decision"] == "hard_stop":
        return "finish"
    if state["attempts"] >= 3:
        return "finish"
    return "execute"

# =========================================================================================
# 5. ASSEMBLY
# =========================================================================================

# --- Build the Graph at Module Level ---
builder = StateGraph(State)
builder.add_node("execute", execute_node)
builder.add_node("diagnose", diagnose_node)
builder.add_node("finish", finish_node)
builder.add_edge(START, "execute")
builder.add_edge("execute", "diagnose")
builder.add_conditional_edges("diagnose", route_after_decide, {"execute": "execute", "finish": "finish"})
builder.add_edge("finish", END)
app = builder.compile()

def main():
    visualize_graph(app, "10_escalation_modern.png")
    print("\n--- Starting Mission 7 - Project 10 ---")
    app.invoke({
        "logs": [],
        "attempts": 0,
        "error": None,
        "decision": None
    })

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "attempts": 0, "error": None, "decision": None})
