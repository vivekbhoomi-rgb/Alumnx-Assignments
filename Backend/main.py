"""Simple demo backend: route question -> fetch dashboard data -> LLM writes the answer."""
import json
import os
import re
from pathlib import Path

import anthropic
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv(Path(__file__).parent.parent / ".env")

DASHBOARD = os.getenv("DASHBOARD_BASE_URL", "https://trainer-central-assigments-api.onrender.com")
MODEL = os.getenv("CHAT_MODEL", "claude-sonnet-5-5")
llm = anthropic.AsyncAnthropic()

app = FastAPI(title="Assignment Chatbot API")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in os.getenv(
                       "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:8001").split(",")],
                   allow_methods=["*"], allow_headers=["*"])

SYSTEM = ("You answer questions about an assignment-submission dashboard using ONLY the JSON data "
          "provided. Never invent numbers. Be brief. Each learner entry is one posted submission "
          "notification; 'submissions' is the count.")


async def get(path: str, **params):
    async with httpx.AsyncClient(timeout=90) as c:
        r = await c.get(f"{DASHBOARD}{path}", params=params)
        r.raise_for_status()
        return r.json()


async def fetch_data(question: str):
    """Keyword routing to the dashboard endpoint that can answer the question."""
    q = question.lower()
    learners = await get("/api/learners")
    # a learner is mentioned if any word (3+ letters) of their name/email matches the question
    words = set(re.findall(r"[a-z0-9]{3,}", q))
    matched = [l for l in learners["items"]
               if words & set(re.findall(r"[a-z0-9]{3,}", l["learner"].lower()))]
    if matched:
        return "/api/learners (matched learners)", matched
    if re.search(r"per day|daily|trend|total|stats|day", q):
        return "/api/stats", await get("/api/stats")
    return "/api/learners", learners


class ChatRequest(BaseModel):
    message: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    try:
        source, data = await fetch_data(req.message)
        resp = await llm.messages.create(
            model=MODEL, max_tokens=500, system=SYSTEM,
            messages=[{"role": "user",
                       "content": f"Question: {req.message}\n\nData from {source}:\n{json.dumps(data)}"}],
        )
        reply = "".join(b.text for b in resp.content if b.type == "text")
        return {"reply": reply, "source": source}
    except (httpx.HTTPError, anthropic.APIError) as exc:
        raise HTTPException(502, str(exc))
