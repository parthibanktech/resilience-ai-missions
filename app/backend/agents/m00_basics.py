import sys
import os
# Ensure parent directory is in path for 'utils' and other modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from typing import List, TypedDict
from pydantic import BaseModel, Field # For structured output

try:
    from .utils import visualize_graph
except ImportError:
    from utils import visualize_graph

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

# Define the schema for our classification output
class Classification(BaseModel):
    task_type: str = Field(description="The category of the helpdesk task")


class State(TypedDict):
    logs: list[str]
    user_request: str
    available_tasks: List[str]  # Dynamic task list
    task_type: str
    answer: str


def title(text):
    print()
    print("=" * 80)
    print(text)
    print("=" * 80)


def classify_node(state):
    # Prepare the LLM with structured output
    structured_llm = llm.with_structured_output(Classification)
    
    # We build the prompt using the 'available_tasks' from the State
    tasks_str = "\n".join([f"- {task}" for task in state["available_tasks"]])
    
    prompt = f"""
You are a helpdesk triage agent.

Classify this user request into exactly one of these task types:
{tasks_str}

User request: {state["user_request"]}
"""
    # Invoke and get a typed object back
    result = structured_llm.invoke(prompt)
    
    log = f"[CLASSIFY] The LLM classified the request as: {result.task_type}"
    print(log)
    return {"task_type": result.task_type, "logs": state.get("logs", []) + [log]}


def act_node(state):
    # Generate a simple agent response based on the chosen task type from state.
    prompt = f"""
You are an internal IT helpdesk agent.

Task type: {state["task_type"]}
User request: {state["user_request"]}

Give a short helpful response in one or two sentences.
"""
    response = llm.invoke(prompt)
    answer = response.content.strip()

    log = "[ACT] The agent generated the response."
    print(log)
    return {"answer": answer, "logs": state.get("logs", []) + [log]}


def finish_node(state):
    log = f"[FINAL ANSWER] {state['answer']}"
    print(log)
    return {
        "logs": state.get("logs", []) + [log],
        "final_outcome": {
            "summary": "Agentic Inquiry Resolved",
            "details": {
                "Request": state.get("user_request"),
                "Task Type": state.get("task_type"),
                "Resolution": state.get("answer")
            }
        }
    }


builder = StateGraph(State)
builder.add_node("classify", classify_node)
builder.add_node("act", act_node)
builder.add_node("finish", finish_node)
builder.add_edge(START, "classify")
builder.add_edge("classify", "act")
builder.add_edge("act", "finish")
builder.add_edge("finish", END)

app = builder.compile()

def main():
    title("Mission 7 - 00 LangGraph Agent Basics")
    visualize_graph(app, "00_langgraph_agent_basics.png")

    app.invoke(
        {
            "user_request": "Check device status for employee E-102",
            "available_tasks": ["device_lookup", "policy_lookup", "general_helpdesk"],
            "task_type": "",
            "answer": "",
            "logs": []
        }
    )


def run_agent(user_input: str):
    return app.invoke(
        {
            "user_request": user_input,
            "available_tasks": ["device_lookup", "policy_lookup", "general_helpdesk"],
            "task_type": "",
            "answer": "",
            "logs": []
        }
    )


if __name__ == "__main__":
    main()
