# 🛠️ Local Setup & Testing Guide

Follow these steps to run the Autonomous Resilience Lab on your machine before deploying to Render.

---

## 1. Environment Preparation
Ensure you have an `.env` file in the `app/backend/` directory with your OpenAI key:

```bash
# app/backend/.env
OPENAI_API_KEY=sk-your-key-here
```

---

## 2. Start the Backend (FastAPI)
Open a new terminal window:

```bash
# 1. Navigate to the backend
cd app/backend

# 2. Install dependencies (if using uv)
uv pip install -r requirements.txt

# 3. Launch the server
uvicorn main:app --reload --port 8000
```
*The API will be live at: http://localhost:8000*

---

## 3. Start the Frontend (React)
Open a **second** terminal window:

```bash
# 1. Navigate to the frontend
cd app/frontend

# 2. Install dependencies
npm install

# 3. Launch the dev server
npm run dev
```
*The Dashboard will be live at: http://localhost:5173 (usually)*

---

## 4. Testing the Lab
1.  Open your browser to the local URL.
2.  Select **Mission 12 (Capstone)** from the dropdown.
3.  Type a request: *"Employee E-999 needs a hardware check."*
4.  Watch the **Terminal Log** in the Dashboard. You should see the `[HEALING]` messages appearing as the agent fixes its own mistakes!

---

## 🛑 Troubleshooting
- **ModuleNotFoundError**: Ensure you are running the `uvicorn` command from inside the `app/backend` directory.
- **CORS Error**: The `main.py` is configured for `allow_origins=["*"]`, so it should connect to any local port automatically.
