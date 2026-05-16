# """
# bot_engine.py — Pure Intent Classifier for Worker Assistant
# No database, no worker_id, just intent classification with date & time extraction
# """

# import json
# import os
# import re
# from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CHAT_MODEL = "gpt-4o-mini"


# # ─────────────────────────────────────────────────────────────
# # DATE & TIME UTILITY FUNCTIONS
# # ─────────────────────────────────────────────────────────────
# class DateTimeExtractor:

#     WORD_TO_UNIT = {
#         # ── seconds ──────────────────────────────────────────
#         "second": "seconds", "seconds": "seconds", "sec": "seconds", "secs": "seconds",
#         "सेकंड": "seconds", "सेकेंड": "seconds",
#         # ── minutes ──────────────────────────────────────────
#         "minute": "minutes", "minutes": "minutes", "min": "minutes", "mins": "minutes",
#         "मिनट": "minutes", "मिनटों": "minutes",
#         # ── hours ────────────────────────────────────────────
#         "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours", "h": "hours",
#         "ghanta": "hours", "ghante": "hours", "घंटा": "hours", "घंटे": "hours",
#         # ── days ─────────────────────────────────────────────
#         "day": "days", "days": "days", "d": "days",
#         "din": "days", "दिन": "days", "दिनों": "days",
#         # ── weeks ────────────────────────────────────────────
#         "week": "weeks", "weeks": "weeks", "wk": "weeks", "wks": "weeks",
#         "hafte": "weeks", "hafta": "weeks", "हफ्ता": "weeks", "हफ्ते": "weeks",
#         "सप्ताह": "weeks",
#         # ── months ───────────────────────────────────────────
#         "month": "months", "months": "months", "mon": "months", "mons": "months",
#         "mahina": "months", "mahine": "months", "महीना": "months", "महीने": "months",
#         # ── years ────────────────────────────────────────────
#         "year": "years", "years": "years", "yr": "years", "yrs": "years", "y": "years",
#         "saal": "years", "साल": "years", "वर्ष": "years",
#     }

#     _UNIT_RE = (
#         r"(?P<unit>"
#         r"seconds?|secs?|sec"
#         r"|minutes?|mins?|min"
#         r"|hours?|hrs?"
#         r"|ghante|ghanta"
#         r"|weeks?|wks?|wk"
#         r"|hafte|hafta"
#         r"|months?|mons?"
#         r"|mahine|mahina"
#         r"|years?|yrs?"
#         r"|saal"
#         r"|days?"
#         r"|din"
#         r"|घंटे|घंटा|मिनट|सेकंड|सेकेंड"
#         r"|दिन|दिनों|हफ्ता|हफ्ते|सप्ताह"
#         r"|महीना|महीने|साल|वर्ष"
#         r")"
#     )

#     _FUTURE_RE = re.compile(
#         r"(?:in|after)?\s*(?P<amount>\d+)\s*"
#         + _UNIT_RE
#         + r"(?:\s*(?:ke\s*)?(?:baad|mein|में|बाद|after|later|from\s*now))",
#         re.IGNORECASE | re.UNICODE,
#     )

#     _PAST_RE = re.compile(
#         r"(?P<amount>\d+)\s*"
#         + _UNIT_RE
#         + r"(?:\s*(?:pehle|pahle|पहले|before|ago))",
#         re.IGNORECASE | re.UNICODE,
#     )

#     @staticmethod
#     def get_unit_type(unit_text: str) -> str:
#         return (
#             DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip().lower())
#             or DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip())
#         )

#     @staticmethod
#     def _apply_offset(amount: int, unit: str, direction: str) -> dict:
#         now = datetime.now()
#         sign = 1 if direction == "future" else -1

#         delta_map = {
#             "seconds": timedelta(seconds=amount * sign),
#             "minutes": timedelta(minutes=amount * sign),
#             "hours":   timedelta(hours=amount * sign),
#             "days":    timedelta(days=amount * sign),
#             "weeks":   timedelta(weeks=amount * sign),
#             "months":  relativedelta(months=amount * sign),
#             "years":   relativedelta(years=amount * sign),
#         }
#         delta = delta_map.get(unit)
#         if delta is None:
#             return {"datetime": None, "date_only": None, "time_only": None}

#         target = now + delta
#         return {
#             "datetime":  target.isoformat(),
#             "date_only": target.strftime("%Y-%m-%d"),
#             "time_only": target.strftime("%H:%M:%S"),
#         }

#     @staticmethod
#     def calculate_datetime_from_offset(amount: int, unit: str, direction: str) -> dict:
#         return DateTimeExtractor._apply_offset(amount, unit, direction)

#     @staticmethod
#     def parse_relative_time(text: str) -> dict | None:
#         for pattern, direction in (
#             (DateTimeExtractor._FUTURE_RE, "future"),
#             (DateTimeExtractor._PAST_RE,   "past"),
#         ):
#             m = pattern.search(text)
#             if m:
#                 amount = int(m.group("amount"))
#                 unit   = DateTimeExtractor.get_unit_type(m.group("unit"))
#                 if unit:
#                     return {
#                         "amount":        amount,
#                         "unit":          unit,
#                         "direction":     direction,
#                         "original_text": m.group(0),
#                     }
#         return None

#     @staticmethod
#     def extract_date_from_message(message: str) -> dict:
#         today = datetime.now().date()
#         now   = datetime.now()
#         ml    = message.lower()

#         # ── 1. Relative offset ───────────────────────────────────────────────
#         rel = DateTimeExtractor.parse_relative_time(message)
#         if rel:
#             r = DateTimeExtractor._apply_offset(rel["amount"], rel["unit"], rel["direction"])
#             if r["datetime"]:
#                 return {
#                     "date":          r["date_only"],
#                     "datetime":      r["datetime"],
#                     "time":          r["time_only"],
#                     "original_text": rel["original_text"],
#                     "type":          "relative_time",
#                     "unit":          rel["unit"],
#                     "amount":        rel["amount"],
#                     "direction":     rel["direction"],
#                 }

#         # ── 2. Named fixed ranges ────────────────────────────────────────────
#         if re.search(r"\b(last week|pichle hafte|पिछले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=7)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "last week", "type": "week"}

#         if re.search(r"\b(last month|pichle mahine|पिछले महीने)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(months=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "last month", "type": "month"}

#         if re.search(r"\b(last year|pichle saal|पिछले साल)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(years=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "last year", "type": "year"}

#         if re.search(r"\b(this week|is hafte|इस हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=today.weekday())
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "this week", "type": "week"}

#         if re.search(r"\b(this month|is mahine|इस महीने)\b", ml, re.IGNORECASE):
#             d = today.replace(day=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "this month", "type": "month"}

#         if re.search(r"\b(this year|is saal|इस साल)\b", ml, re.IGNORECASE):
#             d = today.replace(month=1, day=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "this year", "type": "year"}

#         if re.search(r"\b(next week|agale hafte|अगले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today + timedelta(days=7)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "next week", "type": "week"}

#         if re.search(r"\b(next month|agale mahine|अगले महीने)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(months=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "next month", "type": "month"}

#         if re.search(r"\b(next year|agale saal|अगले साल)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(years=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
#                     "original_text": "next year", "type": "year"}

#         # ── 3. Named days ────────────────────────────────────────────────────
#         if re.search(r"\b(aaj|today|आज|aaj ke|aaj hi|आज ही)\b", ml, re.IGNORECASE | re.UNICODE):
#             return {"date": today.strftime("%Y-%m-%d"), "datetime": now.isoformat(),
#                     "time": None, "original_text": None, "type": "relative"}

#         if re.search(r"\b(parso|day after tomorrow|परसों|parso ke|परसों को)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today + timedelta(days=2)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=2)).isoformat(),
#                     "time": None, "original_text": None, "type": "relative"}

#         if re.search(r"\b(parson|day before yesterday|ना परसों)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=2)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=2)).isoformat(),
#                     "time": None, "original_text": None, "type": "relative"}

#         if re.search(r"\b(yesterday|pichle kal|बीता हुआ कल)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=1)).isoformat(),
#                     "time": None, "original_text": None, "type": "relative"}

#         if re.search(r"\b(kal|tomorrow|कल|kal ke|कल को)\b", ml, re.IGNORECASE | re.UNICODE):
#             past_markers = re.search(
#                 r"\b(pehle|pahle|पहले|ago|yesterday|kal pehle|beet gaya)\b",
#                 ml, re.IGNORECASE | re.UNICODE,
#             )
#             offset = -1 if past_markers else 1
#             d = today + timedelta(days=offset)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=offset)).isoformat(),
#                     "time": None, "original_text": None, "type": "relative"}

#         # ── 4. Explicit date literals ────────────────────────────────────────
#         m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", message)
#         if m:
#             day, month, year = m.groups()
#             try:
#                 specific_date = datetime(int(year), int(month), int(day))
#                 return {"date": specific_date.strftime("%Y-%m-%d"),
#                         "datetime": specific_date.isoformat(), "time": None,
#                         "original_text": m.group(0), "type": "specific"}
#             except ValueError:
#                 pass

#         m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", message)
#         if m:
#             year, month, day = m.groups()
#             try:
#                 specific_date = datetime(int(year), int(month), int(day))
#                 return {"date": specific_date.strftime("%Y-%m-%d"),
#                         "datetime": specific_date.isoformat(), "time": None,
#                         "original_text": m.group(0), "type": "specific"}
#             except ValueError:
#                 pass

#         return {"date": None, "datetime": None, "time": None, "original_text": None, "type": None}


# # ─────────────────────────────────────────────────────────────
# # PROFESSIONAL RESPONSE GENERATOR (Only for general_chat)
# # ─────────────────────────────────────────────────────────────

# def get_professional_response(message: str, date_info: dict = None) -> str:
#     """
#     Generate a professional, helpful response for general_chat intent.
#     Acknowledges what the user seems to be discussing without suggesting specific intents.
#     """
    
#     message_lower = message.lower()
    
#     # Detect what the user might be talking about
#     is_about_task = any(word in message_lower for word in ['task', 'kaam', 'work', 'complete', 'khatam', 'ho gaya'])
#     is_about_report = any(word in message_lower for word in ['report', 'report de', 'summary', 'data', 'numbers'])
#     is_about_update = any(word in message_lower for word in ['update', 'change', 'badlo', 'sudhar', 'modify'])
#     is_about_issue = any(word in message_lower for word in ['issue', 'problem', 'dikkat', 'error', 'galat', 'not working'])
#     is_about_attendance = any(word in message_lower for word in ['present', 'absent', 'attendance', 'haazri', 'aaj', 'kal'])
#     is_about_team = any(word in message_lower for word in ['team', 'member', 'sathi', 'colleague', 'fellow'])
    
#     # Professional, polite responses that acknowledge the topic
#     def _fmt_date(d: str) -> str:
#         """YYYY-MM-DD → '18 April 2026'"""
#         try:
#             return datetime.strptime(d, "%Y-%m-%d").strftime("%-d %B %Y")
#         except Exception:
#             return d
    
#     date_str = date_info.get("date") if date_info else None
#     date_context = f" regarding {_fmt_date(date_str)}" if date_str else ""
    
#     # Topic-specific professional responses
#     if is_about_task:
#         return (
#             f"I understand you're asking about tasks{date_context}. "
#             f"To view or manage your tasks, please use the following commands:\n\n"
#             f"• /tasks - View your task list\n"
#             f"• /complete [task_id] - Mark a task as complete\n"
#             f"• /assign @username - Assign a task to someone\n\n"
#             f"Would you like me to help you with any of these actions?"
#         )
    
#     elif is_about_report:
#         return (
#             f"I see you're interested in getting a report{date_context}. "
#             f"To generate a report, please use:\n\n"
#             f"• /report - Generate a comprehensive report\n\n"
#             f"You can also specify time periods like 'last week' or 'this month' with your request. "
#             f"Would you like to generate a report now?"
#         )
    
#     elif is_about_update:
#         return (
#             f"I notice you're mentioning an update{date_context}. "
#             f"To update tasks or information, please use:\n\n"
#             f"• /update [task_id] - Update a task's status or details\n"
#             f"• /resolve [issue_id] - Mark an issue as resolved\n\n"
#             f"Which update would you like to make?"
#         )
    
#     elif is_about_issue:
#         return (
#             f"I understand you're reporting an issue{date_context}. "
#             f"To help you better, please use:\n\n"
#             f"• /issue - Report a new issue (please describe the problem)\n"
#             f"• /issues - View all active issues\n"
#             f"• /resolve [issue_id] - Resolve an existing issue\n\n"
#             f"Could you please use /issue to log this properly so our team can address it?"
#         )
    
#     elif is_about_attendance:
#         return (
#             f"I see you're asking about attendance{date_context}. "
#             f"To mark your attendance, please use:\n\n"
#             f"• /present - Mark yourself as present\n"
#             f"• /absent - Mark yourself as absent\n\n"
#             f"Would you like me to mark your attendance now?"
#         )
    
#     elif is_about_team:
#         return (
#             f"I understand you're asking about team members. "
#             f"To view team information, please use:\n\n"
#             f"• /members - View all team members\n\n"
#             f"Would you like to see the team list?"
#         )
    
#     # Generic professional help response
#     else:
#         available_commands = [
#             "/present /absent - Mark attendance",
#             "/tasks - View your tasks",
#             "/complete [id] - Complete a task",
#             "/assign @user - Assign a task",
#             "/update [id] - Update a task",
#             "/issue /issues /resolve - Report or track issues",
#             "/members - View team members",
#             "/report - Generate reports",
#             "/help - Show all commands"
#         ]
        
#         cmd_list = "\n".join([f"• {cmd}" for cmd in available_commands[:5]])  # Show first 5 commands
        
#         return (
#             f"Thank you for your message. Main task management aur team coordination mein help kar sakta hoon."
#             f"Saare available commands dekhne ke liye help type karo."
#             f"Batao, main aapki kya help kar sakta hoon?"
#         )


# # ─────────────────────────────────────────────────────────────
# # PURE INTENT CLASSIFIER
# # ─────────────────────────────────────────────────────────────
# class IntentClassifier:
#     def __init__(self):
#         print("✅ Intent Classifier ready.")
#         self.datetime_extractor = DateTimeExtractor()

#     def classify(self, message: str) -> dict:
#         """
#         Classify the user's message into an intent and extract date/time.
#         """
#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         system = self._build_system_prompt()

#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             messages=[
#                 {"role": "system", "content": system},
#                 {"role": "user",   "content": message},
#             ],
#             temperature=0.2,
#             max_tokens=200,
#             response_format={"type": "json_object"},
#         )

#         raw_reply = response.choices[0].message.content.strip()
#         result = self._parse_decision(raw_reply)

#         # Attach date/time fields extracted locally (not via LLM)
#         result["date"]               = datetime_info.get("date")
#         result["datetime"]           = datetime_info.get("datetime")
#         result["time"]               = datetime_info.get("time")
#         result["date_original_text"] = datetime_info.get("original_text")

#         # Build professional message ONLY for general_chat intent
#         if result.get("intent") == "general_chat":
#             result["message"] = get_professional_response(message, datetime_info)
#         else:
#             result["message"] = None  # No message for other intents

#         return result

#     def _build_system_prompt(self) -> str:
#         return """You are a pure intent classification system with date/time extraction capability.
# Your ONLY job is to classify the user's message into one intent and extract any relevant information.
# Respond with ONLY a valid JSON object. Do not include any other text, markdown, or explanations.

# === INTENTS ===

# 1. "/present"    — Marking attendance as present
#                    Keywords: present, aa gaya, aaya, pahunch gaya, main present hu, aaj aaya hu

# 2. "/absent"     — Marking attendance as absent
#                    Keywords: absent, nahi aa sakta, chutti, leave, aaj nahi aaunga

# 3. "/tasks"      — View tasks
#                    Keywords: tasks, kaam dikhao, task list, mera kaam, kya karna hai

# 4. "/complete"   — Marking a task as complete (extract task ID if given)
#                    Keywords: complete, ho gaya, khatam, done, finished
#                    Example: "complete 2"  →  id: 2

# 5. "/assign"     — Assigning a task to someone (extract @username or phone number)
#                    Keywords: assign, @user, @all, de do, allocate

# 6. "/update"     — Updating a task with a comment / status (extract task ID if given)
#                    Keywords: update, add comment, status update

# 7. "/issue"      — Reporting a new issue (extract issue ID if referenced)
#                    Keywords: issue, problem, dikkat, not working, broken

# 8. "/issues"     — View all active issues
#                    Keywords: issues, active issues, problems list

# 9. "/resolve"    — Resolving an issue (extract issue ID)
#                    Keywords: resolve, fixed, solved, hatado, resolved hogya

# 10. "/members"   — View team members
#                    Keywords: members, team, sab log

# 11. "/report"    — Generate a report / summary
#                    Keywords: report, summary, report de do

# 12. "/help"      — Need help with available commands
#                    Keywords: help, commands, kya karein

# 13. "general_chat" — General conversation / anything that doesn't match above

# === OUTPUT FORMAT ===
# {"intent": "<intent_name>", "id": <id_value or null>}

# Examples:
# {"intent": "/present", "id": null}
# {"intent": "/complete", "id": 2}
# {"intent": "general_chat", "id": null}

# Note: date/time fields are added separately by the system — do NOT include them.
# """

#     def _parse_decision(self, raw: str) -> dict:
#         try:
#             return json.loads(raw)
#         except Exception:
#             clean = re.sub(r"```json|```", "", raw).strip()
#             try:
#                 return json.loads(clean)
#             except Exception:
#                 return {"intent": "general_chat", "id": None}


# # ─────────────────────────────────────────────────────────────
# # COMMAND PARSER
# # ─────────────────────────────────────────────────────────────
# class CommandParser:
#     """Parse explicit slash commands without any database dependency."""

#     def __init__(self):
#         self.datetime_extractor = DateTimeExtractor()

#     def parse(self, message: str) -> dict | None:
#         """
#         Parse a slash command and return an intent dict with extracted
#         parameters and resolved date/time.  Returns None if the message is
#         not a slash command.
#         """
#         message = message.strip()
#         ml = message.lower()

#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         def base(intent, id_=None):
#             result = {
#                 "intent":          intent,
#                 "id":              id_,
#                 "date":            datetime_info.get("date"),
#                 "datetime":        datetime_info.get("datetime"),
#                 "time":            datetime_info.get("time"),
#                 "message":         None,  # Slash commands have no message
#             }
#             return result

#         def extract_leading_int(text: str):
#             m = re.search(r"^\d+", text.strip())
#             return int(m.group()) if m else None

#         if ml.startswith("/issues"):
#             return base("/issues")

#         if ml.startswith("/issue"):
#             return base("/issue", extract_leading_int(message[6:]))

#         if ml.startswith("/present"):
#             return base("/present")

#         if ml.startswith("/absent"):
#             return base("/absent")

#         if ml.startswith("/tasks"):
#             return base("/tasks")

#         if ml.startswith("/complete"):
#             return base("/complete", extract_leading_int(message[9:]))

#         if ml.startswith("/assign"):
#             rest = message[7:].strip()
#             m = re.search(r"@(\d+)", rest)
#             if m:
#                 return base("/assign", f"@{m.group(1)}")
#             m = re.search(r"(\d{10})", rest)
#             if m:
#                 return base("/assign", m.group(1))
#             m = re.search(r"@(\w+)", rest)
#             if m:
#                 return base("/assign", f"@{m.group(1)}")
#             return base("/assign")

#         if ml.startswith("/update"):
#             return base("/update", extract_leading_int(message[7:]))

#         if ml.startswith("/resolve"):
#             return base("/resolve", extract_leading_int(message[8:]))

#         if ml.startswith("/members"):
#             return base("/members")

#         if ml.startswith("/report"):
#             return base("/report")

#         if ml.startswith("/help"):
#             return base("/help")

#         return None








# """
# bot_engine.py — Pure Intent Classifier with Task Structure Extraction for Worker Assistant
# No database, no worker_id, just intent classification with date extraction & task structuring
# """

# import json
# import os
# import re
# from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CHAT_MODEL = "gpt-4o-mini"


# # ─────────────────────────────────────────────────────────────
# # DATE UTILITY FUNCTIONS (Time extraction removed)
# # ─────────────────────────────────────────────────────────────
# class DateTimeExtractor:

#     WORD_TO_UNIT = {
#         # ── seconds ──────────────────────────────────────────
#         "second": "seconds", "seconds": "seconds", "sec": "seconds", "secs": "seconds",
#         "सेकंड": "seconds", "सेकेंड": "seconds",
#         # ── minutes ──────────────────────────────────────────
#         "minute": "minutes", "minutes": "minutes", "min": "minutes", "mins": "minutes",
#         "मिनट": "minutes", "मिनटों": "minutes",
#         # ── hours ────────────────────────────────────────────
#         "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours", "h": "hours",
#         "ghanta": "hours", "ghante": "hours", "घंटा": "hours", "घंटे": "hours",
#         # ── days ─────────────────────────────────────────────
#         "day": "days", "days": "days", "d": "days",
#         "din": "days", "दिन": "days", "दिनों": "days",
#         # ── weeks ────────────────────────────────────────────
#         "week": "weeks", "weeks": "weeks", "wk": "weeks", "wks": "weeks",
#         "hafte": "weeks", "hafta": "weeks", "हफ्ता": "weeks", "हफ्ते": "weeks",
#         "सप्ताह": "weeks",
#         # ── months ───────────────────────────────────────────
#         "month": "months", "months": "months", "mon": "months", "mons": "months",
#         "mahina": "months", "mahine": "months", "महीना": "months", "महीने": "months",
#         # ── years ────────────────────────────────────────────
#         "year": "years", "years": "years", "yr": "years", "yrs": "years", "y": "years",
#         "saal": "years", "साल": "years", "वर्ष": "years",
#     }

#     _UNIT_RE = (
#         r"(?P<unit>"
#         r"seconds?|secs?|sec"
#         r"|minutes?|mins?|min"
#         r"|hours?|hrs?"
#         r"|ghante|ghanta"
#         r"|weeks?|wks?|wk"
#         r"|hafte|hafta"
#         r"|months?|mons?"
#         r"|mahine|mahina"
#         r"|years?|yrs?"
#         r"|saal"
#         r"|days?"
#         r"|din"
#         r"|घंटे|घंटा|मिनट|सेकंड|सेकेंड"
#         r"|दिन|दिनों|हफ्ता|हफ्ते|सप्ताह"
#         r"|महीना|महीने|साल|वर्ष"
#         r")"
#     )

#     _FUTURE_RE = re.compile(
#         r"(?:in|after)?\s*(?P<amount>\d+)\s*"
#         + _UNIT_RE
#         + r"(?:\s*(?:ke\s*)?(?:baad|mein|में|बाद|after|later|from\s*now))",
#         re.IGNORECASE | re.UNICODE,
#     )

#     _PAST_RE = re.compile(
#         r"(?P<amount>\d+)\s*"
#         + _UNIT_RE
#         + r"(?:\s*(?:pehle|pahle|पहले|before|ago))",
#         re.IGNORECASE | re.UNICODE,
#     )

#     @staticmethod
#     def get_unit_type(unit_text: str) -> str:
#         return (
#             DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip().lower())
#             or DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip())
#         )

#     @staticmethod
#     def _apply_offset(amount: int, unit: str, direction: str) -> dict:
#         now = datetime.now()
#         sign = 1 if direction == "future" else -1

#         delta_map = {
#             "seconds": timedelta(seconds=amount * sign),
#             "minutes": timedelta(minutes=amount * sign),
#             "hours":   timedelta(hours=amount * sign),
#             "days":    timedelta(days=amount * sign),
#             "weeks":   timedelta(weeks=amount * sign),
#             "months":  relativedelta(months=amount * sign),
#             "years":   relativedelta(years=amount * sign),
#         }
#         delta = delta_map.get(unit)
#         if delta is None:
#             return {"datetime": None, "date_only": None}

#         target = now + delta
#         return {
#             "datetime":  target.isoformat(),
#             "date_only": target.strftime("%Y-%m-%d"),
#         }

#     @staticmethod
#     def calculate_datetime_from_offset(amount: int, unit: str, direction: str) -> dict:
#         return DateTimeExtractor._apply_offset(amount, unit, direction)

#     @staticmethod
#     def parse_relative_time(text: str) -> dict | None:
#         for pattern, direction in (
#             (DateTimeExtractor._FUTURE_RE, "future"),
#             (DateTimeExtractor._PAST_RE,   "past"),
#         ):
#             m = pattern.search(text)
#             if m:
#                 amount = int(m.group("amount"))
#                 unit   = DateTimeExtractor.get_unit_type(m.group("unit"))
#                 if unit:
#                     return {
#                         "amount":        amount,
#                         "unit":          unit,
#                         "direction":     direction,
#                         "original_text": m.group(0),
#                     }
#         return None

#     @staticmethod
#     def extract_date_from_message(message: str) -> dict:
#         today = datetime.now().date()
#         now   = datetime.now()
#         ml    = message.lower()

#         # ── 1. Relative offset ───────────────────────────────────────────────
#         rel = DateTimeExtractor.parse_relative_time(message)
#         if rel:
#             r = DateTimeExtractor._apply_offset(rel["amount"], rel["unit"], rel["direction"])
#             if r["datetime"]:
#                 return {
#                     "date":          r["date_only"],
#                     "datetime":      r["datetime"],
#                     "original_text": rel["original_text"],
#                     "type":          "relative_time",
#                     "unit":          rel["unit"],
#                     "amount":        rel["amount"],
#                     "direction":     rel["direction"],
#                 }

#         # ── 2. Named fixed ranges ────────────────────────────────────────────
#         if re.search(r"\b(last week|pichle hafte|पिछले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=7)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "last week", "type": "week"}

#         if re.search(r"\b(last month|pichle mahine|पिछले महीने)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(months=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "last month", "type": "month"}

#         if re.search(r"\b(last year|pichle saal|पिछले साल)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(years=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "last year", "type": "year"}

#         if re.search(r"\b(this week|is hafte|इस हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=today.weekday())
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "this week", "type": "week"}

#         if re.search(r"\b(this month|is mahine|इस महीने)\b", ml, re.IGNORECASE):
#             d = today.replace(day=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "this month", "type": "month"}

#         if re.search(r"\b(this year|is saal|इस साल)\b", ml, re.IGNORECASE):
#             d = today.replace(month=1, day=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "this year", "type": "year"}

#         if re.search(r"\b(next week|agale hafte|अगले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today + timedelta(days=7)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "next week", "type": "week"}

#         if re.search(r"\b(next month|agale mahine|अगले महीने)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(months=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "next month", "type": "month"}

#         if re.search(r"\b(next year|agale saal|अगले साल)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(years=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "next year", "type": "year"}

#         # ── 3. Named days ────────────────────────────────────────────────────
#         if re.search(r"\b(aaj|today|आज|aaj ke|aaj hi|आज ही)\b", ml, re.IGNORECASE | re.UNICODE):
#             return {"date": today.strftime("%Y-%m-%d"), "datetime": now.isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(parso|day after tomorrow|परसों|parso ke|परसों को)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today + timedelta(days=2)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=2)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(parson|day before yesterday|ना परसों)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=2)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=2)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(yesterday|pichle kal|बीता हुआ कल)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=1)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(kal|tomorrow|कल|kal ke|कल को)\b", ml, re.IGNORECASE | re.UNICODE):
#             past_markers = re.search(
#                 r"\b(pehle|pahle|पहले|ago|yesterday|kal pehle|beet gaya)\b",
#                 ml, re.IGNORECASE | re.UNICODE,
#             )
#             offset = -1 if past_markers else 1
#             d = today + timedelta(days=offset)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=offset)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         # ── 4. Explicit date literals ────────────────────────────────────────
#         m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", message)
#         if m:
#             day, month, year = m.groups()
#             try:
#                 specific_date = datetime(int(year), int(month), int(day))
#                 return {"date": specific_date.strftime("%Y-%m-%d"),
#                         "datetime": specific_date.isoformat(),
#                         "original_text": m.group(0), "type": "specific"}
#             except ValueError:
#                 pass

#         m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", message)
#         if m:
#             year, month, day = m.groups()
#             try:
#                 specific_date = datetime(int(year), int(month), int(day))
#                 return {"date": specific_date.strftime("%Y-%m-%d"),
#                         "datetime": specific_date.isoformat(),
#                         "original_text": m.group(0), "type": "specific"}
#             except ValueError:
#                 pass

#         return {"date": None, "datetime": None, "original_text": None, "type": None}


# # ─────────────────────────────────────────────────────────────
# # TASK STRUCTURE EXTRACTOR (Intent Parsing from Munshi Dada)
# # ─────────────────────────────────────────────────────────────
# class TaskStructureExtractor:
#     """
#     Converts free-text instructions into structured task objects.
#     Maps keywords to department/task types.
#     """
    
#     # Keyword to task type mapping
#     KEYWORD_TO_TASK_TYPE = {
#         # Dispatch/Operations
#         "dispatch": "dispatch",
#         "send": "dispatch",
#         "deliver": "dispatch",
#         "ship": "dispatch",
#         "transport": "dispatch",
#         "despatch": "dispatch",
        
#         # Invoice/Accounting
#         "invoice": "invoice",
#         "bill": "invoice",
#         "payment": "invoice",
#         "account": "invoice",
#         "tax": "invoice",
#         "gst": "invoice",
        
#         # Purchase/Procurement
#         "purchase": "purchase",
#         "buy": "purchase",
#         "procure": "purchase",
#         "order": "purchase",
#         "procurement": "purchase",
        
#         # Sales/Followup
#         "followup": "followup",
#         "follow up": "followup",
#         "sales": "followup",
#         "client": "followup",
#         "customer": "followup",
#         "lead": "followup",
#     }
    
#     # Task type to department mapping
#     TASK_TYPE_TO_DEPARTMENT = {
#         "dispatch": "operations",
#         "invoice": "accounting",
#         "purchase": "procurement",
#         "followup": "sales",
#     }
    
#     @staticmethod
#     def extract_quantity(text: str) -> int | None:
#         """Extract quantity from text (e.g., '500 units', '10 pieces')"""
#         patterns = [
#             r"(\d+)\s*(?:units|pieces|items|qty|quantity|nos|no\.?s?)",
#             r"(?:send|deliver|dispatch|order)\s+(\d+)",
#             r"(\d+)\s*units?",
#         ]
#         for pattern in patterns:
#             m = re.search(pattern, text, re.IGNORECASE)
#             if m:
#                 return int(m.group(1))
#         return None
    
#     @staticmethod
#     def extract_deadline(text: str) -> str | None:
#         """Extract deadline information from text"""
#         # Time-based deadlines
#         time_patterns = [
#             r"before\s+(evening|morning|afternoon|night)",
#             r"by\s+(evening|morning|afternoon|night)",
#             r"by\s+(\d{1,2})\s*(?:am|pm)",
#             r"before\s+(\d{1,2})\s*(?:am|pm)",
#             r"today\s+(evening|morning)",
#             r"tomorrow\s+(evening|morning)",
#         ]
        
#         for pattern in time_patterns:
#             m = re.search(pattern, text, re.IGNORECASE)
#             if m:
#                 return m.group(0).lower()
        
#         # Day-based deadlines
#         day_patterns = [
#             r"today",
#             r"tomorrow",
#             r"by\s+(?:this|next)\s+(week|month)",
#             r"within\s+(\d+)\s*(?:hours?|days?)",
#         ]
        
#         for pattern in day_patterns:
#             m = re.search(pattern, text, re.IGNORECASE)
#             if m:
#                 return m.group(0).lower()
        
#         return None
    
#     @staticmethod
#     def detect_task_type(text: str) -> str | None:
#         """Detect task type based on keywords"""
#         text_lower = text.lower()
#         for keyword, task_type in TaskStructureExtractor.KEYWORD_TO_TASK_TYPE.items():
#             if keyword in text_lower:
#                 return task_type
#         return None
    
#     @staticmethod
#     def extract_task_structure(message: str, intent: str) -> dict | None:
#         """
#         Extract structured task object from free-text instruction.
#         Only returns structure for task-related intents or when task-like content is detected.
#         """
#         # Only extract for relevant intents
#         relevant_intents = ["/assign", "/complete", "/update", "general_chat"]
#         if intent not in relevant_intents and not any(
#             keyword in message.lower() for keyword in TaskStructureExtractor.KEYWORD_TO_TASK_TYPE.keys()
#         ):
#             return None
        
#         task_type = TaskStructureExtractor.detect_task_type(message)
        
#         # If no specific task type detected and intent is assign/complete/update, use default
#         if not task_type and intent in ["/assign", "/complete", "/update"]:
#             task_type = "task"
        
#         if not task_type:
#             return None
        
#         quantity = TaskStructureExtractor.extract_quantity(message)
#         deadline = TaskStructureExtractor.extract_deadline(message)
#         department = TaskStructureExtractor.TASK_TYPE_TO_DEPARTMENT.get(task_type)
        
#         result = {"task_type": task_type}
        
#         if quantity:
#             result["quantity"] = quantity
#         if deadline:
#             result["deadline"] = deadline
#         if department:
#             result["department"] = department
        
#         # Extract additional items if present
#         item_patterns = [
#             r"(?:dispatch|send|deliver|order)\s+(\d+)\s+(.+?)(?:\s+(?:before|by|to|for)|$)",
#             r"(\d+)\s+(?:units of|pieces of)?\s*([a-zA-Z\s]+?)(?:\s+(?:before|by|to|for)|$)"
#         ]
        
#         for pattern in item_patterns:
#             m = re.search(pattern, message, re.IGNORECASE)
#             if m and len(m.groups()) >= 2:
#                 if "item" not in result:
#                     result["item"] = m.group(2).strip()
#                 break
        
#         return result if len(result) > 1 else None


# # ─────────────────────────────────────────────────────────────
# # PROFESSIONAL RESPONSE GENERATOR (Only for general_chat) - HINGLISH VERSION
# # ─────────────────────────────────────────────────────────────

# def get_professional_response(message: str, date_info: dict = None) -> str:
#     """
#     Generate a professional, helpful response for general_chat intent in Hinglish.
#     Acknowledges what the user seems to be discussing without suggesting specific intents.
#     """
    
#     message_lower = message.lower()
    
#     # Detect what the user might be talking about
#     is_about_task = any(word in message_lower for word in ['task', 'kaam', 'work', 'complete', 'khatam', 'ho gaya', 'todo', 'karna hai'])
#     is_about_report = any(word in message_lower for word in ['report', 'report de', 'summary', 'data', 'numbers', 'report chahiye'])
#     is_about_update = any(word in message_lower for word in ['update', 'change', 'badlo', 'sudhar', 'modify', 'badalna'])
#     is_about_issue = any(word in message_lower for word in ['issue', 'problem', 'dikkat', 'error', 'galat', 'not working', 'kharab', 'kaam nahi kar raha'])
#     is_about_attendance = any(word in message_lower for word in ['present', 'absent', 'attendance', 'haazri', 'aaj', 'kal', 'aaya', 'nahi aaya'])
#     is_about_team = any(word in message_lower for word in ['team', 'member', 'sathi', 'colleague', 'fellow', 'saathi', 'log'])
    
#     def _fmt_date(d: str) -> str:
#         """YYYY-MM-DD → '18 April 2026'"""
#         try:
#             return datetime.strptime(d, "%Y-%m-%d").strftime("%-d %B %Y")
#         except Exception:
#             return d
    
#     date_str = date_info.get("date") if date_info else None
    
#     if date_str:
#         date_context = f" {_fmt_date(date_str)} ke baare mein"
#     else:
#         date_context = ""
    
#     # Topic-specific professional responses in Hinglish
#     if is_about_task:
#         return (
#             f"Main samajh gaya aap tasks{date_context} pooch rahe ho.\n\n"
#             f"Tasks dekhne ya manage karne ke liye ye commands use karo:\n\n"
#             f"• /tasks - Apna kaam dekhne ke liye\n"
#             f"• /complete [task_id] - Kaam complete mark karne ke liye\n"
#             f"• /assign @username - Kisi aur ko kaam assign karne ke liye\n\n"
#             f"Kya aap inme se koi action karna chahenge?"
#         )
    
#     elif is_about_report:
#         return (
#             f"Main samjha, aap report{date_context} lena chahte ho.\n\n"
#             f"Report generate karne ke liye ye command use karo:\n\n"
#             f"• /report - Poori report generate karne ke liye\n\n"
#             f"Aap time period bhi specify kar sakte ho jaise 'last week' ya 'this month'.\n"
#             f"Kya aap report generate karni hai?"
#         )
    
#     elif is_about_update:
#         return (
#             f"Aap update{date_context} ki baat kar rahe ho.\n\n"
#             f"Update karne ke liye ye commands use karo:\n\n"
#             f"• /update [task_id] - Task ki status ya details update karne ke liye\n"
#             f"• /resolve [issue_id] - Issue resolve mark karne ke liye\n\n"
#             f"Kaunsa update karna hai?"
#         )
    
#     elif is_about_issue:
#         return (
#             f"Main samjha, aap koi issue{date_context} report kar rahe ho.\n\n"
#             f"Better help ke liye ye commands use karo:\n\n"
#             f"• /issue - Naya issue report karne ke liye (problem describe karo)\n"
#             f"• /issues - Saare active issues dekhne ke liye\n"
#             f"• /resolve [issue_id] - Existing issue resolve karne ke liye\n\n"
#             f"Kya aap /issue use karke properly log kar sakte ho? Taaki team isko address kar sake."
#         )
    
#     elif is_about_attendance:
#         return (
#             f"Aap attendance{date_context} ke baare mein pooch rahe ho.\n\n"
#             f"Attendance mark karne ke liye ye commands use karo:\n\n"
#             f"• /present - Apne aap ko present mark karne ke liye\n"
#             f"• /absent - Apne aap ko absent mark karne ke liye\n\n"
#             f"Kya aap apni attendance mark karwana chahenge?"
#         )
    
#     elif is_about_team:
#         return (
#             f"Team members ke baare mein dekhna chahte ho.\n\n"
#             f"Team information dekhne ke liye ye command use karo:\n\n"
#             f"• /members - Saare team members dekhne ke liye\n\n"
#             f"Kya aap team list dekhna chahenge?"
#         )
    
#     # Generic professional help response in Hinglish
#     else:
#         return (
#             f"Thank you for your message. Main task management aur team coordination mein help kar sakta hoon."
#             f"Saare available commands dekhne ke liye help type karo."
#             f"Batao, main aapki kya help kar sakta hoon?"
#         )


# # ─────────────────────────────────────────────────────────────
# # PURE INTENT CLASSIFIER WITH TASK STRUCTURE
# # ─────────────────────────────────────────────────────────────
# class IntentClassifier:
#     def __init__(self):
#         print("✅ Intent Classifier ready.")
#         self.datetime_extractor = DateTimeExtractor()
#         self.task_extractor = TaskStructureExtractor()

#     def classify(self, message: str) -> dict:
#         """
#         Classify the user's message into an intent, extract date/time,
#         and extract structured task object from free-text instructions.
#         """
#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         system = self._build_system_prompt()

#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             messages=[
#                 {"role": "system", "content": system},
#                 {"role": "user",   "content": message},
#             ],
#             temperature=0.2,
#             max_tokens=200,
#             response_format={"type": "json_object"},
#         )

#         raw_reply = response.choices[0].message.content.strip()
#         result = self._parse_decision(raw_reply)
        
#         intent = result.get("intent", "general_chat")

#         # Attach date fields extracted locally (not via LLM)
#         result["date"]               = datetime_info.get("date")
#         result["datetime"]           = datetime_info.get("datetime")
#         result["date_original_text"] = datetime_info.get("original_text")

#         # Extract structured task object for relevant intents
#         task_structure = self.task_extractor.extract_task_structure(message, intent)
#         if task_structure:
#             result["task"] = task_structure
#         else:
#             result["task"] = None

#         # Build professional message ONLY for general_chat intent
#         if intent == "general_chat":
#             result["message"] = get_professional_response(message, datetime_info)
#         else:
#             result["message"] = None  # No message for other intents

#         return result

#     def _build_system_prompt(self) -> str:
#         return """You are a pure intent classification system with date extraction capability.
# Your ONLY job is to classify the user's message into one intent and extract any relevant information.
# Respond with ONLY a valid JSON object. Do not include any other text, markdown, or explanations.

# === INTENTS ===

# 1. "/present"    — Marking attendance as present
#                    Keywords: present, aa gaya, aaya, pahunch gaya, main present hu, aaj aaya hu

# 2. "/absent"     — Marking attendance as absent
#                    Keywords: absent, nahi aa sakta, chutti, leave, aaj nahi aaunga

# 3. "/tasks"      — View tasks
#                    Keywords: tasks, kaam dikhao, task list, mera kaam, kya karna hai

# 4. "/complete"   — Marking a task as complete (extract task ID if given)
#                    Keywords: complete, ho gaya, khatam, done, finished
#                    Example: "complete 2"  →  id: 2

# 5. "/assign"     — Assigning a task to someone (extract @username or phone number)
#                    Keywords: assign, @user, @all, de do, allocate

# 6. "/update"     — Updating a task with a comment / status (extract task ID if given)
#                    Keywords: update, add comment, status update

# 7. "/issue"      — Reporting a new issue (extract issue ID if referenced)
#                    Keywords: issue, problem, dikkat, not working, broken

# 8. "/issues"     — View all active issues
#                    Keywords: issues, active issues, problems list

# 9. "/resolve"    — Resolving an issue (extract issue ID)
#                    Keywords: resolve, fixed, solved, hatado, resolved hogya

# 10. "/members"   — View team members
#                    Keywords: members, team, sab log

# 11. "/report"    — Generate a report / summary
#                    Keywords: report, summary, report de do

# 12. "/help"      — Need help with available commands
#                    Keywords: help, commands, kya karein

# 13. "general_chat" — General conversation / anything that doesn't match above

# === OUTPUT FORMAT ===
# {"intent": "<intent_name>", "id": <id_value or null>}

# Examples:
# {"intent": "/present", "id": null}
# {"intent": "/complete", "id": 2}
# {"intent": "general_chat", "id": null}

# Note: date fields and task structure are added separately by the system — do NOT include them.
# """

#     def _parse_decision(self, raw: str) -> dict:
#         try:
#             return json.loads(raw)
#         except Exception:
#             clean = re.sub(r"```json|```", "", raw).strip()
#             try:
#                 return json.loads(clean)
#             except Exception:
#                 return {"intent": "general_chat", "id": None}


# # ─────────────────────────────────────────────────────────────
# # COMMAND PARSER
# # ─────────────────────────────────────────────────────────────
# class CommandParser:
#     """Parse explicit slash commands without any database dependency."""

#     def __init__(self):
#         self.datetime_extractor = DateTimeExtractor()
#         self.task_extractor = TaskStructureExtractor()

#     def parse(self, message: str) -> dict | None:
#         """
#         Parse a slash command and return an intent dict with extracted
#         parameters, resolved date, and task structure.
#         """
#         message = message.strip()
#         ml = message.lower()

#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         def base(intent, id_=None):
#             # Extract task structure for assign/update commands
#             task_structure = None
#             if intent in ["/assign", "/update", "/complete"]:
#                 task_structure = self.task_extractor.extract_task_structure(message, intent)
            
#             result = {
#                 "intent":          intent,
#                 "id":              id_,
#                 "date":            datetime_info.get("date"),
#                 "datetime":        datetime_info.get("datetime"),
#                 "task":            task_structure,
#                 "message":         None,  # Slash commands have no message
#             }
#             return result

#         def extract_leading_int(text: str):
#             m = re.search(r"^\d+", text.strip())
#             return int(m.group()) if m else None

#         if ml.startswith("/issues"):
#             return base("/issues")

#         if ml.startswith("/issue"):
#             return base("/issue", extract_leading_int(message[6:]))

#         if ml.startswith("/present"):
#             return base("/present")

#         if ml.startswith("/absent"):
#             return base("/absent")

#         if ml.startswith("/tasks"):
#             return base("/tasks")

#         if ml.startswith("/complete"):
#             return base("/complete", extract_leading_int(message[9:]))

#         if ml.startswith("/assign"):
#             rest = message[7:].strip()
#             m = re.search(r"@(\d+)", rest)
#             if m:
#                 return base("/assign", f"@{m.group(1)}")
#             m = re.search(r"(\d{10})", rest)
#             if m:
#                 return base("/assign", m.group(1))
#             m = re.search(r"@(\w+)", rest)
#             if m:
#                 return base("/assign", f"@{m.group(1)}")
#             return base("/assign")

#         if ml.startswith("/update"):
#             return base("/update", extract_leading_int(message[7:]))

#         if ml.startswith("/resolve"):
#             return base("/resolve", extract_leading_int(message[8:]))

#         if ml.startswith("/members"):
#             return base("/members")

#         if ml.startswith("/report"):
#             return base("/report")

#         if ml.startswith("/help"):
#             return base("/help")

#         return None






































# """
# bot_engine.py — Pure Intent Classifier with Task Structure Extraction for Worker Assistant
# No database, no worker_id, just intent classification with date extraction & task structuring
# """

# import json
# import os
# import re
# from datetime import datetime, timedelta
# from dateutil.relativedelta import relativedelta
# from openai import OpenAI
# from dotenv import load_dotenv

# load_dotenv()
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# CHAT_MODEL = "gpt-4o-mini"


# # ─────────────────────────────────────────────────────────────
# # DATE UTILITY FUNCTIONS (Time extraction removed)
# # ─────────────────────────────────────────────────────────────
# class DateTimeExtractor:

#     WORD_TO_UNIT = {
#         # ── seconds ──────────────────────────────────────────
#         "second": "seconds", "seconds": "seconds", "sec": "seconds", "secs": "seconds",
#         "सेकंड": "seconds", "सेकेंड": "seconds",
#         # ── minutes ──────────────────────────────────────────
#         "minute": "minutes", "minutes": "minutes", "min": "minutes", "mins": "minutes",
#         "मिनट": "minutes", "मिनटों": "minutes",
#         # ── hours ────────────────────────────────────────────
#         "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours", "h": "hours",
#         "ghanta": "hours", "ghante": "hours", "घंटा": "hours", "घंटे": "hours",
#         # ── days ─────────────────────────────────────────────
#         "day": "days", "days": "days", "d": "days",
#         "din": "days", "दिन": "days", "दिनों": "days",
#         # ── weeks ────────────────────────────────────────────
#         "week": "weeks", "weeks": "weeks", "wk": "weeks", "wks": "weeks",
#         "hafte": "weeks", "hafta": "weeks", "हफ्ता": "weeks", "हफ्ते": "weeks",
#         "सप्ताह": "weeks",
#         # ── months ───────────────────────────────────────────
#         "month": "months", "months": "months", "mon": "months", "mons": "months",
#         "mahina": "months", "mahine": "months", "महीना": "months", "महीने": "months",
#         # ── years ────────────────────────────────────────────
#         "year": "years", "years": "years", "yr": "years", "yrs": "years", "y": "years",
#         "saal": "years", "साल": "years", "वर्ष": "years",
#     }

#     _UNIT_RE = (
#         r"(?P<unit>"
#         r"seconds?|secs?|sec"
#         r"|minutes?|mins?|min"
#         r"|hours?|hrs?"
#         r"|ghante|ghanta"
#         r"|weeks?|wks?|wk"
#         r"|hafte|hafta"
#         r"|months?|mons?"
#         r"|mahine|mahina"
#         r"|years?|yrs?"
#         r"|saal"
#         r"|days?"
#         r"|din"
#         r"|घंटे|घंटा|मिनट|सेकंड|सेकेंड"
#         r"|दिन|दिनों|हफ्ता|हफ्ते|सप्ताह"
#         r"|महीना|महीने|साल|वर्ष"
#         r")"
#     )

#     _FUTURE_RE = re.compile(
#         r"(?:in|after)?\s*(?P<amount>\d+)\s*"
#         + _UNIT_RE
#         + r"(?:\s*(?:ke\s*)?(?:baad|mein|में|बाद|after|later|from\s*now))",
#         re.IGNORECASE | re.UNICODE,
#     )

#     _PAST_RE = re.compile(
#         r"(?P<amount>\d+)\s*"
#         + _UNIT_RE
#         + r"(?:\s*(?:pehle|pahle|पहले|before|ago))",
#         re.IGNORECASE | re.UNICODE,
#     )

#     @staticmethod
#     def get_unit_type(unit_text: str) -> str:
#         return (
#             DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip().lower())
#             or DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip())
#         )

#     @staticmethod
#     def _apply_offset(amount: int, unit: str, direction: str) -> dict:
#         now = datetime.now()
#         sign = 1 if direction == "future" else -1

#         delta_map = {
#             "seconds": timedelta(seconds=amount * sign),
#             "minutes": timedelta(minutes=amount * sign),
#             "hours":   timedelta(hours=amount * sign),
#             "days":    timedelta(days=amount * sign),
#             "weeks":   timedelta(weeks=amount * sign),
#             "months":  relativedelta(months=amount * sign),
#             "years":   relativedelta(years=amount * sign),
#         }
#         delta = delta_map.get(unit)
#         if delta is None:
#             return {"datetime": None, "date_only": None}

#         target = now + delta
#         return {
#             "datetime":  target.isoformat(),
#             "date_only": target.strftime("%Y-%m-%d"),
#         }

#     @staticmethod
#     def calculate_datetime_from_offset(amount: int, unit: str, direction: str) -> dict:
#         return DateTimeExtractor._apply_offset(amount, unit, direction)

#     @staticmethod
#     def parse_relative_time(text: str) -> dict | None:
#         for pattern, direction in (
#             (DateTimeExtractor._FUTURE_RE, "future"),
#             (DateTimeExtractor._PAST_RE,   "past"),
#         ):
#             m = pattern.search(text)
#             if m:
#                 amount = int(m.group("amount"))
#                 unit   = DateTimeExtractor.get_unit_type(m.group("unit"))
#                 if unit:
#                     return {
#                         "amount":        amount,
#                         "unit":          unit,
#                         "direction":     direction,
#                         "original_text": m.group(0),
#                     }
#         return None

#     @staticmethod
#     def extract_date_from_message(message: str) -> dict:
#         today = datetime.now().date()
#         now   = datetime.now()
#         ml    = message.lower()

#         # ── 1. Relative offset ───────────────────────────────────────────────
#         rel = DateTimeExtractor.parse_relative_time(message)
#         if rel:
#             r = DateTimeExtractor._apply_offset(rel["amount"], rel["unit"], rel["direction"])
#             if r["datetime"]:
#                 return {
#                     "date":          r["date_only"],
#                     "datetime":      r["datetime"],
#                     "original_text": rel["original_text"],
#                     "type":          "relative_time",
#                     "unit":          rel["unit"],
#                     "amount":        rel["amount"],
#                     "direction":     rel["direction"],
#                 }

#         # ── 2. Named fixed ranges ────────────────────────────────────────────
#         if re.search(r"\b(last week|pichle hafte|पिछले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=7)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "last week", "type": "week"}

#         if re.search(r"\b(last month|pichle mahine|पिछले महीने)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(months=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "last month", "type": "month"}

#         if re.search(r"\b(last year|pichle saal|पिछले साल)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(years=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "last year", "type": "year"}

#         if re.search(r"\b(this week|is hafte|इस हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=today.weekday())
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "this week", "type": "week"}

#         if re.search(r"\b(this month|is mahine|इस महीने)\b", ml, re.IGNORECASE):
#             d = today.replace(day=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "this month", "type": "month"}

#         if re.search(r"\b(this year|is saal|इस साल)\b", ml, re.IGNORECASE):
#             d = today.replace(month=1, day=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "this year", "type": "year"}

#         if re.search(r"\b(next week|agale hafte|अगले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today + timedelta(days=7)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "next week", "type": "week"}

#         if re.search(r"\b(next month|agale mahine|अगले महीने)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(months=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "next month", "type": "month"}

#         if re.search(r"\b(next year|agale saal|अगले साल)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(years=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": None,
#                     "original_text": "next year", "type": "year"}

#         # ── 3. Named days ────────────────────────────────────────────────────
#         if re.search(r"\b(aaj|today|आज|aaj ke|aaj hi|आज ही)\b", ml, re.IGNORECASE | re.UNICODE):
#             return {"date": today.strftime("%Y-%m-%d"), "datetime": now.isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(parso|day after tomorrow|परसों|parso ke|परसों को)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today + timedelta(days=2)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=2)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(parson|day before yesterday|ना परसों)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=2)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=2)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(yesterday|pichle kal|बीता हुआ कल)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=1)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=1)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         if re.search(r"\b(kal|tomorrow|कल|kal ke|कल को)\b", ml, re.IGNORECASE | re.UNICODE):
#             past_markers = re.search(
#                 r"\b(pehle|pahle|पहले|ago|yesterday|kal pehle|beet gaya)\b",
#                 ml, re.IGNORECASE | re.UNICODE,
#             )
#             offset = -1 if past_markers else 1
#             d = today + timedelta(days=offset)
#             return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=offset)).isoformat(),
#                     "original_text": None, "type": "relative"}

#         # ── 4. Explicit date literals ────────────────────────────────────────
#         m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", message)
#         if m:
#             day, month, year = m.groups()
#             try:
#                 specific_date = datetime(int(year), int(month), int(day))
#                 return {"date": specific_date.strftime("%Y-%m-%d"),
#                         "datetime": specific_date.isoformat(),
#                         "original_text": m.group(0), "type": "specific"}
#             except ValueError:
#                 pass

#         m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", message)
#         if m:
#             year, month, day = m.groups()
#             try:
#                 specific_date = datetime(int(year), int(month), int(day))
#                 return {"date": specific_date.strftime("%Y-%m-%d"),
#                         "datetime": specific_date.isoformat(),
#                         "original_text": m.group(0), "type": "specific"}
#             except ValueError:
#                 pass

#         return {"date": None, "datetime": None, "original_text": None, "type": None}


# # ─────────────────────────────────────────────────────────────
# # TASK STRUCTURE EXTRACTOR (Intent Parsing from Munshi Dada)
# # ─────────────────────────────────────────────────────────────
# class TaskStructureExtractor:
#     """
#     Converts free-text instructions into structured task objects.
#     Maps keywords to department/task types.
#     """
    
#     # Keyword to task type mapping
#     KEYWORD_TO_TASK_TYPE = {
#         # Dispatch/Operations
#         "dispatch": "dispatch",
#         "send": "dispatch",
#         "deliver": "dispatch",
#         "ship": "dispatch",
#         "transport": "dispatch",
#         "despatch": "dispatch",
        
#         # Invoice/Accounting
#         "invoice": "invoice",
#         "bill": "invoice",
#         "payment": "invoice",
#         "account": "invoice",
#         "tax": "invoice",
#         "gst": "invoice",
        
#         # Purchase/Procurement
#         "purchase": "purchase",
#         "buy": "purchase",
#         "procure": "purchase",
#         "order": "purchase",
#         "procurement": "purchase",
        
#         # Sales/Followup
#         "followup": "followup",
#         "follow up": "followup",
#         "sales": "followup",
#         "client": "followup",
#         "customer": "followup",
#         "lead": "followup",
#     }
    
#     # Task type to department mapping
#     TASK_TYPE_TO_DEPARTMENT = {
#         "dispatch": "operations",
#         "invoice": "accounting",
#         "purchase": "procurement",
#         "followup": "sales",
#     }
    
#     @staticmethod
#     def extract_quantity(text: str) -> int | None:
#         """Extract quantity from text (e.g., '500 units', '10 pieces')"""
#         patterns = [
#             r"(\d+)\s*(?:units|pieces|items|qty|quantity|nos|no\.?s?)",
#             r"(?:send|deliver|dispatch|order)\s+(\d+)",
#             r"(\d+)\s*units?",
#         ]
#         for pattern in patterns:
#             m = re.search(pattern, text, re.IGNORECASE)
#             if m:
#                 return int(m.group(1))
#         return None
    
#     @staticmethod
#     def extract_deadline(text: str) -> str | None:
#         """Extract deadline information from text"""
#         # Time-based deadlines
#         time_patterns = [
#             r"before\s+(evening|morning|afternoon|night)",
#             r"by\s+(evening|morning|afternoon|night)",
#             r"by\s+(\d{1,2})\s*(?:am|pm)",
#             r"before\s+(\d{1,2})\s*(?:am|pm)",
#             r"today\s+(evening|morning)",
#             r"tomorrow\s+(evening|morning)",
#         ]
        
#         for pattern in time_patterns:
#             m = re.search(pattern, text, re.IGNORECASE)
#             if m:
#                 return m.group(0).lower()
        
#         # Day-based deadlines
#         day_patterns = [
#             r"today",
#             r"tomorrow",
#             r"by\s+(?:this|next)\s+(week|month)",
#             r"within\s+(\d+)\s*(?:hours?|days?)",
#         ]
        
#         for pattern in day_patterns:
#             m = re.search(pattern, text, re.IGNORECASE)
#             if m:
#                 return m.group(0).lower()
        
#         return None
    
#     @staticmethod
#     def detect_task_type(text: str) -> str | None:
#         """Detect task type based on keywords"""
#         text_lower = text.lower()
#         for keyword, task_type in TaskStructureExtractor.KEYWORD_TO_TASK_TYPE.items():
#             if keyword in text_lower:
#                 return task_type
#         return None
    
#     @staticmethod
#     def extract_task_structure(message: str) -> dict | None:
#         """
#         Extract structured task object from free-text instruction.
#         Only returns structure for general_chat intent.
#         """
#         task_type = TaskStructureExtractor.detect_task_type(message)
        
#         if not task_type:
#             return None
        
#         quantity = TaskStructureExtractor.extract_quantity(message)
#         deadline = TaskStructureExtractor.extract_deadline(message)
#         department = TaskStructureExtractor.TASK_TYPE_TO_DEPARTMENT.get(task_type)
        
#         result = {"task_type": task_type}
        
#         if quantity:
#             result["quantity"] = quantity
#         if deadline:
#             result["deadline"] = deadline
#         if department:
#             result["department"] = department
        
#         # Extract additional items if present
#         item_patterns = [
#             r"(?:dispatch|send|deliver|order)\s+(\d+)\s+(.+?)(?:\s+(?:before|by|to|for)|$)",
#             r"(\d+)\s+(?:units of|pieces of)?\s*([a-zA-Z\s]+?)(?:\s+(?:before|by|to|for)|$)"
#         ]
        
#         for pattern in item_patterns:
#             m = re.search(pattern, message, re.IGNORECASE)
#             if m and len(m.groups()) >= 2:
#                 if "item" not in result:
#                     result["item"] = m.group(2).strip()
#                 break
        
#         return result if len(result) > 1 else None


# # ─────────────────────────────────────────────────────────────
# # PROFESSIONAL RESPONSE GENERATOR (Only for general_chat) - HINGLISH VERSION
# # ─────────────────────────────────────────────────────────────

# def get_professional_response(message: str, date_info: dict = None) -> str:
#     """
#     Generate a professional, helpful response for general_chat intent in Hinglish.
#     Acknowledges what the user seems to be discussing without suggesting specific intents.
#     """
    
#     message_lower = message.lower()
    
#     # Expanded keyword lists for better detection
#     task_keywords = [
#         'task', 'kaam', 'work', 'complete', 'khatam', 'ho gaya', 'todo', 'karna hai',
#         'pending', 'baaki', 'assign', 'dekhna', 'dikhao', 'list', 'mera kaam',
#         'kya karna hai', 'task list', 'kaam khatam', 'task complete', 'ho gya'
#     ]
    
#     report_keywords = [
#         'report', 'report de', 'summary', 'data', 'numbers', 'report chahiye',
#         'report do', 'summary do', 'report generate', 'report nikal', 'report bhej',
#         'statistics', 'information', 'poori report'
#     ]
    
#     update_keywords = [
#         'update', 'change', 'badlo', 'sudhar', 'modify', 'badalna', 'status',
#         'badlav', 'change karo', 'update karo', 'modify karo', 'badal do'
#     ]
    
#     issue_keywords = [
#         'issue', 'problem', 'dikkat', 'error', 'galat', 'not working', 'kharab',
#         'kaam nahi kar raha', 'issue hai', 'problem hai', 'dikkat hai', 'machine',
#         'kharab hai', 'fix karo', 'solve karo', 'issue report'
#     ]
    
#     attendance_keywords = [
#         'present', 'absent', 'attendance', 'haazri', 'aaj', 'kal', 'aaya', 'nahi aaya',
#         'chutti', 'leave', 'present hu', 'absent hu', 'haazri lago', 'mark attendance',
#         'aa gaya', 'aaj aaya', 'nahi aa sakta', 'chahiye chutti'
#     ]
    
#     team_keywords = [
#         'team', 'member', 'sathi', 'colleague', 'fellow', 'saathi', 'log',
#         'team members', 'sab log', 'kaun kaun', 'team list', 'members list',
#         'team dekh', 'saare members', 'fellow workers'
#     ]
    
#     # Detection logic
#     is_about_task = any(keyword in message_lower for keyword in task_keywords)
#     is_about_report = any(keyword in message_lower for keyword in report_keywords)
#     is_about_update = any(keyword in message_lower for keyword in update_keywords)
#     is_about_issue = any(keyword in message_lower for keyword in issue_keywords)
#     is_about_attendance = any(keyword in message_lower for keyword in attendance_keywords)
#     is_about_team = any(keyword in message_lower for keyword in team_keywords)
    
#     def _fmt_date(d: str) -> str:
#         """YYYY-MM-DD → '18 April 2026'"""
#         try:
#             return datetime.strptime(d, "%Y-%m-%d").strftime("%-d %B %Y")
#         except Exception:
#             return d
    
#     date_str = date_info.get("date") if date_info else None
    
#     if date_str:
#         date_context = f" {_fmt_date(date_str)} ke baare mein"
#     else:
#         date_context = ""
    
#     # Topic-specific professional responses in Hinglish
#     if is_about_task:
#         return (
#             f"Main samajh gaya aap tasks{date_context} pooch rahe ho.\n\n"
#             f"Tasks dekhne ya manage karne ke liye ye commands use karo:\n\n"
#             f"• /tasks - Apna kaam dekhne ke liye\n"
#             f"• /complete [task_id] - Kaam complete mark karne ke liye\n"
#             f"• /assign @username - Kisi aur ko kaam assign karne ke liye\n\n"
#             f"Kya aap inme se koi action karna chahenge?"
#         )
    
#     elif is_about_report:
#         return (
#             f"Main samjha, aap report{date_context} lena chahte ho.\n\n"
#             f"Report generate karne ke liye ye command use karo:\n\n"
#             f"• /report - Poori report generate karne ke liye\n\n"
#             f"Aap time period bhi specify kar sakte ho jaise 'last week' ya 'this month'.\n"
#             f"Kya aap report generate karni hai?"
#         )
    
#     elif is_about_update:
#         return (
#             f"Aap update{date_context} ki baat kar rahe ho.\n\n"
#             f"Update karne ke liye ye commands use karo:\n\n"
#             f"• /update [task_id] - Task ki status ya details update karne ke liye\n"
#             f"• /resolve [issue_id] - Issue resolve mark karne ke liye\n\n"
#             f"Kaunsa update karna hai?"
#         )
    
#     elif is_about_issue:
#         return (
#             f"Main samjha, aap koi issue{date_context} report kar rahe ho.\n\n"
#             f"Better help ke liye ye commands use karo:\n\n"
#             f"• /issue - Naya issue report karne ke liye (problem describe karo)\n"
#             f"• /issues - Saare active issues dekhne ke liye\n"
#             f"• /resolve [issue_id] - Existing issue resolve karne ke liye\n\n"
#             f"Kya aap /issue use karke properly log kar sakte ho? Taaki team isko address kar sake."
#         )
    
#     elif is_about_attendance:
#         return (
#             f"Aap attendance{date_context} ke baare mein pooch rahe ho.\n\n"
#             f"Attendance mark karne ke liye ye commands use karo:\n\n"
#             f"• /present - Apne aap ko present mark karne ke liye\n"
#             f"• /absent - Apne aap ko absent mark karne ke liye\n\n"
#             f"Kya aap apni attendance mark karwana chahenge?"
#         )
    
#     elif is_about_team:
#         return (
#             f"Team members ke baare mein dekhna chahte ho.\n\n"
#             f"Team information dekhne ke liye ye command use karo:\n\n"
#             f"• /members - Saare team members dekhne ke liye\n\n"
#             f"Kya aap team list dekhna chahenge?"
#         )
    
#     # Generic professional help response in Hinglish
#     else:
#         import random
#         generic_responses = [
#             (
#                 f"Thank you for your message. Main task management aur team coordination mein help kar sakta hoon.\n\n"
#                 f"Saare available commands dekhne ke liye /help type karo.\n\n"
#                 f"Batao, main aapki kya help kar sakta hoon?"
#             )
#         ]
#         return random.choice(generic_responses)


# # ─────────────────────────────────────────────────────────────
# # PURE INTENT CLASSIFIER WITH TASK STRUCTURE
# # ─────────────────────────────────────────────────────────────
# class IntentClassifier:
#     def __init__(self):
#         print("✅ Intent Classifier ready.")
#         self.datetime_extractor = DateTimeExtractor()
#         self.task_extractor = TaskStructureExtractor()

#     def classify(self, message: str) -> dict:
#         """
#         Classify the user's message into an intent, extract date/time,
#         and extract structured task object from free-text instructions.
#         """
#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         system = self._build_system_prompt()

#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             messages=[
#                 {"role": "system", "content": system},
#                 {"role": "user",   "content": message},
#             ],
#             temperature=0.2,
#             max_tokens=200,
#             response_format={"type": "json_object"},
#         )

#         raw_reply = response.choices[0].message.content.strip()
#         result = self._parse_decision(raw_reply)
        
#         intent = result.get("intent", "general_chat")

#         # Attach date fields extracted locally (not via LLM)
#         result["date"]               = datetime_info.get("date")
#         result["datetime"]           = datetime_info.get("datetime")
#         result["date_original_text"] = datetime_info.get("original_text")

#         # Extract structured task object ONLY for general_chat intent
#         if intent == "general_chat":
#             task_structure = self.task_extractor.extract_task_structure(message)
#             result["task"] = task_structure if task_structure else None
#         else:
#             result["task"] = None

#         # Build professional message ONLY for general_chat intent
#         if intent == "general_chat":
#             result["message"] = get_professional_response(message, datetime_info)
#         else:
#             result["message"] = None

#         return result

#     def _build_system_prompt(self) -> str:
#         return """You are a pure intent classification system with date extraction capability.
# Your ONLY job is to classify the user's message into one intent and extract any relevant information.
# Respond with ONLY a valid JSON object. Do not include any other text, markdown, or explanations.

# === INTENTS ===

# 1. "/present"    — Marking attendance as present
#                    Keywords: present, aa gaya, aaya, pahunch gaya, main present hu, aaj aaya hu

# 2. "/absent"     — Marking attendance as absent
#                    Keywords: absent, nahi aa sakta, chutti, leave, aaj nahi aaunga

# 3. "/tasks"      — View tasks or talk about completing tasks
#                    Keywords: tasks, kaam dikhao, task list, mera kaam, kya karna hai, complete karna, khatam karna

# 4. "/complete"   — IMMEDIATE marking of a task as complete (only for past/done tasks, NOT future)
#                    Keywords: complete, ho gaya, khatam, done, finished (ONLY when task is already done)

# 5. "/assign"     — Assigning a NEW task to someone (creates new task)
#                    Keywords: assign, @user, @all, de do, allocate

# 6. "/update"     — Updating a task with a comment / status (extract task ID if given)
#                    Keywords: update, add comment, status update

# 7. "/issue"      — Reporting a new issue (extract issue ID if referenced)
#                    Keywords: issue, problem, dikkat, not working, broken

# 8. "/issues"     — View all active issues
#                    Keywords: issues, active issues, problems list

# 9. "/resolve"    — Resolving an issue (extract issue ID)
#                    Keywords: resolve, fixed, solved, hatado, resolved hogya

# 10. "/members"   — View team members
#                    Keywords: members, team, sab log

# 11. "/report"    — Generate a report / summary
#                    Keywords: report, summary, report de do

# 12. "/help"      — Need help with available commands
#                    Keywords: help, commands, kya karein

# 13. "/mgrself"   — MANAGER: Self-assign an existing task (task already exists)
#                    Keywords: main karunga, khud karunga, i will do it myself, myself, self assign
#                    Example: "task 32 main khud karunga" → intent: "/mgrself", id: 32

# 14. "/mgrassign" — MANAGER: Assign existing task to a worker (task already exists)
#                    Keywords: assign to @username, @user ko do, @user karega
#                    Example: "task 32 @ajay ko do" → intent: "/mgrassign", id: 32, worker_slug: "@ajay"

# 15. "general_chat" — General conversation / anything that doesn't match above

# === IMPORTANT RULES ===
# - "/complete" is ONLY for tasks that are ALREADY DONE (past tense like "ho gaya", "khatam")
# - If user talks about completing a task in FUTURE (e.g., "2 ghante baad complete karna"), classify as "/tasks"
# - "/assign" creates a NEW task and assigns it
# - "/mgrself" and "/mgrassign" are for EXISTING tasks (task already created, manager now acting on it)
# - Look for task IDs (numbers) in the message for mgrself/mgrassign

# === OUTPUT FORMAT ===
# {"intent": "<intent_name>", "id": <id_value or null>, "worker_slug": "<@username or null>"}

# Examples:
# {"intent": "/present", "id": null, "worker_slug": null}
# {"intent": "/complete", "id": 2, "worker_slug": null}
# {"intent": "/tasks", "id": null, "worker_slug": null}
# {"intent": "/mgrself", "id": 32, "worker_slug": null}
# {"intent": "/mgrassign", "id": 32, "worker_slug": "@ajay"}
# {"intent": "general_chat", "id": null, "worker_slug": null}

# Note: date fields and task structure are added separately by the system — do NOT include them.
# """

#     def _parse_decision(self, raw: str) -> dict:
#         try:
#             return json.loads(raw)
#         except Exception:
#             clean = re.sub(r"```json|```", "", raw).strip()
#             try:
#                 return json.loads(clean)
#             except Exception:
#                 return {"intent": "general_chat", "id": None, "worker_slug": None}


# # ─────────────────────────────────────────────────────────────
# # COMMAND PARSER
# # ─────────────────────────────────────────────────────────────
# class CommandParser:
#     """Parse explicit slash commands without any database dependency."""

#     def __init__(self):
#         self.datetime_extractor = DateTimeExtractor()
#         self.task_extractor = TaskStructureExtractor()

#     def parse(self, message: str) -> dict | None:
#         """
#         Parse a slash command and return an intent dict with extracted
#         parameters, resolved date, and task structure.
#         """
#         message = message.strip()
#         ml = message.lower()

#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         def base(intent, id_=None, worker_slug=None):
#             result = {
#                 "intent":          intent,
#                 "id":              id_,
#                 "worker_slug":     worker_slug,
#                 "date":            datetime_info.get("date"),
#                 "datetime":        datetime_info.get("datetime"),
#                 "task":            None,  # No task structure for commands
#                 "message":         None,  # No message for commands
#             }
#             return result

#         def extract_leading_int(text: str):
#             m = re.search(r"^\d+", text.strip())
#             return int(m.group()) if m else None

#         if ml.startswith("/issues"):
#             return base("/issues")

#         if ml.startswith("/issue"):
#             return base("/issue", extract_leading_int(message[6:]))

#         if ml.startswith("/present"):
#             return base("/present")

#         if ml.startswith("/absent"):
#             return base("/absent")

#         if ml.startswith("/tasks"):
#             return base("/tasks")

#         if ml.startswith("/complete"):
#             return base("/complete", extract_leading_int(message[9:]))

#         if ml.startswith("/assign"):
#             rest = message[7:].strip()
#             m = re.search(r"@(\d+)", rest)
#             if m:
#                 return base("/assign", None, f"@{m.group(1)}")
#             m = re.search(r"(\d{10})", rest)
#             if m:
#                 return base("/assign", None, m.group(1))
#             m = re.search(r"@(\w+)", rest)
#             if m:
#                 return base("/assign", None, f"@{m.group(1)}")
#             return base("/assign")

#         if ml.startswith("/update"):
#             return base("/update", extract_leading_int(message[7:]))

#         if ml.startswith("/resolve"):
#             return base("/resolve", extract_leading_int(message[8:]))

#         if ml.startswith("/members"):
#             return base("/members")

#         if ml.startswith("/report"):
#             return base("/report")

#         if ml.startswith("/help"):
#             return base("/help")
        
#         if ml.startswith("/mgrself"):
#             return base("/mgrself", extract_leading_int(message[8:]))
        
#         if ml.startswith("/mgrassign"):
#             rest = message[10:].strip()
#             # Extract task ID and worker
#             id_match = re.search(r"(\d+)", rest)
#             worker_match = re.search(r"@(\w+)", rest)
#             task_id = int(id_match.group(1)) if id_match else None
#             worker_slug = f"@{worker_match.group(1)}" if worker_match else None
#             return base("/mgrassign", task_id, worker_slug)

#         return None









"""
bot_engine.py — Pure Intent Classifier for Worker Assistant
No database, no worker_id, just intent classification with date extraction
"""

import json
import os
import re
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHAT_MODEL = "gpt-4o-mini"


# ─────────────────────────────────────────────────────────────
# DATE UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────
class DateTimeExtractor:

    WORD_TO_UNIT = {
        "second": "seconds", "seconds": "seconds", "sec": "seconds", "secs": "seconds",
        "सेकंड": "seconds", "सेकेंड": "seconds",
        "minute": "minutes", "minutes": "minutes", "min": "minutes", "mins": "minutes",
        "मिनट": "minutes", "मिनटों": "minutes",
        "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours", "h": "hours",
        "ghanta": "hours", "ghante": "hours", "घंटा": "hours", "घंटे": "hours",
        "day": "days", "days": "days", "d": "days",
        "din": "days", "दिन": "days", "दिनों": "days",
        "week": "weeks", "weeks": "weeks", "wk": "weeks", "wks": "weeks",
        "hafte": "weeks", "hafta": "weeks", "हफ्ता": "weeks", "हफ्ते": "weeks",
        "सप्ताह": "weeks",
        "month": "months", "months": "months", "mon": "months", "mons": "months",
        "mahina": "months", "mahine": "months", "महीना": "months", "महीने": "months",
        "year": "years", "years": "years", "yr": "years", "yrs": "years", "y": "years",
        "saal": "years", "साल": "years", "वर्ष": "years",
    }

    _UNIT_RE = (
        r"(?P<unit>"
        r"seconds?|secs?|sec"
        r"|minutes?|mins?|min"
        r"|hours?|hrs?"
        r"|ghante|ghanta"
        r"|weeks?|wks?|wk"
        r"|hafte|hafta"
        r"|months?|mons?"
        r"|mahine|mahina"
        r"|years?|yrs?"
        r"|saal"
        r"|days?"
        r"|din"
        r"|घंटे|घंटा|मिनट|सेकंड|सेकेंड"
        r"|दिन|दिनों|हफ्ता|हफ्ते|सप्ताह"
        r"|महीना|महीने|साल|वर्ष"
        r")"
    )

    _FUTURE_RE = re.compile(
        r"(?:in|after)?\s*(?P<amount>\d+)\s*"
        + _UNIT_RE
        + r"(?:\s*(?:ke\s*)?(?:baad|mein|में|बाद|after|later|from\s*now))",
        re.IGNORECASE | re.UNICODE,
    )

    _PAST_RE = re.compile(
        r"(?P<amount>\d+)\s*"
        + _UNIT_RE
        + r"(?:\s*(?:pehle|pahle|पहले|before|ago))",
        re.IGNORECASE | re.UNICODE,
    )

    _CLOCK_RE = re.compile(
        r"(\d{1,2})(?::(\d{2}))?\s*(?:(am|pm)|(?:bje|baje|baj|बजे|बज))",
        re.IGNORECASE | re.UNICODE,
    )

    @staticmethod
    def get_unit_type(unit_text: str) -> str:
        return (
            DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip().lower())
            or DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip())
        )

    @staticmethod
    def _apply_offset(amount: int, unit: str, direction: str) -> dict:
        now = datetime.now()
        sign = 1 if direction == "future" else -1

        delta_map = {
            "seconds": timedelta(seconds=amount * sign),
            "minutes": timedelta(minutes=amount * sign),
            "hours":   timedelta(hours=amount * sign),
            "days":    timedelta(days=amount * sign),
            "weeks":   timedelta(weeks=amount * sign),
            "months":  relativedelta(months=amount * sign),
            "years":   relativedelta(years=amount * sign),
        }
        delta = delta_map.get(unit)
        if delta is None:
            return {"datetime": None, "date_only": None}

        target = now + delta
        return {
            "datetime":  target.isoformat(),
            "date_only": target.strftime("%Y-%m-%d"),
        }

    @staticmethod
    def calculate_datetime_from_offset(amount: int, unit: str, direction: str) -> dict:
        return DateTimeExtractor._apply_offset(amount, unit, direction)

    @staticmethod
    def parse_relative_time(text: str) -> dict | None:
        for pattern, direction in (
            (DateTimeExtractor._FUTURE_RE, "future"),
            (DateTimeExtractor._PAST_RE,   "past"),
        ):
            m = pattern.search(text)
            if m:
                amount = int(m.group("amount"))
                unit   = DateTimeExtractor.get_unit_type(m.group("unit"))
                if unit:
                    return {
                        "amount":        amount,
                        "unit":          unit,
                        "direction":     direction,
                        "original_text": m.group(0),
                    }
        return None

    @staticmethod
    def _parse_clock(message: str) -> tuple[int, int] | None:
        m = DateTimeExtractor._CLOCK_RE.search(message)
        if not m:
            m24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", message)
            if m24:
                return int(m24.group(1)), int(m24.group(2))
            return None

        hour = int(m.group(1))
        minute = int(m.group(2)) if m.group(2) else 0
        ampm = m.group(3)

        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
        else:
            if 1 <= hour <= 5:
                hour += 12

        return hour, minute

    @staticmethod
    def extract_date_from_message(message: str) -> dict:
        today = datetime.now().date()
        now = datetime.now()
        ml = message.lower()

        def _with_time(d, default_dt: datetime) -> str:
            clock = DateTimeExtractor._parse_clock(message)
            if clock:
                hour, minute = clock
                dt = datetime(d.year, d.month, d.day, hour, minute, 0)
                return dt.isoformat()
            return d.strftime("%Y-%m-%d")

        rel = DateTimeExtractor.parse_relative_time(message)
        if rel:
            r = DateTimeExtractor._apply_offset(rel["amount"], rel["unit"], rel["direction"])
            if r["datetime"]:
                return {"deadline": r["datetime"], "type": "relative_time"}

        if re.search(r"\b(last week|pichle hafte|पिछले हफ्ते)\b", ml, re.IGNORECASE):
            d = today - timedelta(days=7)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "week"}

        if re.search(r"\b(last month|pichle mahine|पिछले महीने)\b", ml, re.IGNORECASE):
            d = today - relativedelta(months=1)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "month"}

        if re.search(r"\b(last year|pichle saal|पिछले साल)\b", ml, re.IGNORECASE):
            d = today - relativedelta(years=1)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "year"}

        if re.search(r"\b(this week|is hafte|इस हफ्ते)\b", ml, re.IGNORECASE):
            d = today - timedelta(days=today.weekday())
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "week"}

        if re.search(r"\b(this month|is mahine|इस महीने)\b", ml, re.IGNORECASE):
            d = today.replace(day=1)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "month"}

        if re.search(r"\b(this year|is saal|इस साल)\b", ml, re.IGNORECASE):
            d = today.replace(month=1, day=1)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "year"}

        if re.search(r"\b(next week|agale hafte|अगले हफ्ते)\b", ml, re.IGNORECASE):
            d = today + timedelta(days=7)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "week"}

        if re.search(r"\b(next month|agale mahine|अगले महीने)\b", ml, re.IGNORECASE):
            d = today + relativedelta(months=1)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "month"}

        if re.search(r"\b(next year|agale saal|अगले साल)\b", ml, re.IGNORECASE):
            d = today + relativedelta(years=1)
            return {"deadline": d.strftime("%Y-%m-%d"), "type": "year"}

        if re.search(r"\b(aaj|today|आज|aaj ke|aaj hi|आज ही)\b", ml, re.IGNORECASE | re.UNICODE):
            return {"deadline": _with_time(today, now), "type": "relative"}

        if re.search(r"\b(parso|day after tomorrow|परसों|parso ke|परसों को)\b", ml, re.IGNORECASE | re.UNICODE):
            d = today + timedelta(days=2)
            return {"deadline": _with_time(d, now + timedelta(days=2)), "type": "relative"}

        if re.search(r"\b(parson|day before yesterday|ना परसों)\b", ml, re.IGNORECASE | re.UNICODE):
            d = today - timedelta(days=2)
            return {"deadline": _with_time(d, now - timedelta(days=2)), "type": "relative"}

        if re.search(r"\b(yesterday|pichle kal|बीता हुआ कल)\b", ml, re.IGNORECASE | re.UNICODE):
            d = today - timedelta(days=1)
            return {"deadline": _with_time(d, now - timedelta(days=1)), "type": "relative"}

        if re.search(r"\b(kal|tomorrow|कल|kal ke|कल को)\b", ml, re.IGNORECASE | re.UNICODE):
            past_markers = re.search(
                r"\b(pehle|pahle|पहले|ago|yesterday|kal pehle|beet gaya)\b",
                ml, re.IGNORECASE | re.UNICODE,
            )
            offset = -1 if past_markers else 1
            d = today + timedelta(days=offset)
            return {"deadline": _with_time(d, now + timedelta(days=offset)), "type": "relative"}

        m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", message)
        if m:
            day, month, year = m.groups()
            try:
                d = datetime(int(year), int(month), int(day)).date()
                return {"deadline": _with_time(d, datetime(int(year), int(month), int(day))), "type": "specific"}
            except ValueError:
                pass

        m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", message)
        if m:
            year, month, day = m.groups()
            try:
                d = datetime(int(year), int(month), int(day)).date()
                return {"deadline": _with_time(d, datetime(int(year), int(month), int(day))), "type": "specific"}
            except ValueError:
                pass

        return {"deadline": None, "type": None}


# ─────────────────────────────────────────────────────────────
# DEPARTMENT CLASSIFIER
# ─────────────────────────────────────────────────────────────

# Keyword-based department detection (fast pre-filter before LLM)
DEPARTMENT_KEYWORDS = {
    "operations": [
        # English
        "warehouse", "dispatch", "delivery", "logistics", "shipment", "inventory",
        "stock", "loading", "unloading", "transport", "vehicle", "driver", "packing",
        "production", "manufacturing", "quality", "inspection", "shift", "machine",
        "equipment", "maintenance", "repair", "store", "godown", "khali",
        # Hinglish / Hindi
        "godam", "maal", "samaan", "bhejo", "bhej", "load", "unload",
        "gaadi", "truck", "tempo", "delivery karo", "pack", "packaging",
        "units", "khali kro", "khali karo", "safai", "clean", "cleaning",
    ],
    "sales": [
        # English
        "invoice", "order", "client", "customer", "quotation", "quote", "deal",
        "sales", "revenue", "payment", "collection", "follow up", "followup",
        "lead", "prospect", "visit", "meeting", "demo", "proposal",
        # Hinglish / Hindi
        "invoice banao", "bill banao", "order aaya", "customer ko",
        "client ko", "collection karo", "payment lao", "becho", "bechna",
        "bikri", "sale", "graahaak", "grahak",
    ],
    "purchase": [
        # English
        "purchase", "buy", "procure", "procurement", "vendor", "supplier",
        "order place", "raw material", "material", "sourcing", "price",
        "quotation from", "rate", "cost",
        # Hinglish / Hindi
        "kharido", "kharidna", "kharid", "mangao", "mangana",
        "order karo", "supplier se", "vendor se", "material lao",
        "saman mangao", "rate puchho", "rate pata karo", "khareedna",
    ],
    "it": [
        # English
        "server", "system", "computer", "laptop", "software", "hardware",
        "network", "internet", "wifi", "password", "login", "access",
        "email", "website", "app", "application", "database", "backup",
        "install", "update software", "bug", "error", "crash", "printer",
        # Hinglish / Hindi
        "computer theek karo", "laptop kharab", "internet nahi",
        "wifi nahi chal", "password reset", "software install",
        "system slow", "it team", "tech support",
    ],
}


def detect_department_by_keywords(message: str) -> str | None:
    """
    Fast keyword-based department detection.
    Returns department name or None if no match found.
    """
    ml = message.lower()
    scores = {dept: 0 for dept in DEPARTMENT_KEYWORDS}

    for dept, keywords in DEPARTMENT_KEYWORDS.items():
        for kw in keywords:
            if kw in ml:
                scores[dept] += 1

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best
    return None


# ─────────────────────────────────────────────────────────────
# PROFESSIONAL RESPONSE GENERATOR (Only for general_chat)
# ─────────────────────────────────────────────────────────────

def get_professional_response(message: str, date_info: dict = None) -> str:
    """
    Generate a professional, helpful response for general_chat intent in Hinglish.
    """
    message_lower = message.lower()

    attendance_keywords = [
        'present', 'absent', 'attendance', 'haazri', 'present hu', 'absent hu',
        'aa gaya', 'aaj aaya', 'nahi aa sakta', 'chutti chahiye'
    ]
    
    is_attendance = any(k in message_lower for k in attendance_keywords)
    
    if is_attendance:
        return (
            f"Attendance ke liye ye commands use karo:\n\n"
            f"• /present - Apne aap ko present mark karne ke liye\n"
            f"• /absent - Apne aap ko absent mark karne ke liye"
        )
    
    # Default response for general_chat
    return (
        f"Thank you for your message. Main task management aur team coordination mein help kar sakta hoon. "
        f"Saare available commands dekhne ke liye help type karo. Batao, main aapki kya help kar sakta hoon?"
    )


# ─────────────────────────────────────────────────────────────
# PURE INTENT CLASSIFIER
# ─────────────────────────────────────────────────────────────
class IntentClassifier:
    def __init__(self):
        print("✅ Intent Classifier ready.")
        self.datetime_extractor = DateTimeExtractor()

    # ── Person-mention patterns ────────────────────────────────
    _ASSIGN_PATTERNS = [
        re.compile(r"@(\w+)", re.IGNORECASE | re.UNICODE),
        re.compile(r"^([A-Za-z\u0900-\u097F]{2,20})\s+ko\b", re.IGNORECASE | re.UNICODE),
        re.compile(r"^([A-Za-z\u0900-\u097F]{2,20})\s+se\b", re.IGNORECASE | re.UNICODE),
    ]

    _NOT_A_NAME = {
        "ye", "yeh", "vo", "woh", "kal", "aaj", "ab", "tab", "kab",
        "kya", "koi", "kuch", "sab", "bas", "aur", "ya", "ki", "ka",
        "ko", "se", "ne", "mein", "par", "pe", "tak", "is", "us",
        "ek", "do", "teen", "char", "das", "sau", "main", "hum",
        "mera", "meri", "apna", "apni", "karo", "karna",
        "krdo", "krdena", "lena", "dena", "bhejo", "send", "please",
        "pls", "thoda", "jaldi", "abhi", "jab", "task", "kaam",
        "the", "this", "that", "some", "all", "please", "can", "get",
        "make", "take", "put", "set", "let", "sir", "hi", "hello",
        "ok", "okay", "sure", "yes", "no",
    }

    # ── Keywords that indicate the user is VIEWING their own tasks ──
    _VIEW_TASKS_PATTERNS = [
        r"\b(mera|mere|meri)\s+(kaam|task|tasks)\b",
        r"\b(my\s+tasks?|my\s+work)\b",
        r"\btask\s*(list|dikhao|show|dekh|kya\s+hai|kya\s+hain)\b",
        r"\b(kaam\s+dikhao|kaam\s+batao|kaam\s+kya\s+hai)\b",
        r"\b(pending\s+tasks?|kya\s+karna\s+hai|aaj\s+kya\s+karna\s+hai)\b",
        r"\b(show\s+tasks?|list\s+tasks?|view\s+tasks?)\b",
        r"\bkaam\s+dekh\b",
    ]

    @staticmethod
    def _is_view_tasks_request(message: str) -> bool:
        """Returns True only if the user is asking to VIEW their own tasks."""
        ml = message.lower().strip()
        for pattern in IntentClassifier._VIEW_TASKS_PATTERNS:
            if re.search(pattern, ml, re.IGNORECASE | re.UNICODE):
                return True
        return False

    @staticmethod
    def _extract_assignee(message: str) -> str | None:
        """Return the assignee slug if the message is directed at a specific person."""
        # Priority 1: explicit @mention
        at_m = re.search(r"@(\w+)", message)
        if at_m:
            return f"@{at_m.group(1)}"

        msg_lower = message.lower().strip()

        # Priority 2: "name ko ..." or "name se ..." pattern with work instruction
        # Any work-related message with a name qualifies now
        name_ko = re.match(
            r"^([A-Za-z\u0900-\u097F]{2,20})\s+ko\b",
            message, re.IGNORECASE | re.UNICODE
        )
        if name_ko and name_ko.group(1).lower() not in IntentClassifier._NOT_A_NAME:
            return name_ko.group(1)

        name_se = re.match(
            r"^([A-Za-z\u0900-\u097F]{2,20})\s+se\b",
            message, re.IGNORECASE | re.UNICODE
        )
        if name_se and name_se.group(1).lower() not in IntentClassifier._NOT_A_NAME:
            return name_se.group(1)

        # Priority 3: name anywhere mid-sentence with "ko" followed by a verb
        mid_ko = re.search(
            r"\b([A-Za-z\u0900-\u097F]{2,20})\s+ko\s+\w",
            message, re.IGNORECASE | re.UNICODE
        )
        if mid_ko and mid_ko.group(1).lower() not in IntentClassifier._NOT_A_NAME:
            return mid_ko.group(1)

        return None

    def _classify_department_via_llm(self, message: str) -> str:
        """
        Ask the LLM to pick the best department for a work instruction
        that has no named assignee.
        Returns one of: operations, sales, purchase, it
        """
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a department classifier for a factory/business WhatsApp bot. "
                        "Given a work instruction in English, Hindi, or Hinglish, classify it into "
                        "exactly ONE of these departments: operations, sales, purchase, it\n\n"
                        "Department definitions:\n"
                        "- operations: warehouse, dispatch, delivery, logistics, inventory, stock, "
                        "loading/unloading, transport, production, manufacturing, machine maintenance, "
                        "cleaning, packaging, godown/store management\n"
                        "- sales: invoices, orders, customer/client handling, payment collection, "
                        "quotations, leads, sales targets, billing\n"
                        "- purchase: buying raw materials, procurement, vendor/supplier management, "
                        "price comparisons, sourcing, material orders\n"
                        "- it: computers, laptops, servers, software, network/internet, passwords, "
                        "printers, applications, tech support\n\n"
                        "Respond with ONLY one word (the department name). No explanation."
                    ),
                },
                {"role": "user", "content": message},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        dept = response.choices[0].message.content.strip().lower()
        valid = {"operations", "sales", "purchase", "it"}
        return dept if dept in valid else "operations"  # default fallback

    def classify(self, message: str) -> dict:
        """
        Classify intent using a layered approach:

        Layer 1 — Deterministic Python pre-filters:
          a) View tasks request → /tasks
          b) Task + assignee pattern (task X to Y) → /mgrassign
          c) Any @mention or name with work → /assign (with worker_slug)
          d) Attendance words → /present / /absent
          e) Past-tense completion → /complete
          f) Work instruction with NO person → /assign (with depart_slug)

        Layer 2 — LLM for everything remaining.
        """
        datetime_info = self.datetime_extractor.extract_date_from_message(message)
        ml = message.lower()

        def _build(intent, id_=None, worker_slug=None, depart_slug=None, message_text=None):
            return {
                "intent": intent,
                "id": id_,
                "worker_slug": worker_slug,
                "depart_slug": depart_slug,
                "deadline": datetime_info.get("deadline"),
                "message": message_text,
            }

        # ── PRE-FILTER 0: /tasks — view-only ─────────────────────────────────
        if self._is_view_tasks_request(message):
            return _build("/tasks")

        # ─────────────────────────────────────────────────────────────────────
        # TASK-REFERENCE DETECTION
        # A "task reference" means the message explicitly talks about a specific
        # task (by number, word, or ID keyword).  This is the key signal that
        # separates /mgrassign (person + task ref) from /assign (person + work).
        #
        # Matches:
        #   "task 4", "task id 4", "id 4", "4 number wala task",
        #   "#4", "task no 4", "task number 4", "4 wala task"
        # ─────────────────────────────────────────────────────────────────────
        _TASK_REF_PATTERNS = [
            r"\btask\s*(id\s*)?\d+",          # "task 4", "task id 4"
            r"\bid\s*\d+",                     # "id 4", "id4"
            r"\b\d+\s*(number\s*)?wala\s*task",# "4 wala task", "4 number wala task"
            r"\btask\s*(no|number|#)\s*\d+",   # "task no 4", "task #4"
            r"#\d+",                           # "#4"
            r"\b\d+\s*wala\s*(kaam|task|number)", # "4 wala kaam" (referring to task)
        ]

        def _has_task_reference(text: str) -> tuple[bool, int | None]:
            """
            Returns (True, task_id) if a task reference is found, else (False, None).
            task_id is the extracted integer if present, else None.
            """
            tl = text.lower()
            for pat in _TASK_REF_PATTERNS:
                m = re.search(pat, tl, re.IGNORECASE | re.UNICODE)
                if m:
                    # Try to extract the number from the matched span
                    num = re.search(r"\d+", m.group(0))
                    return True, (int(num.group()) if num else None)
            return False, None

        has_task_ref, task_ref_id = _has_task_reference(message)

        # Also detect the old "task\s+\d+" pattern used in pre-filter A
        task_id_match = re.search(r"task\s+(\d+)|(\d+)\s+task", ml)

        # ── PRE-FILTER A: Manager assigns a task (by number) to a named person ─
        # Triggers when: task reference present + person named + assignment verb
        # "@ajay id 4 wala kaam pura kardo" → /mgrassign (id:4, worker_slug:@ajay)
        # "task 32 ajay ko do"              → /mgrassign (id:32, worker_slug:ajay)
        assign_keywords = [
            r"ko\s+do", r"ko\s+de", r"ko\s+bhej", r"assign", r"allot",
            r"de\s+do", r"bhej\s+do", r"pura\s+kar", r"kar\s+do",
            r"khatam\s+kar", r"complete\s+kar", r"finish\s+kar",
        ]
        is_mgr_assign_verb = any(re.search(kw, ml) for kw in assign_keywords)

        if has_task_ref:
            # Resolve the task ID — prefer explicit number, fall back to task_id_match
            tid = task_ref_id
            if tid is None and task_id_match:
                tid = int(task_id_match.group(1) or task_id_match.group(2))

            # Named person present → /mgrassign
            at_m = re.search(r"@(\w+)", message)
            if at_m:
                return _build("/mgrassign", tid, f"@{at_m.group(1)}")

            name_match = re.search(
                r"([A-Za-z\u0900-\u097F]{2,20})\s+ko\b", message, re.UNICODE
            )
            if name_match and name_match.group(1).lower() not in self._NOT_A_NAME:
                return _build("/mgrassign", tid, name_match.group(1))

            # Old-style "task X + assign verb + name" without @
            if task_id_match and is_mgr_assign_verb:
                name_m2 = re.search(
                    r"([A-Za-z\u0900-\u097F]{2,20})\b", message, re.UNICODE
                )
                if name_m2 and name_m2.group(1).lower() not in self._NOT_A_NAME:
                    return _build("/mgrassign", tid, name_m2.group(1))

        # ── PRE-FILTER B: Self-assign — with OR without a task # ─────────────
        # Covers: "task 32 main karunga", "ye kaam mai khud karunga",
        #         "main ye kar lunga", "I will do this", "mai khud dunga"
        _SELF_PATTERNS = [
            r"\b(main|mai|mein|me)\s+(karunga|kar\s+lunga|kar\s+leta\s+hu|karunga|kar\s+dunga|khud\s+karunga)\b",
            r"\bkhud\s+(karunga|kar\s+lunga|kar\s+leta|karega|dunga|karunga)\b",
            r"\b(i\s+will\s+do|i\s+will\s+take|i['']ll\s+do|i\s+will\s+handle|myself)\b",
            r"\b(main|mai)\s+khud\b",
            r"\bkhud\s+(main|mai|mein)\b",
            r"\bapne\s+aap\s+(karunga|kar\s+lunga|se\s+kar)\b",
            r"\b(le\s+leta\s+hu|le\s+lunga|kar\s+lunga|nipta\s+lunga|sambhal\s+lunga)\b",
        ]
        is_self_assign = any(re.search(p, ml, re.IGNORECASE | re.UNICODE) for p in _SELF_PATTERNS)

        if is_self_assign:
            tid = task_ref_id
            if tid is None and task_id_match:
                tid = int(task_id_match.group(1) or task_id_match.group(2))
            if tid is None:
                bare_id = re.search(r"\b(\d+)\b", message)
                if bare_id:
                    tid = int(bare_id.group(1))
            return _build("/mgrassign", tid, "self")

        # ── PRE-FILTER C: @mention + NO task reference → /assign ─────────────
        # "@ajay warehouse khali karo"  → /assign  (work, no task number)
        # "@ajay id 4 wala karo"        → already caught above as /mgrassign
        at_m = re.search(r"@(\w+)", message)
        if at_m:
            # Double-check: if somehow a task ref slipped through, send to /mgrassign
            if has_task_ref:
                return _build("/mgrassign", task_ref_id, f"@{at_m.group(1)}")
            return _build("/assign", worker_slug=f"@{at_m.group(1)}")

        # ── PRE-FILTER D: Named person + NO task reference → /assign ──────────
        # "ajay ko invoice bhejdo"  → /assign
        # "ajay ko task 5 do"       → already caught above as /mgrassign
        assignee = self._extract_assignee(message)
        if assignee:
            if has_task_ref:
                return _build("/mgrassign", task_ref_id, assignee)
            return _build("/assign", worker_slug=assignee)

        # ── PRE-FILTER E0: Self-claim ("I will do this myself") → /selfassign ──
        # Handles: "ye kaam mai khud karunga", "main karunga", "I will do it", etc.
        # NOTE: If a specific task ID is also present, PRE-FILTER B above already
        #       handles it as /mgrassign with worker_slug="self". This filter catches
        #       the case where NO task number is mentioned.
        _SELF_CLAIM_PATTERNS = [
            r"\b(main|mai|mein|i)\s+(karunga|karungi|kar\s+leta|kar\s+leti|kar\s+lunga|kar\s+lungi|karunga|karungi)\b",
            r"\b(khud\s+karunga|khud\s+karungi|khud\s+kar\s+leta|khud\s+kar\s+leti)\b",
            r"\b(main|mai)\s+khud\b",
            r"\bkhud\s+(main|mai|me)\b",
            r"\bi\s+will\s+(do|handle|take\s+care|manage)\b",
            r"\bi'?ll\s+(do|handle|take\s+care|manage)\b",
            r"\bmyself\s+(karunga|karungi|kar\s+leta|kar\s+lunga)\b",
            r"\b(le\s+leta|le\s+lunga|le\s+lungi)\b",  # "main le leta hu"
        ]
        is_self_claim = any(
            re.search(p, ml, re.IGNORECASE | re.UNICODE)
            for p in _SELF_CLAIM_PATTERNS
        )
        # Make sure there's no task number (those go
        if re.search(
            r"\b(present\s+hu|aa\s+gaya|aaya\s+hu|pahunch\s+gaya|aaj\s+aaya|i\s+am\s+here|mai\s+aa\s+gaya|main\s+aa\s+gaya)\b",
            ml, re.IGNORECASE | re.UNICODE,
        ):
            return _build("/present")

        if re.search(
            r"\b(absent\s+hu|nahi\s+aa\s+sakta|chutti\s+chahiye|chutti\s+le|leave\s+chahiye|aaj\s+nahi\s+aaunga|nahi\s+aa\s+pa|nahi\s+aaonga)\b",
            ml, re.IGNORECASE | re.UNICODE,
        ):
            return _build("/absent")

        # ── PRE-FILTER F: Past-tense completion ──────────────────────────────
        if re.search(
            r"\b(ho\s+gaya|kar\s+diya|khatam\s+ho\s+gaya|complete\s+ho\s+gaya|complete\s+kar\s+diya|khatam\s+kiya|done\s+hai|finished)\b",
            ml, re.IGNORECASE | re.UNICODE,
        ):
            id_m = re.search(r"\b(\d+)\b", message)
            return _build("/complete", int(id_m.group(1)) if id_m else None)

        # ── PRE-FILTER G: Work instruction with NO person → /assign + depart_slug
        # Detect whether the message sounds like a work instruction at all
        work_instruction_patterns = [
            r"\b(bhejo|bhej|karo|karna|krdo|krdena|banao|banana|lao|lana|chalao|chalana|"
            r"safai|clean|clear|pack|load|unload|dispatch|deliver|send|purchase|buy|"
            r"kharido|mangao|install|fix|check|repair|khali)\b",
            r"\b(units?|maal|samaan|invoice|order|shipment|warehouse|godown|machine|"
            r"computer|laptop|server|material|stock)\b",
        ]
        is_work_instruction = any(
            re.search(p, ml, re.IGNORECASE | re.UNICODE)
            for p in work_instruction_patterns
        )

        if is_work_instruction:
            # Try fast keyword detection first
            dept = detect_department_by_keywords(message)
            if dept is None:
                # Fall back to LLM department classification
                dept = self._classify_department_via_llm(message)
            return _build("/depart_assign", depart_slug=dept)

        # ── LLM: handle everything remaining ─────────────────────────────────
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": self._build_system_prompt()},
                {"role": "user",   "content": message},
            ],
            temperature=0.1,
            max_tokens=150,
            response_format={"type": "json_object"},
        )

        raw_reply = response.choices[0].message.content.strip()
        result = self._parse_decision(raw_reply)

        intent = result.get("intent", "general_chat")
        result["deadline"] = datetime_info.get("deadline")
        result.setdefault("depart_slug", None)

        # Message ONLY for general_chat intent
        if intent == "general_chat":
            result["message"] = get_professional_response(message, datetime_info)
        else:
            result["message"] = None

        # If LLM returned /assign with no person → upgrade to /depart_assign with dept
        if intent == "/assign" and not result.get("worker_slug"):
            dept = detect_department_by_keywords(message)
            if dept is None:
                dept = self._classify_department_via_llm(message)
            result["intent"] = "/depart_assign"
            result["depart_slug"] = dept

        # If LLM returned /depart_assign, ensure depart_slug is set
        if intent == "/depart_assign" and not result.get("depart_slug"):
            dept = detect_department_by_keywords(message)
            if dept is None:
                dept = self._classify_department_via_llm(message)
            result["depart_slug"] = dept

        return result

    def _build_system_prompt(self) -> str:
        return """You are a pure intent classification system for a WhatsApp-based worker assistant called Munshi Dada.
Your ONLY job is to classify the user's message into exactly one intent and extract relevant IDs.
Respond with ONLY a valid JSON object. No text, no markdown, no explanations.

════════════════════════════════════════════════════════
CRITICAL RULES
════════════════════════════════════════════════════════

1. /tasks is ONLY for viewing your own task list. NOT for work instructions.
   ✅ "/tasks" triggers: "mera kaam dikhao", "my tasks", "task list", "kya karna hai"
   ❌ "/tasks" does NOT trigger for: "warehouse khali karo", "invoice bhejo", "500 units send karo"

2. /assign is ONLY when a person is named AND there is NO explicit task reference.
   - "@ajay warehouse khali karo" → /assign  (work instruction, no task number)
   - "rahul ko invoice bhejdo"   → /assign  (work instruction, no task number)

3. /mgrassign is when a person is named AND there IS an explicit task reference
   (task number, "id X", "#X", "task id X", "X wala task"), OR self-claim.
   - "@ajay id 4 wala kaam karo"  → /mgrassign  (task ref present)
   - "task 32 ajay ko do"         → /mgrassign  (task number present)
   - "@rahul #7 complete karo"    → /mgrassign  (task ref present)
   - "ye kaam mai khud karunga"   → /mgrassign  (self-claim)
   RULE: /assign and /mgrassign are mutually exclusive on task reference presence.

════════════════════════════════════════════════════════
INTENT CLASSIFICATION RULES
════════════════════════════════════════════════════════

1. "/tasks" — ONLY "view my tasks" requests
   Examples: "mera kaam dikhao", "my tasks", "task list", "pending tasks", "kya karna hai"

2. "/assign" — Work directed at a NAMED person, but NO specific task reference
   The message mentions a person AND a piece of work (not a specific task number/id).
   Examples:
     "@ajay warehouse khali karo"          → /assign (worker_slug: @ajay)
     "rahul ko invoice bhejdo"             → /assign (worker_slug: rahul)
     "@priya client ko call karo"          → /assign (worker_slug: @priya)
   → Always set worker_slug. depart_slug must be null.
   → KEY: No task ID / task number / "id X" / "#X" in the message.

3. "/depart_assign" — Work instruction with NO named person; route to a department
   Examples: "warehouse khali karo", "500 units bhejdo", "invoice banao", "purchase karo",
             "server theek karo", "material order karo"
   → Always set depart_slug to one of: operations, sales, purchase, it
   → worker_slug must be null

4. "/mgrassign" — Person named AND an explicit task reference present (task id/number),
   OR self-claiming work.
   TASK REFERENCE means: a specific task number, "task X", "id X", "#X",
   "X wala task", "task id X", "task no X", "X number wala task".

   With task reference + named person:
     "@ajay id 4 wala kaam pura kardo"    → /mgrassign (id:4,  worker_slug:@ajay)
     "@ajay task id 4 wala kaam karo"     → /mgrassign (id:4,  worker_slug:@ajay)
     "task 32 ajay ko do"                 → /mgrassign (id:32, worker_slug:ajay)
     "task 45 @rahul ko assign karo"      → /mgrassign (id:45, worker_slug:@rahul)
     "@rahul #7 complete karo"            → /mgrassign (id:7,  worker_slug:@rahul)

   Self-claim (with or without task number):
     "task 32 main karunga"               → /mgrassign (id:32, worker_slug:self)
     "ye kaam mai khud karunga"           → /mgrassign (id:null, worker_slug:self)

   → KEY DISTINCTION from /assign: /mgrassign ALWAYS has either a task reference
     OR worker_slug="self". Plain work instructions to a person = /assign.

5. "/update" — Updating a task with comment/status

6. "/issue" — Reporting a new issue
   Examples: "issue hai", "machine kharab", "kuch kharab hai"

7. "/issues" — View all active issues

8. "/resolve" — Marking an issue as resolved

9. "/members" — View team members

10. "/report" — Generate a report

11. "/help" — Need help with commands

12. "general_chat" — ONLY pure conversation: greetings, small talk, non-work
    Examples: "hello", "hi", "kaise ho", "good morning", "shukriya"

════════════════════════════════════════════════════════
OUTPUT FORMAT
════════════════════════════════════════════════════════
{"intent": "<intent_name>", "id": <int or null>, "worker_slug": "<@username, name, self, or null>", "depart_slug": "<operations|sales|purchase|it|null>"}

Rules:
- /assign      → worker_slug set, depart_slug null
- /depart_assign → depart_slug set, worker_slug null
- All other intents → both null
"""

    def _parse_decision(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except Exception:
            clean = re.sub(r"```json|```", "", raw).strip()
            try:
                return json.loads(clean)
            except Exception:
                return {"intent": "general_chat", "id": None, "worker_slug": None, "depart_slug": None}


# ─────────────────────────────────────────────────────────────
# COMMAND PARSER
# ─────────────────────────────────────────────────────────────
class CommandParser:
    def __init__(self):
        self.datetime_extractor = DateTimeExtractor()

    def parse(self, message: str) -> dict | None:
        message = message.strip()
        ml = message.lower()

        datetime_info = self.datetime_extractor.extract_date_from_message(message)

        def base(intent, id_=None, worker_slug=None, depart_slug=None):
            return {
                "intent": intent,
                "id": id_,
                "worker_slug": worker_slug,
                "depart_slug": depart_slug,
                "deadline": datetime_info.get("deadline"),
                "message": None,
            }

        def extract_leading_int(text: str):
            m = re.search(r"^\d+", text.strip())
            return int(m.group()) if m else None

        # Slash commands
        if ml.startswith("/issues"):
            return base("/issues")
        if ml.startswith("/issue"):
            return base("/issue", extract_leading_int(message[6:]))
        if ml.startswith("/present"):
            return base("/present")
        if ml.startswith("/absent"):
            return base("/absent")
        if ml.startswith("/tasks"):
            return base("/tasks")
        if ml.startswith("/complete"):
            return base("/complete", extract_leading_int(message[9:]))
        if ml.startswith("/assign"):
            rest = message[7:].strip()
            m = re.search(r"@(\d+)", rest)
            if m:
                return base("/assign", None, f"@{m.group(1)}")
            m = re.search(r"(\d{10})", rest)
            if m:
                return base("/assign", None, m.group(1))
            m = re.search(r"@(\w+)", rest)
            if m:
                return base("/assign", None, f"@{m.group(1)}")
            return base("/assign")
        if ml.startswith("/mgrassign"):
            rest = message[10:].strip()
            task_match = re.search(r"(\d+)", rest)
            assignee_match = re.search(r"@(\w+)", rest)
            if task_match and assignee_match:
                return base("/mgrassign", int(task_match.group(1)), f"@{assignee_match.group(1)}")
            elif task_match:
                return base("/mgrassign", int(task_match.group(1)), None)
            return base("/mgrassign")
        if ml.startswith("/update"):
            return base("/update", extract_leading_int(message[7:]))
        if ml.startswith("/resolve"):
            return base("/resolve", extract_leading_int(message[8:]))
        if ml.startswith("/members"):
            return base("/members")
        if ml.startswith("/report"):
            return base("/report")
        if ml.startswith("/help"):
            return base("/help")

        return None