# """
# main.py — FastAPI backend for Pure Intent Classifier
# Run: uvicorn main:app --reload
# """

# from fastapi import FastAPI, Query
# from pydantic import BaseModel
# from typing import Optional, Union
# from bot_engine import IntentClassifier, CommandParser
# from contextlib import asynccontextmanager
# import uvicorn

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
#     description=(
#         "Pure intent classifier — returns intent, IDs, extracted date, department slug, "
#         "and professional responses only for general_chat"
#     ),
#     version="7.0.0",
#     lifespan=lifespan,
# )


# class ClassifyResponse(BaseModel):
#     intent: str
#     id: Optional[Union[int, str]] = None
#     worker_slug: Optional[str] = None
#     depart_slug: Optional[str] = None
#     deadline: Optional[str] = None
#     message: Optional[str] = None


# @app.post(
#     "/classify",
#     response_model=ClassifyResponse,
#     summary="Classify worker message intent with date extraction and department routing",
#     tags=["Classification"],
# )
# async def classify(
#     message: str = Query(
#         ...,
#         description="Message from worker or manager",
#         example="kal subah 10 bje tak warehouse khali krdo",
#     )
# ):
#     """
#     Pure intent classifier — returns intent, IDs, department, and extracted deadline.

#     **Response Fields:**
#     - `intent`: Classified intent (/tasks, /present, /absent, /complete, /assign, /depart_assign, /mgrassign, general_chat, etc.)
#     - `id`: Extracted task ID (for /complete, /mgrassign)
#     - `worker_slug`: Named person (for /assign or /mgrassign when a person is explicitly mentioned)
#     - `depart_slug`: Department (for /depart_assign only — when NO person is mentioned; one of: operations, sales, purchase, it)
#     - `deadline`: Extracted deadline in ISO format or YYYY-MM-DD
#     - `message`: Professional response (ONLY for general_chat intent)

#     **Intent routing (v7):**
#     - `/assign`        → person explicitly named via @mention or name + work instruction
#     - `/depart_assign` → work instruction with NO named person; department auto-detected
#     - `/mgrassign`     → specific task number assigned to someone, OR self-claim ("main karunga")
#     - `/tasks`         → user asking to VIEW their own task list only
#     """

#     command_result = command_parser.parse(message)
#     if command_result:
#         return ClassifyResponse(
#             intent=command_result.get("intent"),
#             id=command_result.get("id"),
#             worker_slug=command_result.get("worker_slug"),
#             depart_slug=command_result.get("depart_slug"),
#             deadline=command_result.get("deadline"),
#             message=None,
#         )

#     result = classifier.classify(message)

#     return ClassifyResponse(
#         intent=result.get("intent", "general_chat"),
#         id=result.get("id"),
#         worker_slug=result.get("worker_slug"),
#         depart_slug=result.get("depart_slug"),
#         deadline=result.get("deadline"),
#         message=result.get("message"),
#     )


# @app.get("/health", tags=["Meta"])
# async def health():
#     return {"status": "ok", "version": "7.0.0"}


# @app.get("/", tags=["Meta"])
# async def root():
#     from datetime import datetime
#     now = datetime.now()

#     return {
#         "service": "Worker Intent Classifier API",
#         "version": "7.0.0",
#         "endpoint": "POST /classify?message=your_message_here",
#         "current_datetime": now.isoformat(),
#         "whats_new_in_7_0": {
#             "/depart_assign_is_new": (
#                 "Work instructions with NO named person now return intent '/depart_assign' "
#                 "(previously they returned '/assign'). This is a breaking change."
#             ),
#             "/assign_person_only": (
#                 "'/assign' is now strictly for messages where a person is explicitly named "
#                 "via @mention or name. worker_slug will always be set for /assign."
#             ),
#             "clean_separation": (
#                 "/assign (person) vs /depart_assign (department) are now mutually exclusive."
#             ),
#         },
#         "departments": ["operations", "sales", "purchase", "it"],
#         "response_examples": {
#             "depart_assign_operations": {
#                 "input": "kal subah 10 bje tak warehouse khali krdo",
#                 "response": {
#                     "intent": "/depart_assign",
#                     "id": None,
#                     "worker_slug": None,
#                     "depart_slug": "operations",
#                     "deadline": "2026-05-17T10:00:00",
#                     "message": None,
#                 },
#             },
#             "depart_assign_sales": {
#                 "input": "invoice banao aur client ko bhejo",
#                 "response": {
#                     "intent": "/depart_assign",
#                     "id": None,
#                     "worker_slug": None,
#                     "depart_slug": "sales",
#                     "deadline": None,
#                     "message": None,
#                 },
#             },
#             "depart_assign_purchase": {
#                 "input": "raw material kharido 500 units",
#                 "response": {
#                     "intent": "/depart_assign",
#                     "id": None,
#                     "worker_slug": None,
#                     "depart_slug": "purchase",
#                     "deadline": None,
#                     "message": None,
#                 },
#             },
#             "depart_assign_it": {
#                 "input": "server down hai theek karo",
#                 "response": {
#                     "intent": "/depart_assign",
#                     "id": None,
#                     "worker_slug": None,
#                     "depart_slug": "it",
#                     "deadline": None,
#                     "message": None,
#                 },
#             },
#             "assign_with_mention": {
#                 "input": "kal subah 10 bje tak warehouse khali krdo @ajay",
#                 "response": {
#                     "intent": "/assign",
#                     "id": None,
#                     "worker_slug": "@ajay",
#                     "depart_slug": None,
#                     "deadline": "2026-05-17T10:00:00",
#                     "message": None,
#                 },
#             },
#             "assign_with_name": {
#                 "input": "ajay ko invoice bhejdo",
#                 "response": {
#                     "intent": "/assign",
#                     "id": None,
#                     "worker_slug": "ajay",
#                     "depart_slug": None,
#                     "deadline": None,
#                     "message": None,
#                 },
#             },
#             "view_tasks": {
#                 "input": "mera kaam dikhao",
#                 "response": {
#                     "intent": "/tasks",
#                     "id": None,
#                     "worker_slug": None,
#                     "depart_slug": None,
#                     "deadline": None,
#                     "message": None,
#                 },
#             },
#             "self_claim_no_task": {
#                 "input": "ye kaam mai khud karunga",
#                 "response": {
#                     "intent": "/mgrassign",
#                     "id": None,
#                     "worker_slug": "self",
#                     "depart_slug": None,
#                     "deadline": None,
#                     "message": None,
#                 },
#             },
#             "mgrassign": {
#                 "input": "task 32 @ajay ko do",
#                 "response": {
#                     "intent": "/mgrassign",
#                     "id": 32,
#                     "worker_slug": "@ajay",
#                     "depart_slug": None,
#                     "deadline": None,
#                     "message": None,
#                 },
#             },
#             "attendance": {
#                 "input": "aaj main aa gaya hu",
#                 "response": {
#                     "intent": "/present",
#                     "deadline": "2026-05-16",
#                     "message": None,
#                 },
#             },
#             "general_chat": {
#                 "input": "hello kaise ho",
#                 "response": {
#                     "intent": "general_chat",
#                     "worker_slug": None,
#                     "depart_slug": None,
#                     "message": "Thank you for your message...",
#                 },
#             },
#         },
#         "supported_languages": ["English", "Hindi", "Hinglish"],
#     }


# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

















"""
main.py
FastAPI Backend

Run:
uvicorn main:app --reload
"""

from contextlib import asynccontextmanager
from typing import Optional, Union

import uvicorn
from fastapi import FastAPI, Query
from pydantic import BaseModel

from bot_engine import (
    IntentClassifier,
    CommandParser,
)

# ============================================================
# GLOBALS
# ============================================================

classifier = None

command_parser = None

# ============================================================
# LIFESPAN
# ============================================================


@asynccontextmanager
async def lifespan(app: FastAPI):

    global classifier
    global command_parser

    print("⏳ Loading Hybrid Intent Classifier...")

    classifier = IntentClassifier()

    command_parser = CommandParser()

    print("✅ API Ready")

    yield

    print("🛑 Shutdown")


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Worker Intent Classification API",
    version="9.0.0",
    lifespan=lifespan,
)

# ============================================================
# RESPONSE MODEL
# ============================================================


class ClassifyResponse(BaseModel):

    intent: str

    id: Optional[Union[int, str]] = None

    worker_slug: Optional[str] = None

    depart_slug: Optional[str] = None

    deadline: Optional[str] = None

    message: Optional[str] = None


# ============================================================
# ROOT
# ============================================================


@app.get("/")
async def root():

    return {
        "service": "Hybrid Intent Classification API",
        "version": "9.0.0",
        "status": "running",
    }


# ============================================================
# HEALTH
# ============================================================


@app.get("/health")
async def health():

    return {
        "status": "ok",
    }


# ============================================================
# CLASSIFICATION ENDPOINT
# ============================================================


@app.post(
    "/classify",
    response_model=ClassifyResponse,
)
async def classify(
    message: str = Query(...)
):

    # ========================================================
    # COMMAND PARSER FIRST
    # ========================================================

    command_result = command_parser.parse(message)

    if command_result:
        return command_result

    # ========================================================
    # HYBRID CLASSIFIER
    # ========================================================

    result = classifier.classify(message)

    return result


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )