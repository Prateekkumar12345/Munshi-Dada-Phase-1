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
  POST /classify?message=transformer%20ho%20gaya
  Response examples:
    - {"intent": "/complete", "id": 2}
    - {"intent": "/assign", "id": "@8295466423"}
    - {"intent": "/update", "id": 5}
    - {"intent": "/issue", "id": 7}
    - {"intent": "/resolve", "id": 3}
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
    description="Pure intent classifier — returns intent and optional IDs for tasks, updates, issues, resolves, and assigns",
    version="3.2.0",
    lifespan=lifespan,
)


# ─────────────────────────────────────────────────────────────
# REQUEST / RESPONSE MODELS
# ─────────────────────────────────────────────────────────────
class ClassifyResponse(BaseModel):
    intent: str
    id: Optional[Union[int, str]] = None  # Can be numeric ID or string for @mentions


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
    message: str = Query(..., description="Message from worker", example="/complete 2")
):
    """
    Pure intent classifier - Returns intent and optional IDs.
    
    Examples:
    - "transformer ho gaya" → {"intent": "/complete", "id": null}
    - "/complete 2" → {"intent": "/complete", "id": 2}
    - "/assign @8295466423 wiring karo" → {"intent": "/assign", "id": "@8295466423"}
    - "/assign 8295466423" → {"intent": "/assign", "id": "8295466423"}
    - "/update 5 wiring done" → {"intent": "/update", "id": 5}
    - "/issue 7 generator not working" → {"intent": "/issue", "id": 7}
    - "/resolve 3" → {"intent": "/resolve", "id": 3}
    - "/tasks" → {"intent": "/tasks"}
    - "/present" → {"intent": "/present"}
    """
    
    # First check if it's a slash command
    command_result = command_parser.parse(message)
    
    if command_result:
        intent = command_result.get("intent")
        extracted_id = command_result.get("id")
        
        # Return response with id if present
        if extracted_id is not None:
            return ClassifyResponse(intent=intent, id=extracted_id)
        else:
            return ClassifyResponse(intent=intent)
    
    # Otherwise use GPT for natural language classification
    result = classifier.classify(message)
    intent = result.get("intent", "general_chat")
    extracted_id = result.get("id")
    
    # Return response with id if present
    if extracted_id is not None:
        return ClassifyResponse(intent=intent, id=extracted_id)
    else:
        return ClassifyResponse(intent=intent)


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
        "version": "3.2.0",
        "endpoint": "POST /classify?message=your_message_here",
        "examples": {
            "complete_task": {
                "/complete 2": {"intent": "/complete", "id": 2},
                "/complete": {"intent": "/complete", "id": None},
                "transformer ho gaya": {"intent": "/complete", "id": None}
            },
            "assign_task": {
                "/assign @8295466423 wiring karo": {"intent": "/assign", "id": "@8295466423"},
                "/assign 8295466423": {"intent": "/assign", "id": "8295466423"},
                "/assign": {"intent": "/assign", "id": None}
            },
            "update_task": {
                "/update 5 wiring done": {"intent": "/update", "id": 5},
                "/update": {"intent": "/update", "id": None}
            },
            "report_issue": {
                "/issue 7 generator not working": {"intent": "/issue", "id": 7},
                "/issue": {"intent": "/issue", "id": None}
            },
            "resolve_issue": {
                "/resolve 3": {"intent": "/resolve", "id": 3},
                "/resolve": {"intent": "/resolve", "id": None}
            },
            "other_commands": {
                "/tasks": {"intent": "/tasks"},
                "/present": {"intent": "/present"},
                "/absent": {"intent": "/absent"},
                "/issues": {"intent": "/issues"},
                "/members": {"intent": "/members"},
                "/report": {"intent": "/report"},
                "/help": {"intent": "help"}
            }
        },
        "supported_intents": [
            "present", "absent", "/tasks", "/complete", "/assign", 
            "/update", "/issue", "/issues", "/resolve", "/members", 
            "/report", "help", "general_chat"
        ],
        "id_types": {
            "/complete": "numeric (task ID)",
            "/assign": "string (@mention or phone number)",
            "/update": "numeric (task ID)",
            "/issue": "numeric (issue ID)",
            "/resolve": "numeric (issue ID)"
        }
    }


# ─────────────────────────────────────────────────────────────
# ENTRYPOINT
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)