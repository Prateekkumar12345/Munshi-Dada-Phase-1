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
No database, no worker_id, just intent classification with date & time extraction
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
# DATE & TIME UTILITY FUNCTIONS
# ─────────────────────────────────────────────────────────────
class DateTimeExtractor:

    # Flat word → canonical unit lookup.
    # Exact match only — avoids the substring false-positive bug in the old
    # UNIT_MAPPINGS + any(word in unit_text_lower …) approach.
    WORD_TO_UNIT = {
        # ── seconds ──────────────────────────────────────────
        "second": "seconds", "seconds": "seconds", "sec": "seconds", "secs": "seconds",
        "सेकंड": "seconds", "सेकेंड": "seconds",
        # ── minutes ──────────────────────────────────────────
        "minute": "minutes", "minutes": "minutes", "min": "minutes", "mins": "minutes",
        "मिनट": "minutes", "मिनटों": "minutes",
        # ── hours ────────────────────────────────────────────
        "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours", "h": "hours",
        "ghanta": "hours", "ghante": "hours", "घंटा": "hours", "घंटे": "hours",
        # ── days ─────────────────────────────────────────────
        "day": "days", "days": "days", "d": "days",
        "din": "days", "दिन": "days", "दिनों": "days",
        # ── weeks ────────────────────────────────────────────
        "week": "weeks", "weeks": "weeks", "wk": "weeks", "wks": "weeks",
        "hafte": "weeks", "hafta": "weeks", "हफ्ता": "weeks", "हफ्ते": "weeks",
        "सप्ताह": "weeks",
        # ── months ───────────────────────────────────────────
        "month": "months", "months": "months", "mon": "months", "mons": "months",
        "mahina": "months", "mahine": "months", "महीना": "months", "महीने": "months",
        # ── years ────────────────────────────────────────────
        "year": "years", "years": "years", "yr": "years", "yrs": "years", "y": "years",
        "saal": "years", "साल": "years", "वर्ष": "years",
    }

    # ── compiled regexes ─────────────────────────────────────────────────────
    # Unit alternatives are longest-first to prevent short tokens shadowing longer ones.
    _UNIT_RE = (
        r"(?P<unit>"
        r"seconds?|secs?|sec"
        r"|minutes?|mins?|min"
        r"|hours?|hrs?"            # English – longer first
        r"|ghante|ghanta"          # Hinglish
        r"|weeks?|wks?|wk"
        r"|hafte|hafta"            # Hinglish
        r"|months?|mons?"
        r"|mahine|mahina"          # Hinglish
        r"|years?|yrs?"
        r"|saal"                   # Hinglish
        r"|days?"
        r"|din"                    # Hinglish
        r"|घंटे|घंटा|मिनट|सेकंड|सेकेंड"    # Hindi
        r"|दिन|दिनों|हफ्ता|हफ्ते|सप्ताह"
        r"|महीना|महीने|साल|वर्ष"
        r")"
    )

    # Future:  "3 din baad", "2 hours later", "in 5 minutes", "after 1 week"
    _FUTURE_RE = re.compile(
        r"(?:in|after)?\s*(?P<amount>\d+)\s*"
        + _UNIT_RE
        + r"(?:\s*(?:ke\s*)?(?:baad|mein|में|बाद|after|later|from\s*now))",
        re.IGNORECASE | re.UNICODE,
    )

    # Past:  "3 din pehle", "2 hours ago", "1 mahine pehle"
    _PAST_RE = re.compile(
        r"(?P<amount>\d+)\s*"
        + _UNIT_RE
        + r"(?:\s*(?:pehle|pahle|पहले|before|ago))",
        re.IGNORECASE | re.UNICODE,
    )

    # ── helpers ──────────────────────────────────────────────────────────────
    @staticmethod
    def get_unit_type(unit_text: str) -> str:
        """Resolve a unit surface form to its canonical name via exact lookup."""
        # Try lowercase first (covers all English + Hinglish romanised forms),
        # then try the original casing (covers Devanagari).
        return (
            DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip().lower())
            or DateTimeExtractor.WORD_TO_UNIT.get(unit_text.strip())
        )

    @staticmethod
    def _apply_offset(amount: int, unit: str, direction: str) -> dict:
        """Return ISO datetime + date/time strings for the requested offset."""
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
            return {"datetime": None, "date_only": None, "time_only": None}

        target = now + delta
        return {
            "datetime":  target.isoformat(),
            "date_only": target.strftime("%Y-%m-%d"),
            "time_only": target.strftime("%H:%M:%S"),
        }

    # kept for backward-compatibility (was called directly in the old code)
    @staticmethod
    def calculate_datetime_from_offset(amount: int, unit: str, direction: str) -> dict:
        return DateTimeExtractor._apply_offset(amount, unit, direction)

    # ── public API ────────────────────────────────────────────────────────────
    @staticmethod
    def parse_relative_time(text: str) -> dict | None:
        """
        Try to match a relative-time expression anywhere in *text*.
        Returns a normalised dict or None.

        Replaces the old hand-rolled list of 30+ patterns with two compiled
        regexes that cover English, Hindi, and Hinglish in one pass each.
        """
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
    def extract_date_from_message(message: str) -> dict:
        """
        Extract date/time information from a natural-language message.

        Priority order:
          1. Relative offset    — "3 din baad", "2 hours ago", "in 5 minutes"
          2. Named fixed ranges — "this week", "next month", "last year", etc.
          3. Named days         — "aaj", "kal", "parso", "parson", "yesterday"
          4. Explicit date      — DD/MM/YYYY, DD-MM-YYYY, YYYY-MM-DD
        """
        today = datetime.now().date()
        now   = datetime.now()
        ml    = message.lower()

        # ── 1. Relative offset ───────────────────────────────────────────────
        rel = DateTimeExtractor.parse_relative_time(message)
        if rel:
            r = DateTimeExtractor._apply_offset(rel["amount"], rel["unit"], rel["direction"])
            if r["datetime"]:
                return {
                    "date":          r["date_only"],
                    "datetime":      r["datetime"],
                    "time":          r["time_only"],
                    "original_text": rel["original_text"],
                    "type":          "relative_time",
                    "unit":          rel["unit"],
                    "amount":        rel["amount"],
                    "direction":     rel["direction"],
                }

        # ── 2. Named fixed ranges ────────────────────────────────────────────
        # Last week / month / year
        if re.search(r"\b(last week|pichle hafte|पिछले हफ्ते)\b", ml, re.IGNORECASE):
            d = today - timedelta(days=7)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "last week", "type": "week"}

        if re.search(r"\b(last month|pichle mahine|पिछले महीने)\b", ml, re.IGNORECASE):
            d = today - relativedelta(months=1)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "last month", "type": "month"}

        if re.search(r"\b(last year|pichle saal|पिछले साल)\b", ml, re.IGNORECASE):
            d = today - relativedelta(years=1)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "last year", "type": "year"}

        # This week / month / year
        if re.search(r"\b(this week|is hafte|इस हफ्ते)\b", ml, re.IGNORECASE):
            d = today - timedelta(days=today.weekday())
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "this week", "type": "week"}

        if re.search(r"\b(this month|is mahine|इस महीने)\b", ml, re.IGNORECASE):
            d = today.replace(day=1)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "this month", "type": "month"}

        if re.search(r"\b(this year|is saal|इस साल)\b", ml, re.IGNORECASE):
            d = today.replace(month=1, day=1)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "this year", "type": "year"}

        # Next week / month / year
        if re.search(r"\b(next week|agale hafte|अगले हफ्ते)\b", ml, re.IGNORECASE):
            d = today + timedelta(days=7)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "next week", "type": "week"}

        if re.search(r"\b(next month|agale mahine|अगले महीने)\b", ml, re.IGNORECASE):
            d = today + relativedelta(months=1)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "next month", "type": "month"}

        if re.search(r"\b(next year|agale saal|अगले साल)\b", ml, re.IGNORECASE):
            d = today + relativedelta(years=1)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": None, "time": None,
                    "original_text": "next year", "type": "year"}

        # ── 3. Named days ────────────────────────────────────────────────────
        # aaj / today / आज
        if re.search(r"\b(aaj|today|आज|aaj ke|aaj hi|आज ही)\b", ml, re.IGNORECASE | re.UNICODE):
            return {"date": today.strftime("%Y-%m-%d"), "datetime": now.isoformat(),
                    "time": None, "original_text": None, "type": "relative"}

        # parso / day after tomorrow / परसों  — check BEFORE kal to avoid overlap
        if re.search(r"\b(parso|day after tomorrow|परसों|parso ke|परसों को)\b", ml, re.IGNORECASE | re.UNICODE):
            d = today + timedelta(days=2)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=2)).isoformat(),
                    "time": None, "original_text": None, "type": "relative"}

        # parson / day before yesterday / ना परसों
        if re.search(r"\b(parson|day before yesterday|ना परसों)\b", ml, re.IGNORECASE | re.UNICODE):
            d = today - timedelta(days=2)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=2)).isoformat(),
                    "time": None, "original_text": None, "type": "relative"}

        # yesterday / pichle kal / बीता हुआ कल
        if re.search(r"\b(yesterday|pichle kal|बीता हुआ कल)\b", ml, re.IGNORECASE | re.UNICODE):
            d = today - timedelta(days=1)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": (now - timedelta(days=1)).isoformat(),
                    "time": None, "original_text": None, "type": "relative"}

        # kal / tomorrow / कल
        # Hindi "kal" is ambiguous (yesterday OR tomorrow).
        # Heuristic: if strong past-tense markers are present → yesterday, else → tomorrow.
        if re.search(r"\b(kal|tomorrow|कल|kal ke|कल को)\b", ml, re.IGNORECASE | re.UNICODE):
            past_markers = re.search(
                r"\b(pehle|pahle|पहले|ago|yesterday|kal pehle|beet gaya)\b",
                ml, re.IGNORECASE | re.UNICODE,
            )
            offset = -1 if past_markers else 1
            d = today + timedelta(days=offset)
            return {"date": d.strftime("%Y-%m-%d"), "datetime": (now + timedelta(days=offset)).isoformat(),
                    "time": None, "original_text": None, "type": "relative"}

        # ── 4. Explicit date literals ────────────────────────────────────────
        # DD/MM/YYYY or DD-MM-YYYY
        m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", message)
        if m:
            day, month, year = m.groups()
            try:
                specific_date = datetime(int(year), int(month), int(day))
                return {"date": specific_date.strftime("%Y-%m-%d"),
                        "datetime": specific_date.isoformat(), "time": None,
                        "original_text": m.group(0), "type": "specific"}
            except ValueError:
                pass

        # YYYY-MM-DD
        m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", message)
        if m:
            year, month, day = m.groups()
            try:
                specific_date = datetime(int(year), int(month), int(day))
                return {"date": specific_date.strftime("%Y-%m-%d"),
                        "datetime": specific_date.isoformat(), "time": None,
                        "original_text": m.group(0), "type": "specific"}
            except ValueError:
                pass

        return {"date": None, "datetime": None, "time": None, "original_text": None, "type": None}


# ─────────────────────────────────────────────────────────────
# PURE INTENT CLASSIFIER
# ─────────────────────────────────────────────────────────────
class IntentClassifier:
    def __init__(self):
        print("✅ Intent Classifier ready.")
        self.datetime_extractor = DateTimeExtractor()

    def classify(self, message: str) -> dict:
        """
        Classify the user's message into an intent and extract date/time.
        Returns intent, ID, and date/time information.
        """
        datetime_info = self.datetime_extractor.extract_date_from_message(message)

        system = self._build_system_prompt()

        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": message},
            ],
            temperature=0.2,
            max_tokens=200,
            response_format={"type": "json_object"},
        )

        raw_reply = response.choices[0].message.content.strip()
        result = self._parse_decision(raw_reply)

        # Attach date/time fields extracted locally (not via LLM)
        result["date"]               = datetime_info.get("date")
        result["datetime"]           = datetime_info.get("datetime")
        result["time"]               = datetime_info.get("time")
        result["date_original_text"] = datetime_info.get("original_text")

        return result

    def _build_system_prompt(self) -> str:
        return """You are a pure intent classification system with date/time extraction capability.
Your ONLY job is to classify the user's message into one intent and extract any relevant information.
Respond with ONLY a valid JSON object. Do not include any other text, markdown, or explanations.

=== INTENTS ===

1. "/present"    — Marking attendance as present
                   Keywords: present, aa gaya, aaya, pahunch gaya, main present hu, aaj aaya hu

2. "/absent"     — Marking attendance as absent
                   Keywords: absent, nahi aa sakta, chutti, leave, aaj nahi aaunga

3. "/tasks"      — View tasks
                   Keywords: tasks, kaam dikhao, task list, mera kaam, kya karna hai

4. "/complete"   — Marking a task as complete (extract task ID if given)
                   Keywords: complete, ho gaya, khatam, done, finished
                   Example: "complete 2"  →  id: 2

5. "/assign"     — Assigning a task to someone (extract @username or phone number)
                   Keywords: assign, @user, @all, de do, allocate

6. "/update"     — Updating a task with a comment / status (extract task ID if given)
                   Keywords: update, add comment, status update

7. "/issue"      — Reporting a new issue (extract issue ID if referenced)
                   Keywords: issue, problem, dikkat, not working, broken

8. "/issues"     — View all active issues
                   Keywords: issues, active issues, problems list

9. "/resolve"    — Resolving an issue (extract issue ID)
                   Keywords: resolve, fixed, solved, hatado, resolved hogya

10. "/members"   — View team members
                   Keywords: members, team, sab log

11. "/report"    — Generate a report / summary
                   Keywords: report, summary, report de do

12. "/help"      — Need help with available commands
                   Keywords: help, commands, kya karein

13. "general_chat" — General conversation / anything that doesn't match above

=== OUTPUT FORMAT ===
{"intent": "<intent_name>", "id": <id_value or null>}

Examples:
{"intent": "/present", "id": null}
{"intent": "/complete", "id": 2}
{"intent": "/assign", "id": "@8295466423"}
{"intent": "general_chat", "id": null}

Note: date/time fields are added separately by the system — do NOT include them.
"""

    def _parse_decision(self, raw: str) -> dict:
        try:
            return json.loads(raw)
        except Exception:
            clean = re.sub(r"```json|```", "", raw).strip()
            try:
                return json.loads(clean)
            except Exception:
                return {"intent": "general_chat", "id": None}


# ─────────────────────────────────────────────────────────────
# COMMAND PARSER
# ─────────────────────────────────────────────────────────────
class CommandParser:
    """Parse explicit slash commands without any database dependency."""

    def __init__(self):
        self.datetime_extractor = DateTimeExtractor()

    def parse(self, message: str) -> dict | None:
        """
        Parse a slash command and return an intent dict with extracted
        parameters and resolved date/time.  Returns None if the message is
        not a slash command.
        """
        message = message.strip()
        ml = message.lower()

        datetime_info = self.datetime_extractor.extract_date_from_message(message)

        def base(intent, id_=None):
            return {
                "intent":   intent,
                "id":       id_,
                "date":     datetime_info.get("date"),
                "datetime": datetime_info.get("datetime"),
            }

        def extract_leading_int(text: str):
            m = re.search(r"^\d+", text.strip())
            return int(m.group()) if m else None

        # /issues must be checked before /issue (longer prefix first)
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
            # @number
            m = re.search(r"@(\d+)", rest)
            if m:
                return base("/assign", f"@{m.group(1)}")
            # bare 10-digit phone
            m = re.search(r"(\d{10})", rest)
            if m:
                return base("/assign", m.group(1))
            # @username
            m = re.search(r"@(\w+)", rest)
            if m:
                return base("/assign", f"@{m.group(1)}")
            return base("/assign")

        if ml.startswith("/update"):
            return base("/update", extract_leading_int(message[7:]))

        if ml.startswith("/resolve"):
            return base("/resolve", extract_leading_int(message[8:]))

        if ml.startswith("/members"):
            return base("/members")

        if ml.startswith("/report"):
            return base("/report")

        if ml.startswith("/help"):
            return base("help")

        return None