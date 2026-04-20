# 🛡️ Autonomous Resilience AI Lab
## The Industry Standard for Self-Healing AI Agent Workflows

Welcome to the **Autonomous Resilience AI Lab.** This repository contains a curated sequence of **12 Mission Projects** that demonstrate how to build "indestructible" AI agents using **LangGraph**, **Pydantic**, and **Structured Output.**

Traditional AI agents fail when they hit an error. These agents **Self-Heal.**

---

## 🏛️ System Architecture
The platform is built as a **Full-Stack AI Lab**:
- 🧠 **Backend (FastAPI)**: Serves 12 specialized LangGraph agents.
- 💻 **Frontend (React)**: A premium dashboard visualizing the "Healing Loops" in real-time.
- 🛠️ **Engine (LangGraph)**: Manages state, cyclic transitions, and autonomous recovery logic.
- 📦 **Infrastructure**: Dockerized and ready for [Render.com](https://render.com) or any cloud provider.

---

## 🎖️ The 12 Missions of Resilience
Every mission in this repository teaches a specific "Self-Healing" pattern:

| Mission | Title | Technical Pattern | Purpose |
| :--- | :--- | :--- | :--- |
| **M00** | **Agent Basics** | Entry Points & State | Foundations of LangGraph. |
| **M01** | **Fragile Demo** | Zero-Healing | Demonstrates how easily standard agents fail. |
| **M02** | **Self-Healing** | `try/except` Feedback | The first "Loop" that catches and fixes code errors. |
| **M03** | **Diagnostic Router** | Structured Diagnosis | AI identifies the *type* of error before repairing. |
| **M04** | **Payload Repair** | Data Validation | Correcting missing or malformed JSON data. |
| **M05** | **Tool Query Repair** | Query Refinement | Rewriting vague search queries for API success. |
| **M06** | **Prompt Repair** | Meta-Prompting | Agent autonomously redesigns its own instructions. |
| **M07** | **Workflow Repair** | Logical Re-Sequencing | AI re-orders its steps to fix logic errors. |
| **M08** | **Persistence** | Memory Checkpoints | Saving state so agents can resume after a crash. |
| **M09** | **Master Brain** | Multi-Agent Loop | A central orchestrator managing global healing. |
| **M10** | **Safety Escalation** | Hard-Stop Fallback | Graceful human escalation for high-risk errors. |
| **M11** | **Workflow Template** | Modular Baseline | A production-grade boilerplate for new agents. |
| **M12** | **FINAL CAPSTONE** | Full Integration | The ultimate IT Helpdesk agent (The LinkedIn Demo). |

---

## 🚀 Deployment Guide (Render.com)

This project is optimized for **Render**. Follow these steps:

1.  **Repo Setup**: Create a new GitHub repository and push this code.
2.  **Web Service**:
    *   **Root Directory**: `app/backend`
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3.  **Env Variables**:
    *   `OPENAI_API_KEY`: Your key.
    *   `PYTHONPATH`: `.` (This is critical for finding the `agents` package).

---

## 🎯 Impact & Value Proposition
In a production environment, AI downtime costs money. By moving from **M01 (Fragile)** to **M12 (Resilient)**, you are implementing the **"Corrective RAG"** and **"Self-Reflective Agent"** patterns popularized by researchers at Google and Stanford.

**"We don't just build agents that work. We build agents that recover."**

---

### Developed for the [Your Hackathon Name]
*Created by [Your Name]*
