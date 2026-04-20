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

# Initialize components
load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =========================================================================================
# 1. STRUCTURED OUTPUT MODELS
# =========================================================================================

class ToolQuery(BaseModel):
    """The specific query string expected by the policy tool."""
    query: str = Field(description="The refined lookup string (must include 'policy' or 'device')")

# =========================================================================================
# 2. GRAPH STATE
# =========================================================================================

class State(TypedDict):
    logs: list[str]
    user_input: str      # Human request
    policy_query: str    # Current query string
    error: Optional[dict]# Captured tool error
    policy_result: Optional[str] # Tool response
    iterations: int      # Safety counter

# =========================================================================================
# 3. TOOL SIMULATOR
# =========================================================================================

def fake_policy_tool(query: str):
    # This tool is picky: it requires specific keywords.
    query_lower = query.lower()
    if "policy" not in query_lower and "device" not in query_lower:
        raise ValueError("UNDERSPECIFIED: Query must contain the word 'policy' or 'device'.")
    
    # Dynamic response based on keywords
    topic = "General"
    if "vpn" in query_lower: topic = "VPN Security"
    elif "laptop" in query_lower: topic = "Hardware"
    elif "vacation" in query_lower: topic = "Leave"
    
    return f"SUCCESS: {topic} policy identified. Requirement: Manager approval necessary for '{query}'."

# =========================================================================================
# 4. GRAPH NODES
# =========================================================================================

def agent_node(state: State):
    """The Agent makes a 'First Guess' (intentionally vague for the demo)."""
    log = "[AGENT] Booting initial inquiry engine..."
    print(log)
    return {
        "policy_query": "approval", 
        "iterations": 0,
        "logs": state.get("logs", []) + [log]
    }

def tool_node(state: State):
    """Executes the policy lookup and catches schema/call errors."""
    log = f"[TOOL] Attempting query: '{state['policy_query']}'"
    print(log)
    try:
        result = fake_policy_tool(state["policy_query"])
        success_log = f"[TOOL SUCCESS] {result}"
        print(success_log)
        return {"policy_result": result, "error": None, "logs": state.get("logs", []) + [log, success_log]}
    except Exception as e:
        error_msg = str(e)
        fail_log = f"[TOOL FAILURE] {error_msg}"
        print(fail_log)
        return {"error": {"msg": error_msg}, "policy_result": None, "logs": state.get("logs", []) + [log, fail_log]}

def repair_node(state: State):
    """The Repair Brain rewrites the query based on the specific error message."""
    log = "[REPAIR] Refining the tool query based on feedback..."
    print(log)
    structured_llm = llm.with_structured_output(ToolQuery)
    
    prompt = f"""
    The original lookup for '{state['user_input']}' failed.
    Error from tool: {state['error']['msg']}
    
    Rewrite the query so it fulfills the tool's requirements.
    Include necessary keywords like 'policy' or 'device'.
    """
    
    refined = structured_llm.invoke(prompt)
    repair_log = f"[REPAIR] New Optimized Query: '{refined.query}'"
    print(repair_log)
    
    return {
        "policy_query": refined.query, 
        "iterations": state["iterations"] + 1,
        "logs": state.get("logs", []) + [log, repair_log]
    }

# =========================================================================================
# 5. CYCLIC ROUTING
# =========================================================================================

def route_next(state: State):
    if state.get("policy_result"):
        return "end"
    
    # Allow 2 repair attempts
    if state["iterations"] < 2:
        return "repair"
    
    return "end"

# =========================================================================================
# 6. GRAPH ASSEMBLY
# =========================================================================================

# --- Build the Graph at Module Level ---
builder = StateGraph(State)
builder.add_node("agent", agent_node)
builder.add_node("tool", tool_node)
builder.add_node("repair", repair_node)
def finish_node(state: State):
    """Final summarizes the result for the UI summary section."""
    log = "[DONE] Policy inquiry closed."
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Autonomous Policy Lookup Success",
            "details": {
                "Inquiry": state.get("user_input"),
                "Final Query": state.get("policy_query"),
                "Result": state.get("policy_result")
            }
        }
    }

builder.add_node("finish", finish_node)
builder.add_edge(START, "agent")
builder.add_edge("agent", "tool")
builder.add_edge("repair", "tool")
builder.add_conditional_edges("tool", route_next, {"repair": "repair", "end": "finish"})
builder.add_edge("finish", END)
app = builder.compile()

def main():
    visualize_graph(app, "05_tool_call_repair_modern.png")
    print("\n--- Starting Mission 7 - Project 05 ---")
    app.invoke({
        "logs": [],
        "user_input": "Check device policy for laptop approvals",
        "policy_query": "",
        "error": None,
        "policy_result": None,
        "iterations": 0
    })

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "policy_query": "", "error": None, "policy_result": None, "iterations": 0})
