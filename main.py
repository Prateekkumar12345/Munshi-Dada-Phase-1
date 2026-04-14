"""
main.py — FastAPI backend for Pure Intent Classifier
Run: uvicorn main:app --reload

Endpoint:
  POST /classify?message=transformer%20ho%20gaya
  Response: {"intent": "complete_task"}
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from bot_engine import IntentClassifier, CommandParser
from contextlib import asynccontextmanager
import uvicorn

# ─────────────────────────────────────────────────────────────
# LIFESPAN — Load classifier once at startup
# ─────────────────────────────────────────────────────────────
classifier: IntentClassifier = None
command_parser: CommandParser = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global classifier, command_parser
    print("⏳ Loading Intent Classifier…")
    classifier = IntentClassifier()
    command_parser = CommandParser()
    print("✅ Intent Classifier ready.")
    yield
    print("🛑 Shutting down.")

app = FastAPI(
    title="Worker Intent Classifier API",
    description="Pure intent classifier — returns only the intent",
    version="3.0.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────
class ClassifyResponse(BaseModel):
    intent: str


# ─────────────────────────────────────────────────────────────
# ENDPOINT — Classify intent
# ─────────────────────────────────────────────────────────────
@app.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Classify worker message intent",
    tags=["Classification"],
)
async def classify(
    message: str = Query(..., description="Message from worker", example="transformer ho gaya")
):
    """
    Pure intent classifier - Returns only the intent.
    
    Examples:
    - "transformer ho gaya" → {"intent": "complete_task"}
    - "main present hu" → {"intent": "present"}
    - "/tasks" → {"intent": "view_tasks"}
    - "wiring mein problem hai" → {"intent": "report_issue"}
    """
    
    # First check if it's a slash command
    command_result = command_parser.parse(message)
    
    if command_result:
        return ClassifyResponse(intent=command_result["intent"])
    
    # Otherwise use GPT for natural language classification
    result = classifier.classify(message)
    
    return ClassifyResponse(intent=result.get("intent", "general_chat"))


# ─────────────────────────────────────────────────────────────
# HEALTH CHECK
# ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok"}


# ─────────────────────────────────────────────────────────────
# HELP ENDPOINT
# ─────────────────────────────────────────────────────────────
@app.get("/", tags=["Meta"])
async def root():
    return {
        "service": "Worker Intent Classifier API",
        "version": "3.0.0",
        "endpoint": "POST /classify?message=your_message_here",
        "example": "POST /classify?message=transformer%20ho%20gaya",
        "response": {"intent": "complete_task"},
        "supported_intents": [
            "present", "absent", "view_tasks", "complete_task", 
            "assign_task", "update_task", "report_issue", "view_issues",
            "resolve_issue", "view_members", "generate_report", "help", "general_chat"
        ]
    }


# ─────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)