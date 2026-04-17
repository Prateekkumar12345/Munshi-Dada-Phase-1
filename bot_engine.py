# """
# bot_engine.py — Pure Intent Classifier for Worker Assistant
# No database, no worker_id, just intent classification
# """

# import json
# import os
# import re
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CHAT_MODEL = "gpt-4o-mini"


# # ─────────────────────────────────────────────────────────────
# # PURE INTENT CLASSIFIER - No database, no state, no worker_id
# # ─────────────────────────────────────────────────────────────
# class IntentClassifier:
#     def __init__(self):
#         print("✅ Intent Classifier ready.")

#     def classify(self, message: str) -> dict:
#         """
#         Classify the user's message into intents.
#         Returns intent only. No database operations, no side effects.
#         """
#         system = self._build_system_prompt()
        
#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             messages=[
#                 {"role": "system", "content": system},
#                 {"role": "user", "content": message}
#             ],
#             temperature=0.2,
#             max_tokens=100,
#             response_format={"type": "json_object"},
#         )
        
#         raw_reply = response.choices[0].message.content.strip()
#         return self._parse_decision(raw_reply)

#     def _build_system_prompt(self) -> str:
#         return """You are a pure intent classification system.
# Your ONLY job is to classify the user's message into one intent.
# Respond with ONLY a JSON object containing the intent.

# === INTENTS ===

# 1. "present" - Marking attendance as present
#    Examples: "present", "aa gaya", "main present hu", "aaj aaya hu", "pahunch gaya"

# 2. "absent" - Marking attendance as absent
#    Examples: "absent", "nahi aa sakta", "chutti", "aaj nahi aaunga"

# 3. "/tasks" - View tasks
#    Examples: "tasks", "kaam dikhao", "mera kaam", "kya karna hai"

# 4. "/complete" - Marking a task as complete
#    Examples: "ho gaya", "khatam", "done", "complete", "transformer ho gaya"

# 5. "/assign" - Assigning a task to someone
#    Examples: "assign", "@user karo", "@all ye kaam karo"

# 6. "/update" - Updating a task with a message
#    Examples: "update", "task update", "status update"

# 7. "/issue" - Reporting an issue
#    Examples: "issue", "problem", "dikkat", "not working"

# 8. "/issues" - View active issues
#    Examples: "issues", "active issues", "problems list"

# 9. "/resolve" - Resolving an issue
#    Examples: "resolve", "fixed", "solved", "hatado"

# 10. "/members" - View team members
#     Examples: "members", "team", "sab log"

# 11. "/report" - Generate a report
#     Examples: "report", "summary", "report de do"

# 12. "/help" - Need help with commands
#     Examples: "help", "commands", "kya karein"

# 13. "general_chat" - General conversation
#     Examples: "hello", "hi", "thank you", "bye"

# === OUTPUT FORMAT ===
# Respond with ONLY this JSON, nothing else:
# {"intent": "<intent_name>"}

# Example responses:
# {"intent": "present"}
# {"intent": "complete_task"}
# {"intent": "report_issue"}
# """

#     def _parse_decision(self, raw: str) -> dict:
#         try:
#             return json.loads(raw)
#         except Exception:
#             # strip markdown fences if present
#             clean = re.sub(r"```json|```", "", raw).strip()
#             try:
#                 return json.loads(clean)
#             except Exception:
#                 return {"intent": "general_chat"}


# # ─────────────────────────────────────────────────────────────
# # COMMAND PARSER - For explicit slash commands
# # ─────────────────────────────────────────────────────────────
# class CommandParser:
#     """Parse slash commands without any database dependency"""
    
#     def parse(self, message: str) -> dict:
#         """Parse slash commands and return intent"""
#         message = message.strip().lower()
        
#         # /present
#         if message.startswith("/present"):
#             return {"intent": "/present"}
        
#         # /absent
#         if message.startswith("/absent"):
#             return {"intent": "/absent"}
        
#         # /tasks
#         if message.startswith("/tasks"):
#             return {"intent": "/tasks"}
        
#         # /complete
#         if message.startswith("/complete"):
#             return {"intent": "/complete"}
        
#         # /assign
#         if message.startswith("/assign"):
#             return {"intent": "/assign"}
        
#         # /update
#         if message.startswith("/update"):
#             return {"intent": "/update"}
        
#         # /issue
#         if message.startswith("/issue"):
#             return {"intent": "/issue"}
        
#         # /issues
#         if message.startswith("/issues"):
#             return {"intent": "/issues"}
        
#         # /resolve
#         if message.startswith("/resolve"):
#             return {"intent": "/resolve"}
        
#         # /members
#         if message.startswith("/members"):
#             return {"intent": "/members"}
        
#         # /report
#         if message.startswith("/report"):
#             return {"intent": "/report"}
        
#         # /help
#         if message.startswith("/help"):
#             return {"intent": "help"}
        
#         # Not a command
#         return None



"""
bot_engine.py — Pure Intent Classifier for Worker Assistant
No database, no worker_id, just intent classification
"""

import json
import os
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHAT_MODEL = "gpt-4o-mini"


# ─────────────────────────────────────────────────────────────
# PURE INTENT CLASSIFIER - No database, no state, no worker_id
# ─────────────────────────────────────────────────────────────
class IntentClassifier:
    def __init__(self):
        print("✅ Intent Classifier ready.")

    def classify(self, message: str) -> dict:
        """
        Classify the user's message into intents.
        Returns intent only. No database operations, no side effects.
        """
        system = self._build_system_prompt()
        
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": message}
            ],
            temperature=0.2,
            max_tokens=100,
            response_format={"type": "json_object"},
        )
        
        raw_reply = response.choices[0].message.content.strip()
        return self._parse_decision(raw_reply)

    def _build_system_prompt(self) -> str:
        return """You are a pure intent classification system.
Your ONLY job is to classify the user's message into one intent.
Respond with ONLY a JSON object containing the intent.

=== INTENTS ===

1. "present" - Marking attendance as present
   Examples: "present", "aa gaya", "main present hu", "aaj aaya hu", "pahunch gaya"

2. "absent" - Marking attendance as absent
   Examples: "absent", "nahi aa sakta", "chutti", "aaj nahi aaunga"

3. "/tasks" - View tasks
   Examples: "tasks", "kaam dikhao", "mera kaam", "kya karna hai"

4. "/complete" - Marking a task as complete (with optional task ID)
   Examples: "ho gaya", "khatam", "done", "complete", "transformer ho gaya"
   If user provides a number after "complete" like "complete 2" or "/complete 2", extract the ID

5. "/assign" - Assigning a task to someone
   Examples: "assign", "@user karo", "@all ye kaam karo"

6. "/update" - Updating a task with a message
   Examples: "update", "task update", "status update"

7. "/issue" - Reporting an issue
   Examples: "issue", "problem", "dikkat", "not working"

8. "/issues" - View active issues
   Examples: "issues", "active issues", "problems list"

9. "/resolve" - Resolving an issue
   Examples: "resolve", "fixed", "solved", "hatado"

10. "/members" - View team members
    Examples: "members", "team", "sab log"

11. "/report" - Generate a report
    Examples: "report", "summary", "report de do"

12. "/help" - Need help with commands
    Examples: "help", "commands", "kya karein"

13. "general_chat" - General conversation
    Examples: "hello", "hi", "thank you", "bye"

=== OUTPUT FORMAT ===
Respond with ONLY this JSON, nothing else:
{"intent": "<intent_name>"}

For "/complete" intent with an ID, respond with:
{"intent": "/complete", "id": <number>}

If no ID is provided for "/complete", respond with:
{"intent": "/complete", "id": null}

Example responses:
{"intent": "present"}
{"intent": "/complete", "id": 2}
{"intent": "/complete", "id": null}
{"intent": "/issue"}
"""

    def _parse_decision(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except Exception:
            # strip markdown fences if present
            clean = re.sub(r"```json|```", "", raw).strip()
            try:
                return json.loads(clean)
            except Exception:
                return {"intent": "general_chat"}


# ─────────────────────────────────────────────────────────────
# COMMAND PARSER - For explicit slash commands
# ─────────────────────────────────────────────────────────────
class CommandParser:
    """Parse slash commands without any database dependency"""
    
    def parse(self, message: str) -> dict:
        """Parse slash commands and return intent with extracted parameters"""
        message = message.strip()
        original_message = message
        message_lower = message.lower()
        
        # /present
        if message_lower.startswith("/present"):
            return {"intent": "/present"}
        
        # /absent
        if message_lower.startswith("/absent"):
            return {"intent": "/absent"}
        
        # /tasks
        if message_lower.startswith("/tasks"):
            return {"intent": "/tasks"}
        
        # /complete - Extract ID if present
        if message_lower.startswith("/complete"):
            # Extract everything after /complete
            rest = message[9:].strip()  # 9 is length of "/complete"
            
            # Try to extract ID (first number in the string)
            import re
            match = re.search(r'^\d+', rest)
            
            if match:
                task_id = int(match.group())
                return {"intent": "/complete", "id": task_id}
            else:
                return {"intent": "/complete", "id": None}
        
        # /assign
        if message_lower.startswith("/assign"):
            return {"intent": "/assign"}
        
        # /update
        if message_lower.startswith("/update"):
            return {"intent": "/update"}
        
        # /issue
        if message_lower.startswith("/issue"):
            return {"intent": "/issue"}
        
        # /issues
        if message_lower.startswith("/issues"):
            return {"intent": "/issues"}
        
        # /resolve
        if message_lower.startswith("/resolve"):
            return {"intent": "/resolve"}
        
        # /members
        if message_lower.startswith("/members"):
            return {"intent": "/members"}
        
        # /report
        if message_lower.startswith("/report"):
            return {"intent": "/report"}
        
        # /help
        if message_lower.startswith("/help"):
            return {"intent": "help"}
        
        # Not a command
        return None