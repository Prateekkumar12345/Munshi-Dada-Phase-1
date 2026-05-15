# """
# main.py — FastAPI backend for Pure Intent Classifier
# Run: uvicorn main:app --reload

# Endpoint:
#   POST /classify?message=2%20ghante%20baad%20complete%20karna%20hai
# """

# from fastapi import FastAPI, Query
# from pydantic import BaseModel
# from typing import Optional, Union
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
#     description="Pure intent classifier — returns intent, IDs, extracted date/time, and professional responses only for general_chat",
#     version="3.7.0",
#     lifespan=lifespan,
# )


# # ─────────────────────────────────────────────────────────────
# # REQUEST / RESPONSE MODELS
# # ─────────────────────────────────────────────────────────────
# class ClassifyResponse(BaseModel):
#     intent: str
#     id: Optional[Union[int, str]] = None
#     date: Optional[str] = None           # YYYY-MM-DD
#     datetime: Optional[str] = None       # ISO 8601
#     time: Optional[str] = None           # HH:MM:SS
#     message: Optional[str] = None        # Professional response (ONLY for general_chat)


# # ─────────────────────────────────────────────────────────────
# # ENDPOINT — Classify intent
# # ─────────────────────────────────────────────────────────────
# @app.post(
#     "/classify",
#     response_model=ClassifyResponse,
#     summary="Classify worker message intent with date/time extraction",
#     tags=["Classification"],
# )
# async def classify(
#     message: str = Query(
#         ...,
#         description="Message from worker",
#         example="2 ghante baad complete karna hai",
#     )
# ):
#     """
#     Pure intent classifier — returns intent, IDs, extracted date/time.
    
#     **Response Fields:**
    
#     - `intent`: Classified intent (/present, /tasks, /complete, general_chat, etc.)
#     - `id`: Extracted ID (for complete, update, resolve commands)
#     - `date`: Extracted date in YYYY-MM-DD format
#     - `datetime`: Extracted datetime in ISO format
#     - `time`: Extracted time in HH:MM:SS format
#     - `message`: Professional response (ONLY for general_chat intent, null otherwise)
    
#     **Message Field Behaviour:**
    
#     - For **non-general_chat intents** (e.g., /present, /tasks, /complete): 
#       `message` field is `null`
    
#     - For **general_chat intent**:
#       `message` contains professional, helpful responses that acknowledge what the user 
#       seems to be discussing (tasks, reports, updates, issues, attendance, team) and 
#       guides them to use appropriate commands — without suggesting specific intents.
    
#     **Professional Response Examples:**
    
#     - User: "main apna kaam dekhna chahta hu" → 
#       `message`: "I understand you're asking about tasks. To view or manage your tasks, please use: /tasks, /complete, or /assign..."
    
#     - User: "report chahiye" → 
#       `message`: "I see you're interested in getting a report. To generate a report, please use /report..."
    
#     - User: "kuch problem hai machine mein" → 
#       `message`: "I understand you're reporting an issue. To help you better, please use /issue to log this properly..."
#     """

#     # ── 1. Try slash-command fast path ───────────────────────
#     command_result = command_parser.parse(message)
#     if command_result:
#         return ClassifyResponse(
#             intent           = command_result.get("intent"),
#             id               = command_result.get("id"),
#             date             = command_result.get("date"),
#             datetime         = command_result.get("datetime"),
#             time             = command_result.get("time"),
#             message          = None,  # No message for explicit commands
#         )

#     # ── 2. Natural-language classification via GPT ────────────
#     result = classifier.classify(message)

#     return ClassifyResponse(
#         intent           = result.get("intent", "general_chat"),
#         id               = result.get("id"),
#         date             = result.get("date"),
#         datetime         = result.get("datetime"),
#         time             = result.get("time"),
#         message          = result.get("message"),  # Will be None for non-general_chat
#     )


# # ─────────────────────────────────────────────────────────────
# # HEALTH CHECK
# # ─────────────────────────────────────────────────────────────
# @app.get("/health", tags=["Meta"])
# async def health():
#     return {"status": "ok", "version": "3.7.0"}


# # ─────────────────────────────────────────────────────────────
# # ROOT — API overview
# # ─────────────────────────────────────────────────────────────
# @app.get("/", tags=["Meta"])
# async def root():
#     from datetime import datetime, timedelta
#     now = datetime.now()

#     return {
#         "service": "Worker Intent Classifier API",
#         "version": "3.7.0",
#         "endpoint": "POST /classify?message=your_message_here",
#         "current_datetime": now.isoformat(),
#         "whats_new_in_3_7": {
#             "removed_suggested_intent": "The 'suggested_intent' field has been removed from the response body.",
#             "professional_responses": (
#                 "For 'general_chat' intent, the assistant now provides professional, helpful responses that "
#                 "acknowledge what the user seems to be discussing (tasks, reports, updates, issues, attendance, team) "
#                 "and guides them to use appropriate commands — without suggesting specific intents."
#             ),
#             "no_intent_suggestions": (
#                 "The assistant no longer suggests intents like 'Did you mean /tasks?'. Instead, it professionally "
#                 "acknowledges the topic and provides relevant command options."
#             ),
#         },
#         "response_examples": {
#             "command_intent_no_message": {
#                 "input": "/present",
#                 "response": {
#                     "intent": "/present",
#                     "message": None,
#                     "date": "2026-05-14"
#                 },
#             },
#             "nlp_detected_command_no_message": {
#                 "input": "aaj main aa gaya hu",
#                 "response": {
#                     "intent": "/present",
#                     "message": None,
#                     "date": "2026-05-14"
#                 },
#             },
#             "general_chat_about_tasks": {
#                 "input": "mera kaam dekhna hai",
#                 "response": {
#                     "intent": "general_chat",
#                     "message": "I understand you're asking about tasks. To view or manage your tasks, please use the following commands:\n\n• /tasks - View your task list\n• /complete [task_id] - Mark a task as complete\n• /assign @username - Assign a task to someone\n\nWould you like me to help you with any of these actions?"
#                 },
#             },
#             "general_chat_about_report": {
#                 "input": "mujhe report chahiye",
#                 "response": {
#                     "intent": "general_chat",
#                     "message": "I see you're interested in getting a report. To generate a report, please use:\n\n• /report - Generate a comprehensive report\n\nYou can also specify time periods like 'last week' or 'this month' with your request. Would you like to generate a report now?"
#                 },
#             },
#             "general_chat_about_issue": {
#                 "input": "machine mein problem hai",
#                 "response": {
#                     "intent": "general_chat",
#                     "message": "I understand you're reporting an issue. To help you better, please use:\n\n• /issue - Report a new issue (please describe the problem)\n• /issues - View all active issues\n• /resolve [issue_id] - Resolve an existing issue\n\nCould you please use /issue to log this properly so our team can address it?"
#                 },
#             },
#         },
#         "supported_units": [
#             "seconds (सेकंड)", "minutes (मिनट)", "hours (घंटे)",
#             "days (दिन)", "weeks (हफ्ते)", "months (महीने)", "years (साल)",
#         ],
#         "supported_languages": ["English", "Hindi", "Hinglish"],
#     }


# # ─────────────────────────────────────────────────────────────
# # ENTRYPOINT
# # ─────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)














# """
# main.py — FastAPI backend for Pure Intent Classifier with Task Structure
# Run: uvicorn main:app --reload

# Endpoint:
#   POST /classify?message=2%20ghante%20baad%20complete%20karna%20hai
# """

# from fastapi import FastAPI, Query
# from pydantic import BaseModel
# from typing import Optional, Union, Dict, Any
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
#     description="Pure intent classifier — returns intent, IDs, extracted date, task structure, and professional responses only for general_chat",
#     version="4.0.0",
#     lifespan=lifespan,
# )


# # ─────────────────────────────────────────────────────────────
# # REQUEST / RESPONSE MODELS
# # ─────────────────────────────────────────────────────────────
# class ClassifyResponse(BaseModel):
#     intent: str
#     id: Optional[Union[int, str]] = None
#     date: Optional[str] = None           # YYYY-MM-DD
#     datetime: Optional[str] = None       # ISO 8601
#     task: Optional[Dict[str, Any]] = None  # Structured task object from free-text
#     message: Optional[str] = None        # Professional response (ONLY for general_chat)


# # ─────────────────────────────────────────────────────────────
# # ENDPOINT — Classify intent
# # ─────────────────────────────────────────────────────────────
# @app.post(
#     "/classify",
#     response_model=ClassifyResponse,
#     summary="Classify worker message intent with date extraction and task structuring",
#     tags=["Classification"],
# )
# async def classify(
#     message: str = Query(
#         ...,
#         description="Message from worker",
#         example="Send 500 units before evening",
#     )
# ):
#     """
#     Pure intent classifier — returns intent, IDs, extracted date, and structured task object.
    
#     **Response Fields:**
    
#     - `intent`: Classified intent (/present, /tasks, /complete, general_chat, etc.)
#     - `id`: Extracted ID (for complete, update, resolve commands)
#     - `date`: Extracted date in YYYY-MM-DD format
#     - `datetime`: Extracted datetime in ISO format (when both date and time present)
#     - `task`: Structured task object extracted from free-text instructions
#     - `message`: Professional Hinglish response (ONLY for general_chat intent, null otherwise)
    
#     **Task Structure Fields (from Intent Parsing):**
    
#     - `task_type`: Type of task (dispatch, invoice, purchase, followup, etc.)
#     - `quantity`: Extracted quantity (e.g., 500)
#     - `deadline`: Extracted deadline (e.g., "today evening")
#     - `department`: Mapped department (operations, accounting, procurement, sales)
#     - `item`: Extracted item description
    
#     **Keyword to Task Type Mapping:**
    
#     - dispatch, send, deliver → `dispatch` → operations department
#     - invoice, bill, payment → `invoice` → accounting department
#     - purchase, buy, order → `purchase` → procurement department
#     - followup, sales, client → `followup` → sales department
    
#     **Example:**
    
#     Input: "Send 500 units before evening"
    
#     Output:
#     {
#         "intent": "general_chat",
#         "task": {
#             "task_type": "dispatch",
#             "quantity": 500,
#             "deadline": "before evening",
#             "department": "operations"
#         },
#         "message": "Main samajh gaya aap tasks pooch rahe ho..."
#     }
#     """

#     # ── 1. Try slash-command fast path ───────────────────────
#     command_result = command_parser.parse(message)
#     if command_result:
#         return ClassifyResponse(
#             intent           = command_result.get("intent"),
#             id               = command_result.get("id"),
#             date             = command_result.get("date"),
#             datetime         = command_result.get("datetime"),
#             task             = command_result.get("task"),
#             message          = None,  # No message for explicit commands
#         )

#     # ── 2. Natural-language classification via GPT ────────────
#     result = classifier.classify(message)

#     return ClassifyResponse(
#         intent           = result.get("intent", "general_chat"),
#         id               = result.get("id"),
#         date             = result.get("date"),
#         datetime         = result.get("datetime"),
#         task             = result.get("task"),
#         message          = result.get("message"),  # Will be None for non-general_chat
#     )


# # ─────────────────────────────────────────────────────────────
# # HEALTH CHECK
# # ─────────────────────────────────────────────────────────────
# @app.get("/health", tags=["Meta"])
# async def health():
#     return {"status": "ok", "version": "4.0.0"}


# # ─────────────────────────────────────────────────────────────
# # ROOT — API overview
# # ─────────────────────────────────────────────────────────────
# @app.get("/", tags=["Meta"])
# async def root():
#     from datetime import datetime
#     now = datetime.now()

#     return {
#         "service": "Worker Intent Classifier API",
#         "version": "4.0.0",
#         "endpoint": "POST /classify?message=your_message_here",
#         "current_datetime": now.isoformat(),
#         "whats_new_in_4_0": {
#             "task_structure_extraction": (
#                 "Added Intent Parsing capability from Munshi Dada proposal. "
#                 "Converts free-text instructions into structured task objects with "
#                 "task_type, quantity, deadline, department, and item fields."
#             ),
#             "keyword_to_department_mapping": {
#                 "dispatch/send/deliver": "operations",
#                 "invoice/bill/payment": "accounting",
#                 "purchase/buy/order": "procurement",
#                 "followup/sales/client": "sales"
#             }
#         },
#         "response_examples": {
#             "task_structure_extraction": {
#                 "input": "Send 500 units before evening",
#                 "response": {
#                     "intent": "general_chat",
#                     "task": {
#                         "task_type": "dispatch",
#                         "quantity": 500,
#                         "deadline": "before evening",
#                         "department": "operations"
#                     },
#                     "message": "Main samajh gaya aap tasks pooch rahe ho..."
#                 }
#             },
#             "invoice_extraction": {
#                 "input": "Generate invoice for 1000 rupees",
#                 "response": {
#                     "intent": "general_chat",
#                     "task": {
#                         "task_type": "invoice",
#                         "quantity": 1000,
#                         "department": "accounting"
#                     }
#                 }
#             },
#             "purchase_extraction": {
#                 "input": "Order 50 leather sheets",
#                 "response": {
#                     "intent": "general_chat",
#                     "task": {
#                         "task_type": "purchase",
#                         "quantity": 50,
#                         "item": "leather sheets",
#                         "department": "procurement"
#                     }
#                 }
#             },
#             "command_intent_no_message": {
#                 "input": "/present",
#                 "response": {
#                     "intent": "/present",
#                     "message": None,
#                     "date": "2026-05-14"
#                 },
#             }
#         },
#         "supported_units": [
#             "seconds (सेकंड)", "minutes (मिनट)", "hours (घंटे)",
#             "days (दिन)", "weeks (हफ्ते)", "months (महीने)", "years (साल)",
#         ],
#         "supported_languages": ["English", "Hindi", "Hinglish"],
#     }


# # ─────────────────────────────────────────────────────────────
# # ENTRYPOINT
# # ─────────────────────────────────────────────────────────────
# if __name__ == "__main__":
#     uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)







"""
main.py — FastAPI backend for Pure Intent Classifier
Run: uvicorn main:app --reload
"""

from fastapi import FastAPI, Query
from pydantic import BaseModel
from typing import Optional, Union
from bot_engine import IntentClassifier, CommandParser
from contextlib import asynccontextmanager
import uvicorn

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
    description="Pure intent classifier — returns intent, IDs, extracted date, and professional responses only for general_chat",
    version="5.0.0",
    lifespan=lifespan,
)


class ClassifyResponse(BaseModel):
    intent: str
    id: Optional[Union[int, str]] = None
    worker_slug: Optional[str] = None
    deadline: Optional[str] = None
    message: Optional[str] = None


@app.post(
    "/classify",
    response_model=ClassifyResponse,
    summary="Classify worker message intent with date extraction",
    tags=["Classification"],
)
async def classify(
    message: str = Query(
        ...,
        description="Message from worker or manager",
        example="kal subah 10 bje tak warehouse khali krdo",
    )
):
    """
    Pure intent classifier — returns intent, IDs, and extracted deadline.
    
    **Response Fields:**
    - `intent`: Classified intent (/tasks, /present, /absent, /complete, /assign, /mgrself, /mgrassign, general_chat, etc.)
    - `id`: Extracted task ID (for complete, mgrself, mgrassign)
    - `worker_slug`: Worker username (for /mgrassign command)
    - `deadline`: Extracted deadline in ISO format or YYYY-MM-DD
    - `message`: Professional response (ONLY for general_chat intent)
    
    **Important:** All work-related instructions (dispatch, invoice, purchase, warehouse cleanup, etc.)
    are classified as "/tasks" - NOT as "general_chat".
    """

    command_result = command_parser.parse(message)
    if command_result:
        return ClassifyResponse(
            intent=command_result.get("intent"),
            id=command_result.get("id"),
            worker_slug=command_result.get("worker_slug"),
            deadline=command_result.get("deadline"),
            message=None,
        )

    result = classifier.classify(message)

    return ClassifyResponse(
        intent=result.get("intent", "general_chat"),
        id=result.get("id"),
        worker_slug=result.get("worker_slug"),
        deadline=result.get("deadline"),
        message=result.get("message"),
    )


@app.get("/health", tags=["Meta"])
async def health():
    return {"status": "ok", "version": "5.0.0"}


@app.get("/", tags=["Meta"])
async def root():
    from datetime import datetime
    now = datetime.now()

    return {
        "service": "Worker Intent Classifier API",
        "version": "5.0.0",
        "endpoint": "POST /classify?message=your_message_here",
        "current_datetime": now.isoformat(),
        "whats_new_in_5_0": {
            "removed_task_field": "The 'task' field has been completely removed from the response body.",
            "all_tasks_to_tasks_intent": "All work-related instructions (dispatch, invoice, purchase, warehouse cleanup, etc.) are now classified as '/tasks' intent.",
            "general_chat_only": "The 'general_chat' intent is now ONLY for pure conversation (greetings, small talk, non-work related)."
        },
        "response_examples": {
            "operational_task": {
                "input": "kal subah 10 bje tak warehouse khali krdo",
                "response": {
                    "intent": "/tasks",
                    "deadline": "2026-05-16T10:00:00",
                    "message": None
                }
            },
            "dispatch_task": {
                "input": "send 500 units before evening",
                "response": {
                    "intent": "/tasks",
                    "deadline": "2026-05-15",
                    "message": None
                }
            },
            "attendance": {
                "input": "aaj main aa gaya hu",
                "response": {
                    "intent": "/present",
                    "deadline": "2026-05-15",
                    "message": None
                }
            },
            "general_chat": {
                "input": "hello kaise ho",
                "response": {
                    "intent": "general_chat",
                    "message": "Main aapki baat samajh gaya. Main yeh sab kar sakta hoon:\n\n• Tasks manage karna (/tasks, /complete, /assign)\n• Reports generate karna (/report)\n..."
                }
            }
        },
        "supported_languages": ["English", "Hindi", "Hinglish"],
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)