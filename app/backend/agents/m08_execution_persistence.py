import sys
import os
# Ensure parent directory is in path for 'utils' and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Optional, TypedDict, Literal
from pydantic import BaseModel, Field

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver  # Persistence!
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

class RetryDecision(BaseModel):
    """The AI's decision on whether to continue or give up."""
    decision: Literal["retry", "hard_stop"] = Field(description="Choice: 'retry' or 'hard_stop'")
    justification: str = Field(description="Logic behind the retry or stop.")

class State(TypedDict):
    logs: list[str]
    user_input: str
    attempts: int
    error: Optional[dict]
    decision: Optional[str]
    result: Optional[str]

# =========================================================================================
# 2. FLAKY INFRASTRUCTURE (Simulator)
# =========================================================================================

def flaky_network_call(attempt_number: int, user_req: str):
    # This simulation will FAIL exactly 2 times and then work on the 3rd.
    if attempt_number < 3:
        raise ConnectionError(f"Network Timeout (Attempt {attempt_number}). Service unavailable.")
    return f"SUCCESS: Task '{user_req}' completed on attempt {attempt_number}."

# =========================================================================================
# 3. GRAPH NODES
# =========================================================================================

def execute_node(state: State):
    """Network Execution: Tries the flaky call."""
    it = state.get("attempts", 0) + 1
    user_req = state.get("user_input", "System sync")
    print(f"\n[EXECUTE] Attempt #{it}")
    
    try:
        msg = flaky_network_call(it, user_req)
        print(f"[SUCCESS] {msg}")
        return {"result": msg, "error": None, "attempts": it}
    except Exception as e:
        error_msg = str(e)
        print(f"[FAILURE] {error_msg}")
        return {"error": {"msg": error_msg}, "result": None, "attempts": it}

def decide_node(state: State):
    """Router Node: Evaluates if a retry is worth it."""
    print("[DECISION] AI is evaluating the infrastructure failure...")
    structured_llm = llm.with_structured_output(RetryDecision)
    
    prompt = f"""
    Internal System Error: {state['error']['msg']}
    Attempts Made: {state['attempts']}
    
    Should we retry? 
    Guidelines: Retry if under 5 attempts. Stop if it seems like a fatal error.
    """
    
    outcome = structured_llm.invoke(prompt)
    print(f"[DECISION] Action: {outcome.decision} | Reason: {outcome.justification}")
    
    return {"decision": outcome.decision}

def pause_node(state: State):
    """Pause Node: This is where the graph stops for human or system resume."""
    print("[PAUSE] Hitting checkpoint... Releasing control to the main loop.")
    return {}

# =========================================================================================
# 4. CONDITIONAL LOGIC
# =========================================================================================

def route_after_execute(state: State):
    if state.get("result"): return "finish"
    return "decide"

def route_after_decide(state: State):
    if state["decision"] == "hard_stop": return "finish"
    return "pause" # If retry, hit the pause/checkpoint node

# =========================================================================================
# 5. ASSEMBLY WITH PERSISTENCE
# =========================================================================================

# --- Build the Graph at Module Level ---
builder = StateGraph(State)
builder.add_node("execute", execute_node)
builder.add_node("decide", decide_node)
builder.add_node("pause", pause_node)
def finish_node(state: State):
    """Summarizes success for the UI."""
    log = "[DONE] Mission finalized."
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Infrastructure Restoration Success",
            "details": {
                "Input": state.get("user_input"),
                "Total Attempts": state.get("attempts"),
                "Final Result": state.get("result")
            }
        }
    }

builder.add_node("finish", finish_node)
builder.add_edge(START, "execute")
builder.add_conditional_edges("execute", route_after_execute, {"decide": "decide", "finish": "finish"})
builder.add_conditional_edges("decide", route_after_decide, {"pause": "pause", "finish": "finish"})
builder.add_edge("pause", "execute")
builder.add_edge("finish", END)

memory = MemorySaver()
app = builder.compile(checkpointer=memory, interrupt_before=["pause"])

def main():
    visualize_graph(app, "08_retry_resume_modern.png")
    config = {"configurable": {"thread_id": "mission_7_retry_demo"}}
    print("\n--- Starting Mission 7 - Project 08 ---")
    app.invoke({
        "logs": [],
        "user_input": "Retrieve secure server logs",
        "attempts": 0,
        "error": None,
        "result": None,
        "decision": None
    }, config)

    while True:
        current_state = app.get_state(config)
        if not current_state.next: break
        print(f"[SYSTEM] Graph is paused. Resuming...")
        app.invoke(None, config)

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    # For the web demo, we skip the manual interrupt to show clear cyclic success
    # But we use a unique thread ID per run
    demo_app = builder.compile(checkpointer=MemorySaver())
    config = {"configurable": {"thread_id": "run_" + str(os.getpid())}}
    
    # We run until completion for the dashboard
    state = {"logs": [], "user_input": user_input, "attempts": 0, "error": None, "result": None, "decision": None}
    app_state = demo_app.invoke(state, config)
    
    # Simulate the resume loop if it pauses
    while True:
        thread_state = demo_app.get_state(config)
        if not thread_state.next: break
        app_state = demo_app.invoke(None, config)
        
    return app_state
