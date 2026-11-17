# Assignment Chatbot

- `Backend/` FastAPI. `POST /api/chat` sends the question to Claude, which calls tools that hit the
  Text Dashboard API (`/api/learners`, `/api/stats`, `/api/entries?q=`) and returns the answer.
- `Frontend/` React (Vite) chat UI.

## Run
Backend (needs `ANTHROPIC_API_KEY` in the root `.env`, already present):

    cd Backend
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

Frontend (needs Node.js 18+):

    cd Frontend
    npm install
    npm run dev      # http://localhost:5173

Optional env: `DASHBOARD_BASE_URL`, `CHAT_MODEL`, `CORS_ORIGINS` (backend); `VITE_API_URL` (frontend).
