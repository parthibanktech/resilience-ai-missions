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
    
    return "SUCCESS: Laptop device policy found. Manager approval required for Remote Work."

# =========================================================================================
# 4. GRAPH NODES
# =========================================================================================

def agent_node(state: State):
    """The Agent makes a 'First Guess' (intentionally vague for the demo)."""
    # Force a failure for the demo by only allowing 1 word
    print("[AGENT] Creating initial (vague) query...")
    return {
        "policy_query": "approval", 
        "iterations": 0
    }

def tool_node(state: State):
    """Executes the policy lookup and catches schema/call errors."""
    print(f"[TOOL] Attempting query: '{state['policy_query']}'")
    try:
        result = fake_policy_tool(state["policy_query"])
        print(f"[TOOL SUCCESS] {result}")
        return {"policy_result": result, "error": None}
    except Exception as e:
        error_msg = str(e)
        print(f"[TOOL FAILURE] {error_msg}")
        return {"error": {"msg": error_msg}, "policy_result": None}

def repair_node(state: State):
    """The Repair Brain rewrites the query based on the specific error message."""
    print("[REPAIR] Refining the tool query based on feedback...")
    structured_llm = llm.with_structured_output(ToolQuery)
    
    prompt = f"""
    The original lookup for '{state['user_input']}' failed.
    Error from tool: {state['error']['msg']}
    
    Rewrite the query so it fulfills the tool's requirements.
    Include necessary keywords like 'policy' or 'device'.
    """
    
    refined = structured_llm.invoke(prompt)
    print(f"[REPAIR] New Optimized Query: '{refined.query}'")
    
    return {
        "policy_query": refined.query, 
        "iterations": state["iterations"] + 1
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

def main():
    builder = StateGraph(State)

    builder.add_node("agent", agent_node)
    builder.add_node("tool", tool_node)
    builder.add_node("repair", repair_node)

    builder.add_edge(START, "agent")
    builder.add_edge("agent", "tool")
    
    # THE REPAIR LOOP
    builder.add_edge("repair", "tool")

    builder.add_conditional_edges(
        "tool",
        route_next,
        {
            "repair": "repair",
            "end": END
        }
    )

    app = builder.compile()
    visualize_graph(app, "05_tool_call_repair_modern.png")

    print("\n--- Starting Mission 7 - Project 05 (Tool Query Repair) ---")
    app.invoke({
        "user_input": "Check device policy for laptop approvals",
        "policy_query": "",
        "error": None,
        "policy_result": None,
        "iterations": 0
    })

if __name__ == "__main__":
    main()


def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "policy_query": None, "error": None, "policy_result": None, "iterations": 0})
