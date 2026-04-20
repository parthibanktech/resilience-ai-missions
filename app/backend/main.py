from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import importlib
import sys
import os

# Ensure agents can be found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(title="Autonomous Resilience AI Lab")

# Enable CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class AgentRequest(BaseModel):
    mission_id: str
    user_input: str

class AgentResponse(BaseModel):
    status: str
    logs: List[str]
    final_output: Optional[dict]
    detail: Optional[str] = None

@app.get("/")
def health_check():
    return {"status": "online", "engine": "LangGraph Self-Healing"}

@app.post("/run-mission", response_model=AgentResponse)
async def run_mission(request: AgentRequest):
    """
    Dynamically loads and runs a mission, capturing real-time execution steps.
    """
    try:
      module_path = f"agents.{request.mission_id}"
      agent_module = importlib.import_module(module_path)
      
      # We need the compiled app to stream events
      # Most modules have a run_agent that compiles and invokes
      # We'll try to find the 'app' or re-compile if possible
      
      import io
      import contextlib

      execution_logs = []
      final_result = None

      if hasattr(agent_module, "run_agent"):
          # Capture all print statements during execution
          f = io.StringIO()
          with contextlib.redirect_stdout(f):
              final_state = agent_module.run_agent(request.user_input)
          
          final_result = final_state
          
          # Combine captured stdout with internal state logs if they exist
          raw_stdout = f.getvalue().strip()
          if raw_stdout:
             execution_logs.extend([line for line in raw_stdout.split('\n') if line.strip()])
          
          if isinstance(final_state, dict) and "logs" in final_state:
              # Avoid duplicates if nodes already log what they print
              for log in final_state["logs"]:
                  if log not in execution_logs:
                      execution_logs.append(log)
          
          if not execution_logs:
              # Fallback summary if no output captured
              execution_logs.append(f"[INIT] Executing {request.mission_id}...")
              if "error" in final_state and final_state["error"]:
                  execution_logs.append(f"[DIAGNOSTIC] Detected failure: {final_state['error'].get('msg', 'Unknown')}")
                  execution_logs.append("[HEALING] Autonomous repair cycle triggered.")
              if "result" in final_state or "answer" in final_state:
                  execution_logs.append("[SUCCESS] Convergence reached.")
      
      # Clean up the final result to avoid visible duplication in Metadata
      clean_result = {}
      if isinstance(final_result, dict):
          clean_result = {k: v for k, v in final_result.items() if k != "logs"}
      else:
          clean_result = final_result

      return AgentResponse(
          status="success",
          logs=execution_logs,
          final_output=clean_result
      )
    except Exception as e:
      import traceback
      error_detail = traceback.format_exc()
      print(f"Engine Error: {error_detail}")
      return AgentResponse(
          status="error",
          logs=[f"[ERROR] Engine state mismatch: {str(e)}"],
          final_output={"error": str(e), "traceback": error_detail},
          detail=str(e)
      )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
