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

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# =========================================================================================
# 1. THE DATA SCHEMA (What we want the Agent to produce)
# =========================================================================================

class EmployeeRequest(BaseModel):
    """The final structured extract we need."""
    employee_id: str = Field(description="Must start with 'E-' followed by numbers.")
    action: str = Field(description="The intent: 'lookup', 'update', or 'create'.")
    confidence: float = Field(description="Score between 0 and 1.")

# =========================================================================================
# 2. THE GRAPH STATE
# =========================================================================================

class State(TypedDict):
    logs: list[str]
    user_input: str
    system_prompt: str    # The "Instructions" that we will self-heal
    parsed_output: Optional[dict]
    error: Optional[dict]
    iterations: int

# =========================================================================================
# 3. GRAPH NODES
# =========================================================================================

def model_node(state: State):
    """Execution Node: Uses the current System Prompt to process input."""
    print(f"\n[MODEL] Attempting with prompt version {state['iterations'] + 1}...")
    
    # We use structured output, but we simulate a 'Validation Error' 
    # if the LLM doesn't have enough context.
    structured_llm = llm.with_structured_output(EmployeeRequest)
    
    try:
        # Combine instructions + input
        full_command = f"{state['system_prompt']}\n\nINPUT: {state['user_input']}"
        response = structured_llm.invoke(full_command)
        
        # DEMO TRICK: If confidence is not 1.0, we force a "Prompt Refinement" 
        if response.confidence < 1.0:
            raise ValueError(f"Confidence too low ({response.confidence}). Instructions need sharpening.")

        log = f"[MODEL SUCCESS] Extracted: {response.model_dump()}"
        print(log)
        return {"parsed_output": response.model_dump(), "error": None, "logs": state.get("logs", []) + [log]}
    
    except Exception as e:
        error_msg = str(e)
        fail_log = f"[MODEL FAILURE] Error: {error_msg}"
        print(fail_log)
        return {"error": {"msg": error_msg}, "parsed_output": None, "logs": state.get("logs", []) + [fail_log]}

def prompt_repair_node(state: State):
    """The Meta-Agent Node: It fixes the PROMPT, not the data."""
    print("[REPAIR] AI is redesigning the instructions to be more precise...")
    
    # We tell the LLM the REAL GOAL (user_input) so it stops fixing the joke
    # and starts fixing the functional instruction.
    repair_prompt = f"""
    You are a Prompt Engineer. Your previous instruction failed.
    The goal is to extract data for this specific request: '{state['user_input']}'
    
    Original Bad Prompt: {state['system_prompt']}
    Failure Error: {state['error']['msg']}
    
    Task: Redesign the System Prompt so it successfully extracts Employee ID, Action, and Confidence.
    Stop telling jokes. Focus on professional JSON extraction.
    Return ONLY the new prompt text.
    """
    
    new_prompt = llm.invoke(repair_prompt).content.strip()
    log = f"[REPAIR] AI redesigned the instruction strategy."
    repair_log = f"[REPAIR] New Prompt: {new_prompt[:100]}..."
    print(repair_log)
    
    return {
        "system_prompt": new_prompt, 
        "iterations": state["iterations"] + 1,
        "logs": state.get("logs", []) + [log, repair_log]
    }

# =========================================================================================
# 4. ROUTING LOGIC
# =========================================================================================

def route_next(state: State):
    if state.get("parsed_output"):
        return "finish"
    if state["iterations"] < 2:
        return "repair"
    return "finish"

def finish_node(state: State):
    log = "[DONE] Prompt engineering cycle closed."
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Autonomous Prompt Engineering Success",
            "details": {
                "Final System Prompt": state.get("system_prompt"),
                "Extraction Result": state.get("parsed_output"),
                "Refinement Cycles": state.get("iterations")
            }
        }
    }

# =========================================================================================
# 5. ASSEMBLY
# =========================================================================================

# --- Build the Graph at Module Level ---
builder = StateGraph(State)
builder.add_node("model", model_node)
builder.add_node("repair", prompt_repair_node)
builder.add_node("finish", finish_node)
builder.add_edge(START, "model")
builder.add_edge("repair", "model")
builder.add_conditional_edges("model", route_next, {"repair": "repair", "finish": "finish"})
builder.add_edge("finish", END)
app = builder.compile()

def main():
    visualize_graph(app, "06_prompt_repair_modern.png")
    print("\n--- Starting Mission 7 - Project 06 ---")
    
    # Start with a COMPLETELY USLESS prompt to force the AI to fix it.
    initial_prompt = "Tell me a funny joke about an employee named Dave."
    
    app.invoke({
        "logs": [],
        "user_input": "Employee E-999 wants a laptop lookup.",
        "system_prompt": initial_prompt,
        "parsed_output": None,
        "error": None,
        "iterations": 0
    })

if __name__ == "__main__":
    main()

def run_agent(user_input: str):
    # Start with a "joke" prompt to trigger the self-healing loop
    initial_prompt = "Tell a joke about IT departments."
    return app.invoke({"logs": [], "user_input": user_input, "system_prompt": initial_prompt, "parsed_output": None, "error": None, "iterations": 0})
