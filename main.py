# """
# main.py — FastAPI backend for Pure Intent Classifier
# Run: uvicorn main:app --reload

# Endpoint:
#   POST /classify?message=transformer%20ho%20gaya
#   Response: {"intent": "complete_task"}
# """

# from fastapi import FastAPI, Query
# from pydantic import BaseModel
# from bot_engine import IntentClassifier, CommandParser
# from contextlib import asynccontextmanager
# import uvicorn

# # ─────────────────────────────────────────────────────────────
# # LIFESPAN — Load classifier once at startup
# # ─────────────────────────────────────────────────────────────
# classifier: IntentClassifier = None
# command_parser: CommandParser = None

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     global classifier, command_parser
#     print("⏳ Loading Intent Classifier…")
#     classifier = IntentClassifier()
#     command_parser = CommandParser()
#     print("✅ Intent Classifier ready.")
#     yield
#     print("🛑 Shutting down.")

# app = FastAPI(
#     title="Worker Intent Classifier API",
#     description="Pure intent classifier — returns only the intent",
#     version="3.0.0",
#     lifespan=lifespan,
# )


# # ─────────────────────────────────────────────────────────────
# # REQUEST / RESPONSE MODELS
# # ─────────────────────────────────────────────────────────────
# class ClassifyResponse(BaseModel):
#     intent: str


# # ─────────────────────────────────────────────────────────────
# # ENDPOINT — Classify intent
# # ─────────────────────────────────────────────────────────────
# @app.post(
#     "/classify",
#     response_model=ClassifyResponse,
#     summary="Classify worker message intent",
#     tags=["Classification"],
# )
# async def classify(
#     message: str = Query(..., description="Message from worker", example="transformer ho gaya")
# ):
#     """
#     Pure intent classifier - Returns only the intent.
    
#     Examples:
#     - "transformer ho gaya" → {"intent": "complete_task"}
#     - "main present hu" → {"intent": "present"}
#     - "/tasks" → {"intent": "view_tasks"}
#     - "wiring mein problem hai" → {"intent": "report_issue"}
#     """
    
#     # First check if it's a slash command
#     command_result = command_parser.parse(message)
    
#     if command_result:
#         return ClassifyResponse(intent=command_result["intent"])
    
#     # Otherwise use GPT for natural language classification
#     result = classifier.classify(message)
    
#     return ClassifyResponse(intent=result.get("intent", "general_chat"))


# # ─────────────────────────────────────────────────────────────
# # HEALTH CHECK
# # ─────────────────────────────────────────────────────────────
# @app.get("/health", tags=["Meta"])
# async def health():
#     return {"status": "ok"}


# # ─────────────────────────────────────────────────────────────
# # HELP ENDPOINT
# # ─────────────────────────────────────────────────────────────
# @app.get("/", tags=["Meta"])
# async def root():
#     return {
#         "service": "Worker Intent Classifier API",
#         "version": "3.0.0",
#         "endpoint": "POST /classify?message=your_message_here",
#         "example": "POST /classify?message=transformer%20ho%20gaya",
#         "response": {"intent": "complete_task"},
#         "supported_intents": [
#             "present", "absent", "view_tasks", "complete_task", 
#             "assign_task", "update_task", "report_issue", "view_issues",
#             "resolve_issue", "view_members", "generate_report", "help", "general_chat"
#         ]
#     }


# # ─────────────────────────────────────────────────────────────
# # ENTRYPOINT
# # ─────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


"""
main.py — FastAPI backend for Pure Intent Classifier
Run: uvicorn main:app --reload

Endpoint:
  POST /classify?message=2%20ghante%20baad%20complete%20karna%20hai
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, Union
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
    description="Pure intent classifier — returns intent, IDs, and extracted date/time",
    version="3.4.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────
class ClassifyResponse(BaseModel):
    intent: str
    id: Optional[Union[int, str]] = None
    date: Optional[str] = None  # Date in YYYY-MM-DD format
    datetime: Optional[str] = None  # Full datetime in ISO format
    time: Optional[str] = None  # Time in HH:MM:SS format


# ─────────────────────────────────────────────────────────────
# ENDPOINT — Classify intent
# ─────────────────────────────────────────────────────────────
@app.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Classify worker message intent with date/time extraction",
    tags=["Classification"],
)
async def classify(
    message: str = Query(..., description="Message from worker", example="2 ghante baad complete karna hai")
):
    """
    Pure intent classifier - Returns intent, IDs, and extracted date/time.
    
    Examples:
    - "2 ghante baad complete karna hai" → {"intent": "/complete", "date": "2026-04-18", "datetime": "2026-04-18T15:30:00", "time": "15:30:00"}
    - "3 hafte mein task khatam karo" → {"intent": "/complete", "date": "2026-05-09", "datetime": "2026-05-09T12:00:00"}
    - "2 mahine baad report chahiye" → {"intent": "/report", "date": "2026-06-18"}
    - "1 saal mein promotion" → {"intent": "general_chat", "date": "2027-04-18"}
    - "aaj mai aaya hu" → {"intent": "/present", "date": "2026-04-18"}
    - "/complete 2" → {"intent": "/complete", "id": 2, "date": null}
    """
    
    # First check if it's a slash command
    command_result = command_parser.parse(message)
    
    if command_result:
        return ClassifyResponse(
            intent=command_result.get("intent"),
            id=command_result.get("id"),
            date=command_result.get("date"),
            datetime=command_result.get("datetime"),
            time=command_result.get("time")
        )
    
    # Otherwise use GPT for natural language classification
    result = classifier.classify(message)
    
    return ClassifyResponse(
        intent=result.get("intent", "general_chat"),
        id=result.get("id"),
        date=result.get("date"),
        datetime=result.get("datetime"),
        time=result.get("time")
    )


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
    from datetime import datetime
    now = datetime.now()
    
    return {
        "service": "Worker Intent Classifier API",
        "version": "3.4.0",
        "endpoint": "POST /classify?message=your_message_here",
        "current_datetime": now.isoformat(),
        "examples": {
            "time_based": {
                "2 ghante baad complete karna hai": {
                    "intent": "/complete",
                    "datetime": (now + __import__('datetime').timedelta(hours=2)).isoformat()
                },
                "30 minutes mein meeting": {
                    "intent": "general_chat",
                    "datetime": (now + __import__('datetime').timedelta(minutes=30)).isoformat()
                }
            },
            "weeks_months_years": {
                "3 hafte mein task khatam karo": {"intent": "/complete", "date": (now + __import__('datetime').timedelta(weeks=3)).strftime("%Y-%m-%d")},
                "2 mahine baad report chahiye": {"intent": "/report", "date": "2026-06-18"},
                "1 saal mein promotion": {"intent": "general_chat", "date": "2027-04-18"}
            },
            "relative_dates": {
                "aaj mai aaya hu": {"intent": "/present", "date": now.strftime("%Y-%m-%d")},
                "kal nahi aa sakta": {"intent": "/absent", "date": (now + __import__('datetime').timedelta(days=1)).strftime("%Y-%m-%d")},
                "parso complete karna hai": {"intent": "/complete", "date": (now + __import__('datetime').timedelta(days=2)).strftime("%Y-%m-%d")}
            },
            "slash_commands": {
                "/complete 2": {"intent": "/complete", "id": 2},
                "/assign @8295466423": {"intent": "/assign", "id": "@8295466423"}
            }
        },
        "supported_units": [
            "seconds (सेकंड)", "minutes (मिनट)", "hours (घंटे)",
            "days (दिन)", "weeks (हफ्ते)", "months (महीने)", "years (साल)"
        ],
        "supported_languages": ["English", "Hindi", "Hinglish"]
    }


# ─────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)