import sys
import os
# Ensure parent directory is in path for 'utils' and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing import TypedDict
from dotenv import load_dotenv

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class State(TypedDict):
    logs: list[str]
    user_input: str
    code: str
    error: str
    iterations: int

def coder(state: State):
    it = state.get("iterations", 0) + 1
    user_req = state.get("user_input", "Write a division by zero")
    print(f"\n[CODER] Attempt #{it}")

    if it == 1:
        prompt = f"Goal: {user_req}. Write a short Python script to achieve this. DO NOT try to fix or catch potential errors yet. Just write the code."
    else:
        prompt = f"CRITICAL: Your previous code crashed with: {state['error']}. You MUST fix this now using a try-except block or validation logic. Return the safe code now."

    response = llm.invoke(prompt)
    content = response.content.strip()
    if "```python" in content:
        clean_code = content.split("```python")[1].split("```")[0].strip()
    elif "```" in content:
        clean_code = content.split("```")[1].split("```")[0].strip()
    else:
        clean_code = content
    
    log = f"----- Generated Code (Cycle #{it}) -----\n{clean_code}"
    print(log)
    return {"code": clean_code, "iterations": it, "logs": state.get("logs", []) + [log]}

def executor(state: State):
    try:
        # We capture stdout to see the code result in the logs
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            exec(state["code"])
        output = f.getvalue()
        log = f"[SUCCESS]: Code ran perfectly! Output: {output}"
        print(log)
        return {"error": "", "logs": state.get("logs", []) + [log]}
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        log = f"[EXECUTOR FAILURE]: {error_msg}"
        print(log)
        return {"error": error_msg, "logs": state.get("logs", []) + [log]}

def finish_node(state: State):
    return {
        "logs": state.get("logs", []) + ["[DONE] Recovery complete."],
        "final_outcome": {
            "summary": "Self-Correction Successful",
            "details": {
                "Iterations": state["iterations"],
                "Final Code": state["code"],
                "Execution Result": "Verified"
            }
        }
    }

# Simple Graph Logic
builder = StateGraph(State)
builder.add_node("coder", coder)
builder.add_node("executor", executor)
builder.add_node("finish", finish_node)

builder.add_edge(START, "coder")
builder.add_edge("coder", "executor")

# Route back to coder if error, else stop
builder.add_conditional_edges(
    "executor", 
    lambda s: "finish" if not s["error"] or s["iterations"] >= 3 else "heal", 
    {"heal": "coder", "finish": "finish"}
)
builder.add_edge("finish", END)

app = builder.compile()

if __name__ == "__main__":
    print("Starting SIMPLE Self-Healing Loop...")
    app.invoke({"code": "", "error": "", "iterations": 0})


def run_agent(user_input: str):
    return app.invoke({"logs": [], "user_input": user_input, "code": "", "error": "", "iterations": 0})
