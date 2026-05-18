# """
# bot_engine.py — Pure Intent Classifier for Worker Assistant
# No database, no worker_id, just intent classification with date extraction
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
# # DATE UTILITY FUNCTIONS
# # ─────────────────────────────────────────────────────────────
# class DateTimeExtractor:

#     WORD_TO_UNIT = {
#         "second": "seconds", "seconds": "seconds", "sec": "seconds", "secs": "seconds",
#         "सेकंड": "seconds", "सेकेंड": "seconds",
#         "minute": "minutes", "minutes": "minutes", "min": "minutes", "mins": "minutes",
#         "मिनट": "minutes", "मिनटों": "minutes",
#         "hour": "hours", "hours": "hours", "hr": "hours", "hrs": "hours", "h": "hours",
#         "ghanta": "hours", "ghante": "hours", "घंटा": "hours", "घंटे": "hours",
#         "day": "days", "days": "days", "d": "days",
#         "din": "days", "दिन": "days", "दिनों": "days",
#         "week": "weeks", "weeks": "weeks", "wk": "weeks", "wks": "weeks",
#         "hafte": "weeks", "hafta": "weeks", "हफ्ता": "weeks", "हफ्ते": "weeks",
#         "सप्ताह": "weeks",
#         "month": "months", "months": "months", "mon": "months", "mons": "months",
#         "mahina": "months", "mahine": "months", "महीना": "months", "महीने": "months",
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

#     _CLOCK_RE = re.compile(
#         r"(\d{1,2})(?::(\d{2}))?\s*(?:(am|pm)|(?:bje|baje|baj|बजे|बज))",
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
#     def _parse_clock(message: str) -> tuple[int, int] | None:
#         m = DateTimeExtractor._CLOCK_RE.search(message)
#         if not m:
#             m24 = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", message)
#             if m24:
#                 return int(m24.group(1)), int(m24.group(2))
#             return None

#         hour = int(m.group(1))
#         minute = int(m.group(2)) if m.group(2) else 0
#         ampm = m.group(3)

#         if ampm:
#             ampm = ampm.lower()
#             if ampm == "pm" and hour != 12:
#                 hour += 12
#             elif ampm == "am" and hour == 12:
#                 hour = 0
#         else:
#             if 1 <= hour <= 5:
#                 hour += 12

#         return hour, minute

#     @staticmethod
#     def extract_date_from_message(message: str) -> dict:
#         today = datetime.now().date()
#         now = datetime.now()
#         ml = message.lower()

#         def _with_time(d, default_dt: datetime) -> str:
#             clock = DateTimeExtractor._parse_clock(message)
#             if clock:
#                 hour, minute = clock
#                 dt = datetime(d.year, d.month, d.day, hour, minute, 0)
#                 return dt.isoformat()
#             return d.strftime("%Y-%m-%d")

#         rel = DateTimeExtractor.parse_relative_time(message)
#         if rel:
#             r = DateTimeExtractor._apply_offset(rel["amount"], rel["unit"], rel["direction"])
#             if r["datetime"]:
#                 return {"deadline": r["datetime"], "type": "relative_time"}

#         if re.search(r"\b(last week|pichle hafte|पिछले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=7)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "week"}

#         if re.search(r"\b(last month|pichle mahine|पिछले महीने)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(months=1)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "month"}

#         if re.search(r"\b(last year|pichle saal|पिछले साल)\b", ml, re.IGNORECASE):
#             d = today - relativedelta(years=1)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "year"}

#         if re.search(r"\b(this week|is hafte|इस हफ्ते)\b", ml, re.IGNORECASE):
#             d = today - timedelta(days=today.weekday())
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "week"}

#         if re.search(r"\b(this month|is mahine|इस महीने)\b", ml, re.IGNORECASE):
#             d = today.replace(day=1)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "month"}

#         if re.search(r"\b(this year|is saal|इस साल)\b", ml, re.IGNORECASE):
#             d = today.replace(month=1, day=1)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "year"}

#         if re.search(r"\b(next week|agale hafte|अगले हफ्ते)\b", ml, re.IGNORECASE):
#             d = today + timedelta(days=7)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "week"}

#         if re.search(r"\b(next month|agale mahine|अगले महीने)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(months=1)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "month"}

#         if re.search(r"\b(next year|agale saal|अगले साल)\b", ml, re.IGNORECASE):
#             d = today + relativedelta(years=1)
#             return {"deadline": d.strftime("%Y-%m-%d"), "type": "year"}

#         if re.search(r"\b(aaj|today|आज|aaj ke|aaj hi|आज ही)\b", ml, re.IGNORECASE | re.UNICODE):
#             return {"deadline": _with_time(today, now), "type": "relative"}

#         if re.search(r"\b(parso|day after tomorrow|परसों|parso ke|परसों को)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today + timedelta(days=2)
#             return {"deadline": _with_time(d, now + timedelta(days=2)), "type": "relative"}

#         if re.search(r"\b(parson|day before yesterday|ना परसों)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=2)
#             return {"deadline": _with_time(d, now - timedelta(days=2)), "type": "relative"}

#         if re.search(r"\b(yesterday|pichle kal|बीता हुआ कल)\b", ml, re.IGNORECASE | re.UNICODE):
#             d = today - timedelta(days=1)
#             return {"deadline": _with_time(d, now - timedelta(days=1)), "type": "relative"}

#         if re.search(r"\b(kal|tomorrow|कल|kal ke|कल को)\b", ml, re.IGNORECASE | re.UNICODE):
#             past_markers = re.search(
#                 r"\b(pehle|pahle|पहले|ago|yesterday|kal pehle|beet gaya)\b",
#                 ml, re.IGNORECASE | re.UNICODE,
#             )
#             offset = -1 if past_markers else 1
#             d = today + timedelta(days=offset)
#             return {"deadline": _with_time(d, now + timedelta(days=offset)), "type": "relative"}

#         m = re.search(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", message)
#         if m:
#             day, month, year = m.groups()
#             try:
#                 d = datetime(int(year), int(month), int(day)).date()
#                 return {"deadline": _with_time(d, datetime(int(year), int(month), int(day))), "type": "specific"}
#             except ValueError:
#                 pass

#         m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", message)
#         if m:
#             year, month, day = m.groups()
#             try:
#                 d = datetime(int(year), int(month), int(day)).date()
#                 return {"deadline": _with_time(d, datetime(int(year), int(month), int(day))), "type": "specific"}
#             except ValueError:
#                 pass

#         return {"deadline": None, "type": None}


# # ─────────────────────────────────────────────────────────────
# # DEPARTMENT CLASSIFIER
# # ─────────────────────────────────────────────────────────────

# # Keyword-based department detection (fast pre-filter before LLM)
# DEPARTMENT_KEYWORDS = {
#     "operations": [
#         # English
#         "warehouse", "dispatch", "delivery", "logistics", "shipment", "inventory",
#         "stock", "loading", "unloading", "transport", "vehicle", "driver", "packing",
#         "production", "manufacturing", "quality", "inspection", "shift", "machine",
#         "equipment", "maintenance", "repair", "store", "godown", "khali",
#         # Hinglish / Hindi
#         "godam", "maal", "samaan", "bhejo", "bhej", "load", "unload",
#         "gaadi", "truck", "tempo", "delivery karo", "pack", "packaging",
#         "units", "khali kro", "khali karo", "safai", "clean", "cleaning",
#     ],
#     "sales": [
#         # English
#         "invoice", "order", "client", "customer", "quotation", "quote", "deal",
#         "sales", "revenue", "payment", "collection", "follow up", "followup",
#         "lead", "prospect", "visit", "meeting", "demo", "proposal",
#         # Hinglish / Hindi
#         "invoice banao", "bill banao", "order aaya", "customer ko",
#         "client ko", "collection karo", "payment lao", "becho", "bechna",
#         "bikri", "sale", "graahaak", "grahak",
#     ],
#     "purchase": [
#         # English
#         "purchase", "buy", "procure", "procurement", "vendor", "supplier",
#         "order place", "raw material", "material", "sourcing", "price",
#         "quotation from", "rate", "cost",
#         # Hinglish / Hindi
#         "kharido", "kharidna", "kharid", "mangao", "mangana",
#         "order karo", "supplier se", "vendor se", "material lao",
#         "saman mangao", "rate puchho", "rate pata karo", "khareedna",
#     ],
#     "it": [
#         # English
#         "server", "system", "computer", "laptop", "software", "hardware",
#         "network", "internet", "wifi", "password", "login", "access",
#         "email", "website", "app", "application", "database", "backup",
#         "install", "update software", "bug", "error", "crash", "printer",
#         # Hinglish / Hindi
#         "computer theek karo", "laptop kharab", "internet nahi",
#         "wifi nahi chal", "password reset", "software install",
#         "system slow", "it team", "tech support",
#     ],
# }


# def detect_department_by_keywords(message: str) -> str | None:
#     """
#     Fast keyword-based department detection.
#     Returns department name or None if no match found.
#     """
#     ml = message.lower()
#     scores = {dept: 0 for dept in DEPARTMENT_KEYWORDS}

#     for dept, keywords in DEPARTMENT_KEYWORDS.items():
#         for kw in keywords:
#             if kw in ml:
#                 scores[dept] += 1

#     best = max(scores, key=scores.get)
#     if scores[best] > 0:
#         return best
#     return None


# # ─────────────────────────────────────────────────────────────
# # PROFESSIONAL RESPONSE GENERATOR (Only for general_chat)
# # ─────────────────────────────────────────────────────────────

# def get_professional_response(message: str, date_info: dict = None) -> str:
#     """
#     Generate a professional, helpful response for general_chat intent in Hinglish.
#     """
#     message_lower = message.lower()

#     attendance_keywords = [
#         'present', 'absent', 'attendance', 'haazri', 'present hu', 'absent hu',
#         'aa gaya', 'aaj aaya', 'nahi aa sakta', 'chutti chahiye'
#     ]
    
#     is_attendance = any(k in message_lower for k in attendance_keywords)
    
#     if is_attendance:
#         return (
#             f"Attendance ke liye ye commands use karo:\n\n"
#             f"• /present - Apne aap ko present mark karne ke liye\n"
#             f"• /absent - Apne aap ko absent mark karne ke liye"
#         )
    
#     # Default response for general_chat
#     return (
#         f"Thank you for your message. Main task management aur team coordination mein help kar sakta hoon. "
#         f"Saare available commands dekhne ke liye help type karo. Batao, main aapki kya help kar sakta hoon?"
#     )


# # ─────────────────────────────────────────────────────────────
# # PURE INTENT CLASSIFIER
# # ─────────────────────────────────────────────────────────────
# class IntentClassifier:
#     def __init__(self):
#         print("✅ Intent Classifier ready.")
#         self.datetime_extractor = DateTimeExtractor()

#     # ── Person-mention patterns ────────────────────────────────
#     _ASSIGN_PATTERNS = [
#         re.compile(r"@(\w+)", re.IGNORECASE | re.UNICODE),
#         re.compile(r"^([A-Za-z\u0900-\u097F]{2,20})\s+ko\b", re.IGNORECASE | re.UNICODE),
#         re.compile(r"^([A-Za-z\u0900-\u097F]{2,20})\s+se\b", re.IGNORECASE | re.UNICODE),
#     ]

#     _NOT_A_NAME = {
#         "ye", "yeh", "vo", "woh", "kal", "aaj", "ab", "tab", "kab",
#         "kya", "koi", "kuch", "sab", "bas", "aur", "ya", "ki", "ka",
#         "ko", "se", "ne", "mein", "par", "pe", "tak", "is", "us",
#         "ek", "do", "teen", "char", "das", "sau", "main", "hum",
#         "mera", "meri", "apna", "apni", "karo", "karna",
#         "krdo", "krdena", "lena", "dena", "bhejo", "send", "please",
#         "pls", "thoda", "jaldi", "abhi", "jab", "task", "kaam",
#         "the", "this", "that", "some", "all", "please", "can", "get",
#         "make", "take", "put", "set", "let", "sir", "hi", "hello",
#         "ok", "okay", "sure", "yes", "no",
#     }

#     # ── Keywords that indicate the user is VIEWING their own tasks ──
#     _VIEW_TASKS_PATTERNS = [
#         r"\b(mera|mere|meri)\s+(kaam|task|tasks)\b",
#         r"\b(my\s+tasks?|my\s+work)\b",
#         r"\btask\s*(list|dikhao|show|dekh|kya\s+hai|kya\s+hain)\b",
#         r"\b(kaam\s+dikhao|kaam\s+batao|kaam\s+kya\s+hai)\b",
#         r"\b(pending\s+tasks?|kya\s+karna\s+hai|aaj\s+kya\s+karna\s+hai)\b",
#         r"\b(show\s+tasks?|list\s+tasks?|view\s+tasks?)\b",
#         r"\bkaam\s+dekh\b",
#     ]

#     @staticmethod
#     def _is_view_tasks_request(message: str) -> bool:
#         """Returns True only if the user is asking to VIEW their own tasks."""
#         ml = message.lower().strip()
#         for pattern in IntentClassifier._VIEW_TASKS_PATTERNS:
#             if re.search(pattern, ml, re.IGNORECASE | re.UNICODE):
#                 return True
#         return False

#     @staticmethod
#     def _extract_assignee(message: str) -> str | None:
#         """Return the assignee slug if the message is directed at a specific person."""
#         # Priority 1: explicit @mention
#         at_m = re.search(r"@(\w+)", message)
#         if at_m:
#             return f"@{at_m.group(1)}"

#         msg_lower = message.lower().strip()

#         # Priority 2: "name ko ..." or "name se ..." pattern with work instruction
#         # Any work-related message with a name qualifies now
#         name_ko = re.match(
#             r"^([A-Za-z\u0900-\u097F]{2,20})\s+ko\b",
#             message, re.IGNORECASE | re.UNICODE
#         )
#         if name_ko and name_ko.group(1).lower() not in IntentClassifier._NOT_A_NAME:
#             return name_ko.group(1)

#         name_se = re.match(
#             r"^([A-Za-z\u0900-\u097F]{2,20})\s+se\b",
#             message, re.IGNORECASE | re.UNICODE
#         )
#         if name_se and name_se.group(1).lower() not in IntentClassifier._NOT_A_NAME:
#             return name_se.group(1)

#         # Priority 3: name anywhere mid-sentence with "ko" followed by a verb
#         mid_ko = re.search(
#             r"\b([A-Za-z\u0900-\u097F]{2,20})\s+ko\s+\w",
#             message, re.IGNORECASE | re.UNICODE
#         )
#         if mid_ko and mid_ko.group(1).lower() not in IntentClassifier._NOT_A_NAME:
#             return mid_ko.group(1)

#         return None

#     def _classify_department_via_llm(self, message: str) -> str:
#         """
#         Ask the LLM to pick the best department for a work instruction
#         that has no named assignee.
#         Returns one of: operations, sales, purchase, it
#         """
#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             messages=[
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a department classifier for a factory/business WhatsApp bot. "
#                         "Given a work instruction in English, Hindi, or Hinglish, classify it into "
#                         "exactly ONE of these departments: operations, sales, purchase, it\n\n"
#                         "Department definitions:\n"
#                         "- operations: warehouse, dispatch, delivery, logistics, inventory, stock, "
#                         "loading/unloading, transport, production, manufacturing, machine maintenance, "
#                         "cleaning, packaging, godown/store management\n"
#                         "- sales: invoices, orders, customer/client handling, payment collection, "
#                         "quotations, leads, sales targets, billing\n"
#                         "- purchase: buying raw materials, procurement, vendor/supplier management, "
#                         "price comparisons, sourcing, material orders\n"
#                         "- it: computers, laptops, servers, software, network/internet, passwords, "
#                         "printers, applications, tech support\n\n"
#                         "Respond with ONLY one word (the department name). No explanation."
#                     ),
#                 },
#                 {"role": "user", "content": message},
#             ],
#             temperature=0.0,
#             max_tokens=10,
#         )
#         dept = response.choices[0].message.content.strip().lower()
#         valid = {"operations", "sales", "purchase", "it"}
#         return dept if dept in valid else "operations"  # default fallback

#     def classify(self, message: str) -> dict:
#         """
#         Classify intent using a layered approach:

#         Layer 1 — Deterministic Python pre-filters:
#           a) View tasks request → /tasks
#           b) Task + assignee pattern (task X to Y) → /mgrassign or /mgrself
#           c) Any @mention or name with work → /assign (with worker_slug)
#           d) Attendance words → /present / /absent
#           e) Past-tense completion → /complete
#           f) Work instruction with NO person → /depart_assign

#         Layer 2 — LLM for everything remaining.
#         """
#         datetime_info = self.datetime_extractor.extract_date_from_message(message)
#         ml = message.lower()

#         def _build(intent, id_=None, worker_slug=None, depart_slug=None, message_text=None):
#             return {
#                 "intent": intent,
#                 "id": id_,
#                 "worker_slug": worker_slug,
#                 "depart_slug": depart_slug,
#                 "deadline": datetime_info.get("deadline"),
#                 "message": message_text,
#             }

#         # ── PRE-FILTER 0: /tasks — view-only ─────────────────────────────────
#         if self._is_view_tasks_request(message):
#             return _build("/tasks")

#         # ─────────────────────────────────────────────────────────────────────
#         # TASK-REFERENCE DETECTION
#         # A "task reference" means the message explicitly talks about a specific
#         # task (by number, word, or ID keyword).
#         #
#         # Matches:
#         #   "task 4", "task id 4", "id 4", "4 number wala task",
#         #   "#4", "task no 4", "task number 4", "4 wala task"
#         # ─────────────────────────────────────────────────────────────────────
#         _TASK_REF_PATTERNS = [
#             r"\btask\s*(id\s*)?\d+",          # "task 4", "task id 4"
#             r"\bid\s*\d+",                     # "id 4", "id4"
#             r"\b\d+\s*(number\s*)?wala\s*task",# "4 wala task", "4 number wala task"
#             r"\btask\s*(no|number|#)\s*\d+",   # "task no 4", "task #4"
#             r"#\d+",                           # "#4"
#             r"\b\d+\s*wala\s*(kaam|task|number)", # "4 wala kaam" (referring to task)
#         ]

#         def _has_task_reference(text: str) -> tuple[bool, int | None]:
#             """
#             Returns (True, task_id) if a task reference is found, else (False, None).
#             task_id is the extracted integer if present, else None.
#             """
#             tl = text.lower()
#             for pat in _TASK_REF_PATTERNS:
#                 m = re.search(pat, tl, re.IGNORECASE | re.UNICODE)
#                 if m:
#                     # Try to extract the number from the matched span
#                     num = re.search(r"\d+", m.group(0))
#                     return True, (int(num.group()) if num else None)
#             return False, None

#         has_task_ref, task_ref_id = _has_task_reference(message)

#         # Also detect the old "task\s+\d+" pattern
#         task_id_match = re.search(r"task\s+(\d+)|(\d+)\s+task", ml)

#         # ── PRE-FILTER A: Self-assign (manager assigning task to themselves) ──
#         # Covers: "task 32 main karunga", "I will do task 32", "task 32 myself"
#         # Returns: /mgrself with id only, worker_slug = null
#         _SELF_ASSIGN_PATTERNS = [
#             r"\b(task|id|#)?\s*(\d+)\s*(main|mai|mein|me|i)\s+(karunga|kar\s+lunga|kar\s+leta\s+hu|karunga|kar\s+dunga|khud\s+karunga|will\s+do|will\s+take|'ll\s+do)\b",
#             r"\b(main|mai|mein|me|i)\s+(karunga|kar\s+lunga|kar\s+leta\s+hu|karunga|kar\s+dunga|khud\s+karunga|will\s+do|will\s+take|'ll\s+do)\s+(task|id|#)?\s*(\d+)\b",
#             r"\bkhud\s+(karunga|kar\s+lunga|kar\s+leta)\s+(task|id|#)?\s*(\d+)\b",
#             r"\b(task|id|#)?\s*(\d+)\s+(myself|khud)\b",
#             r"\b(i\s+will\s+do\s+task\s+\d+|i'll\s+do\s+task\s+\d+)\b",
#         ]
        
#         is_self_assign = False
#         self_task_id = None
        
#         for pattern in _SELF_ASSIGN_PATTERNS:
#             match = re.search(pattern, ml, re.IGNORECASE | re.UNICODE)
#             if match:
#                 is_self_assign = True
#                 # Extract task ID (could be in different groups)
#                 for group in match.groups():
#                     if group and group.isdigit():
#                         self_task_id = int(group)
#                         break
#                 break
        
#         # Also check for patterns without task reference (pure self-claim without task number)
#         _SELF_CLAIM_NO_TASK = [
#             r"\b(main|mai|mein|i)\s+(karunga|karungi|kar\s+leta|kar\s+leti|kar\s+lunga|kar\s+lungi|will\s+do|'ll\s+do)\s+(ye|this|iska|is)\s+(kaam|task)\b",
#             r"\b(ye|this)\s+(kaam|task)\s+(main|mai|mein|i)\s+(karunga|karungi|kar\s+leta|kar\s+leti)\b",
#         ]
        
#         if not is_self_assign:
#             for pattern in _SELF_CLAIM_NO_TASK:
#                 if re.search(pattern, ml, re.IGNORECASE | re.UNICODE):
#                     is_self_assign = True
#                     self_task_id = None
#                     break
        
#         if is_self_assign and has_task_ref:
#             # If we have a task reference, use that ID
#             tid = task_ref_id if task_ref_id else self_task_id
#             if tid is None and task_id_match:
#                 tid = int(task_id_match.group(1) or task_id_match.group(2))
#             if tid is None:
#                 # Try to find any number in the message
#                 bare_id = re.search(r"\b(\d+)\b", message)
#                 if bare_id:
#                     tid = int(bare_id.group(1))
#             # Return /mgrself with worker_slug = null
#             return _build("/mgrself", tid, worker_slug=None)

#         # ── PRE-FILTER B: Manager assigns task to another person ─────────────
#         # Triggers when: task reference present + person named (with @ or name)
#         # "task 32 @ajay ko do" → /mgrassign (id:32, worker_slug:@ajay)
#         # "@ajay will do task 32" → /mgrassign (id:32, worker_slug:@ajay)
        
#         if has_task_ref:
#             # Resolve the task ID
#             tid = task_ref_id
#             if tid is None and task_id_match:
#                 tid = int(task_id_match.group(1) or task_id_match.group(2))
            
#             # Check for named person (with @mention)
#             at_m = re.search(r"@(\w+)", message)
#             if at_m:
#                 return _build("/mgrassign", tid, f"@{at_m.group(1)}")
            
#             # Check for named person (without @)
#             name_match = re.search(
#                 r"([A-Za-z\u0900-\u097F]{2,20})\s+ko\b", message, re.UNICODE
#             )
#             if name_match and name_match.group(1).lower() not in self._NOT_A_NAME:
#                 return _build("/mgrassign", tid, name_match.group(1))
            
#             # Check for patterns like "ajay will do task 32"
#             name_before = re.match(
#                 r"^([A-Za-z\u0900-\u097F]{2,20})\s+(will|ko|se)", message, re.IGNORECASE | re.UNICODE
#             )
#             if name_before and name_before.group(1).lower() not in self._NOT_A_NAME:
#                 return _build("/mgrassign", tid, name_before.group(1))

#         # ── PRE-FILTER C: @mention + NO task reference → /assign ─────────────
#         at_m = re.search(r"@(\w+)", message)
#         if at_m:
#             if has_task_ref:
#                 return _build("/mgrassign", task_ref_id, f"@{at_m.group(1)}")
#             return _build("/assign", worker_slug=f"@{at_m.group(1)}")

#         # ── PRE-FILTER D: Named person + NO task reference → /assign ──────────
#         assignee = self._extract_assignee(message)
#         if assignee:
#             if has_task_ref:
#                 return _build("/mgrassign", task_ref_id, assignee)
#             return _build("/assign", worker_slug=assignee)

#         # ── PRE-FILTER E: Attendance commands ────────────────────────────────
#         if re.search(
#             r"\b(present\s+hu|aa\s+gaya|aaya\s+hu|pahunch\s+gaya|aaj\s+aaya|i\s+am\s+here|mai\s+aa\s+gaya|main\s+aa\s+gaya)\b",
#             ml, re.IGNORECASE | re.UNICODE,
#         ):
#             return _build("/present")

#         if re.search(
#             r"\b(absent\s+hu|nahi\s+aa\s+sakta|chutti\s+chahiye|chutti\s+le|leave\s+chahiye|aaj\s+nahi\s+aaunga|nahi\s+aa\s+pa|nahi\s+aaonga)\b",
#             ml, re.IGNORECASE | re.UNICODE,
#         ):
#             return _build("/absent")

#         # ── PRE-FILTER F: Past-tense completion ──────────────────────────────
#         if re.search(
#             r"\b(ho\s+gaya|kar\s+diya|khatam\s+ho\s+gaya|complete\s+ho\s+gaya|complete\s+kar\s+diya|khatam\s+kiya|done\s+hai|finished)\b",
#             ml, re.IGNORECASE | re.UNICODE,
#         ):
#             id_m = re.search(r"\b(\d+)\b", message)
#             return _build("/complete", int(id_m.group(1)) if id_m else None)

#         # ── PRE-FILTER G: Work instruction with NO person → /depart_assign ────
#         work_instruction_patterns = [
#             r"\b(bhejo|bhej|karo|karna|krdo|krdena|banao|banana|lao|lana|chalao|chalana|"
#             r"safai|clean|clear|pack|load|unload|dispatch|deliver|send|purchase|buy|"
#             r"kharido|mangao|install|fix|check|repair|khali)\b",
#             r"\b(units?|maal|samaan|invoice|order|shipment|warehouse|godown|machine|"
#             r"computer|laptop|server|material|stock)\b",
#         ]
#         is_work_instruction = any(
#             re.search(p, ml, re.IGNORECASE | re.UNICODE)
#             for p in work_instruction_patterns
#         )

#         if is_work_instruction:
#             # Try fast keyword detection first
#             dept = detect_department_by_keywords(message)
#             if dept is None:
#                 # Fall back to LLM department classification
#                 dept = self._classify_department_via_llm(message)
#             return _build("/depart_assign", depart_slug=dept)

#         # ── LLM: handle everything remaining ─────────────────────────────────
#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             messages=[
#                 {"role": "system", "content": self._build_system_prompt()},
#                 {"role": "user",   "content": message},
#             ],
#             temperature=0.1,
#             max_tokens=150,
#             response_format={"type": "json_object"},
#         )

#         raw_reply = response.choices[0].message.content.strip()
#         result = self._parse_decision(raw_reply)

#         intent = result.get("intent", "general_chat")
#         result["deadline"] = datetime_info.get("deadline")
#         result.setdefault("depart_slug", None)

#         # Message ONLY for general_chat intent
#         if intent == "general_chat":
#             result["message"] = get_professional_response(message, datetime_info)
#         else:
#             result["message"] = None

#         # If LLM returned /assign with no person → upgrade to /depart_assign with dept
#         if intent == "/assign" and not result.get("worker_slug"):
#             dept = detect_department_by_keywords(message)
#             if dept is None:
#                 dept = self._classify_department_via_llm(message)
#             result["intent"] = "/depart_assign"
#             result["depart_slug"] = dept

#         # If LLM returned /depart_assign, ensure depart_slug is set
#         if intent == "/depart_assign" and not result.get("depart_slug"):
#             dept = detect_department_by_keywords(message)
#             if dept is None:
#                 dept = self._classify_department_via_llm(message)
#             result["depart_slug"] = dept
        
#         # Convert any /mgrassign with worker_slug="self" to /mgrself
#         if intent == "/mgrassign" and result.get("worker_slug") == "self":
#             result["intent"] = "/mgrself"
#             result["worker_slug"] = None

#         return result

#     def _build_system_prompt(self) -> str:
#         return """You are a pure intent classification system for a WhatsApp-based worker assistant called Munshi Dada.
# Your ONLY job is to classify the user's message into exactly one intent and extract relevant IDs.
# Respond with ONLY a valid JSON object. No text, no markdown, no explanations.

# ════════════════════════════════════════════════════════
# INTENT CLASSIFICATION RULES
# ════════════════════════════════════════════════════════

# 1. "/tasks" — ONLY "view my tasks" requests
#    Examples: "mera kaam dikhao", "my tasks", "task list", "pending tasks", "kya karna hai"

# 2. "/assign" — Work directed at a NAMED person, but NO specific task reference
#    The message mentions a person AND a piece of work (not a specific task number/id).
#    Examples:
#      "@ajay warehouse khali karo"          → /assign (worker_slug: @ajay)
#      "rahul ko invoice bhejdo"             → /assign (worker_slug: rahul)
#      "@priya client ko call karo"          → /assign (worker_slug: @priya)
#    → Always set worker_slug. depart_slug must be null.
#    → KEY: No task ID / task number / "id X" / "#X" in the message.

# 3. "/depart_assign" — Work instruction with NO named person; route to a department
#    Examples: "warehouse khali karo", "500 units bhejdo", "invoice banao", "purchase karo",
#              "server theek karo", "material order karo"
#    → Always set depart_slug to one of: operations, sales, purchase, it
#    → worker_slug must be null

# 4. "/mgrassign" — Manager assigns a specific task (by ID/number) to another person
#    TASK REFERENCE means: a specific task number, "task X", "id X", "#X",
#    "X wala task", "task id X", "task no X", "X number wala task".
   
#    Examples:
#      "@ajay id 4 wala kaam pura kardo"    → /mgrassign (id:4,  worker_slug:@ajay)
#      "task 32 ajay ko do"                 → /mgrassign (id:32, worker_slug:ajay)
#      "@rahul #7 complete karo"            → /mgrassign (id:7,  worker_slug:@rahul)
#      "ajay will do task 32"               → /mgrassign (id:32, worker_slug:ajay)
#    → worker_slug must be the person's name (with @ if mentioned)

# 5. "/mgrself" — Manager assigns a task to themselves (self-assign)
#    Examples:
#      "task 32 main karunga"               → /mgrself (id:32, worker_slug:null)
#      "I will do task 32 myself"           → /mgrself (id:32, worker_slug:null)
#      "task 18 mai khud karunga"           → /mgrself (id:18, worker_slug:null)
#      "main ye task kar lunga"              → /mgrself (id:null, worker_slug:null)
#    → worker_slug MUST be null for /mgrself

# 6. "/update" — Updating a task with comment/status

# 7. "/issue" — Reporting a new issue
#    Examples: "issue hai", "machine kharab", "kuch kharab hai"

# 8. "/issues" — View all active issues

# 9. "/resolve" — Marking an issue as resolved

# 10. "/members" — View team members

# 11. "/report" — Generate a report

# 12. "/help" — Need help with commands

# 13. "general_chat" — ONLY pure conversation: greetings, small talk, non-work
#     Examples: "hello", "hi", "kaise ho", "good morning", "shukriya"

# ════════════════════════════════════════════════════════
# OUTPUT FORMAT
# ════════════════════════════════════════════════════════
# {"intent": "<intent_name>", "id": <int or null>, "worker_slug": "<@username, name, or null>", "depart_slug": "<operations|sales|purchase|it|null>"}

# Rules:
# - /assign      → worker_slug set (person's name), depart_slug null
# - /depart_assign → depart_slug set, worker_slug null
# - /mgrassign   → id set, worker_slug set (person's name), depart_slug null
# - /mgrself     → id set (if available), worker_slug null, depart_slug null
# - All other intents → both null
# """

#     def _parse_decision(self, raw: str) -> dict:
#         try:
#             return json.loads(raw)
#         except Exception:
#             clean = re.sub(r"```json|```", "", raw).strip()
#             try:
#                 return json.loads(clean)
#             except Exception:
#                 return {"intent": "general_chat", "id": None, "worker_slug": None, "depart_slug": None}


# # ─────────────────────────────────────────────────────────────
# # COMMAND PARSER
# # ─────────────────────────────────────────────────────────────
# class CommandParser:
#     def __init__(self):
#         self.datetime_extractor = DateTimeExtractor()

#     def parse(self, message: str) -> dict | None:
#         message = message.strip()
#         ml = message.lower()

#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         def base(intent, id_=None, worker_slug=None, depart_slug=None):
#             return {
#                 "intent": intent,
#                 "id": id_,
#                 "worker_slug": worker_slug,
#                 "depart_slug": depart_slug,
#                 "deadline": datetime_info.get("deadline"),
#                 "message": None,
#             }

#         def extract_leading_int(text: str):
#             m = re.search(r"^\d+", text.strip())
#             return int(m.group()) if m else None

#         # Slash commands
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
#         if ml.startswith("/mgrself"):
#             rest = message[8:].strip()
#             task_match = re.search(r"(\d+)", rest)
#             if task_match:
#                 return base("/mgrself", int(task_match.group(1)), None)
#             return base("/mgrself")
#         if ml.startswith("/mgrassign"):
#             rest = message[10:].strip()
#             task_match = re.search(r"(\d+)", rest)
#             assignee_match = re.search(r"@(\w+)", rest)
#             if task_match and assignee_match:
#                 return base("/mgrassign", int(task_match.group(1)), f"@{assignee_match.group(1)}")
#             elif task_match:
#                 return base("/mgrassign", int(task_match.group(1)), None)
#             return base("/mgrassign")
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

#         return None















# """
# bot_engine.py
# Production Hybrid Intent Classification Engine

# Architecture:
# 1. Slash command parser
# 2. Lightweight deterministic extraction
# 3. LLM semantic intent classification
# 4. Validation layer
# 5. Structured JSON response

# Supports:
# - English
# - Hindi
# - Hinglish

# Author: OpenAI Hybrid Architecture
# """

# import json
# import os
# import re
# from datetime import datetime, timedelta
# from typing import Optional, Dict, Any

# from dateutil.relativedelta import relativedelta
# from dotenv import load_dotenv
# from openai import OpenAI

# # ============================================================
# # ENV
# # ============================================================

# load_dotenv()

# client = OpenAI(
#     api_key=os.getenv("OPENAI_API_KEY")
# )

# CHAT_MODEL = "gpt-4.1-mini"

# # ============================================================
# # DATE EXTRACTOR
# # ============================================================


# class DateTimeExtractor:

#     RELATIVE_KEYWORDS = {
#         "today": 0,
#         "aaj": 0,
#         "आज": 0,

#         "tomorrow": 1,
#         "kal": 1,
#         "कल": 1,

#         "parso": 2,
#         "परसों": 2,
#         "day after tomorrow": 2,
#     }

#     CLOCK_RE = re.compile(
#         r"(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje|bje|baj|बजे)?",
#         re.IGNORECASE,
#     )

#     @staticmethod
#     def parse_clock(message: str):

#         match = DateTimeExtractor.CLOCK_RE.search(message)

#         if not match:
#             return None

#         hour = int(match.group(1))
#         minute = int(match.group(2)) if match.group(2) else 0

#         ampm = match.group(3)

#         if ampm:

#             ampm = ampm.lower()

#             if ampm == "pm" and hour != 12:
#                 hour += 12

#             elif ampm == "am" and hour == 12:
#                 hour = 0

#             elif ampm in ["baje", "bje", "baj", "बजे"]:

#                 # heuristic
#                 if 1 <= hour <= 6:
#                     hour += 12

#         return hour, minute

#     @staticmethod
#     def extract_date_from_message(message: str):

#         now = datetime.now()
#         today = now.date()

#         ml = message.lower()

#         final_date = None

#         # relative keywords
#         for word, offset in DateTimeExtractor.RELATIVE_KEYWORDS.items():

#             if word in ml:
#                 final_date = today + timedelta(days=offset)
#                 break

#         # next week
#         if "next week" in ml or "agle hafte" in ml:
#             final_date = today + timedelta(days=7)

#         # next month
#         if "next month" in ml or "agle mahine" in ml:
#             final_date = today + relativedelta(months=1)

#         # explicit date dd-mm-yyyy
#         explicit_date = re.search(
#             r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
#             message,
#         )

#         if explicit_date:

#             day, month, year = explicit_date.groups()

#             try:

#                 final_date = datetime(
#                     int(year),
#                     int(month),
#                     int(day)
#                 ).date()

#             except Exception:
#                 pass

#         if not final_date:
#             return {
#                 "deadline": None,
#                 "type": None,
#             }

#         clock = DateTimeExtractor.parse_clock(message)

#         if clock:

#             hour, minute = clock

#             dt = datetime(
#                 final_date.year,
#                 final_date.month,
#                 final_date.day,
#                 hour,
#                 minute,
#                 0,
#             )

#             return {
#                 "deadline": dt.isoformat(),
#                 "type": "datetime",
#             }

#         return {
#             "deadline": final_date.strftime("%Y-%m-%d"),
#             "type": "date",
#         }


# # ============================================================
# # GENERAL CHAT RESPONSE
# # ============================================================


# def get_general_chat_response(message: str):

#     return (
#         "Main task management, attendance, assignment aur reports mein help kar sakta hoon. "
#         "Commands dekhne ke liye /help type karo."
#     )


# # ============================================================
# # COMMAND PARSER
# # ============================================================


# class CommandParser:

#     def __init__(self):

#         self.datetime_extractor = DateTimeExtractor()

#     def parse(self, message: str):

#         message = message.strip()

#         ml = message.lower()

#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         def build(
#             intent,
#             id=None,
#             worker_slug=None,
#             depart_slug=None,
#             reject_reason=None,
#         ):

#             result = {
#                 "intent": intent,
#                 "id": id,
#                 "worker_slug": worker_slug,
#                 "depart_slug": depart_slug,
#                 "deadline": datetime_info.get("deadline"),
#                 "message": None,
#                 "reject_reason": reject_reason,
#             }

#             return result

#         # ====================================================
#         # COMMANDS
#         # ====================================================

#         if ml.startswith("/tasks"):
#             return build("/tasks")

#         if ml.startswith("/present"):
#             return build("/present")

#         if ml.startswith("/absent"):
#             return build("/absent")

#         if ml.startswith("/help"):
#             return build("/help")

#         if ml.startswith("/report"):
#             return build("/report")

#         if ml.startswith("/members"):
#             return build("/members")

#         if ml.startswith("/issues"):
#             return build("/issues")

#         if ml.startswith("/issue"):
#             return build("/issue")

#         if ml.startswith("/resolve"):

#             task_id = re.search(r"\d+", message)

#             return build(
#                 "/resolve",
#                 int(task_id.group()) if task_id else None,
#             )

#         if ml.startswith("/complete"):

#             task_id = re.search(r"\d+", message)

#             return build(
#                 "/complete",
#                 int(task_id.group()) if task_id else None,
#             )

#         if ml.startswith("/update"):

#             task_id = re.search(r"\d+", message)

#             return build(
#                 "/update",
#                 int(task_id.group()) if task_id else None,
#             )

#         # ====================================================
#         # NEW: MGRTRANSFER COMMAND
#         # ====================================================

#         if ml.startswith("/mgrtransfer"):

#             # Pattern: /mgrtransfer 12 sales
#             match = re.search(r"/mgrtransfer\s+(\d+)\s+(\w+)", message, re.IGNORECASE)

#             if match:
#                 task_id = int(match.group(1))
#                 depart_slug = match.group(2).lower()

#                 return build(
#                     "/mgrtransfer",
#                     id=task_id,
#                     depart_slug=depart_slug,
#                 )

#             # If pattern doesn't match, just extract task id
#             task_id = re.search(r"\d+", message)
#             return build(
#                 "/mgrtransfer",
#                 id=int(task_id.group()) if task_id else None,
#                 depart_slug=None,
#             )

#         # ====================================================
#         # NEW: MGRREJECT COMMAND
#         # ====================================================

#         if ml.startswith("/mgrreject"):

#             # Pattern: /mgrreject 12 not our department scope
#             match = re.match(r"/mgrreject\s+(\d+)\s+(.*)", message, re.IGNORECASE)

#             if match:
#                 task_id = int(match.group(1))
#                 reason = match.group(2).strip()

#                 return build(
#                     "/mgrreject",
#                     id=task_id,
#                     reject_reason=reason,
#                 )

#             # If only task id provided
#             task_id = re.search(r"\d+", message)
#             return build(
#                 "/mgrreject",
#                 id=int(task_id.group()) if task_id else None,
#                 reject_reason=None,
#             )

#         return None


# # ============================================================
# # INTENT CLASSIFIER
# # ============================================================


# class IntentClassifier:

#     VALID_INTENTS = {
#         "/tasks",
#         "/assign",
#         "/depart_assign",
#         "/mgrassign",
#         "/mgrself",
#         "/update",
#         "/issue",
#         "/issues",
#         "/resolve",
#         "/members",
#         "/report",
#         "/help",
#         "/present",
#         "/absent",
#         "/complete",
#         "/mgrtransfer",  # NEW
#         "/mgrreject",    # NEW
#         "general_chat",
#     }

#     VALID_DEPARTMENTS = {
#         "operations",
#         "sales",
#         "purchase",
#         "it",
#     }

#     def __init__(self):

#         self.datetime_extractor = DateTimeExtractor()

#         print("✅ Hybrid Intent Classifier Loaded")

#     # ========================================================
#     # ENTITY EXTRACTION
#     # ========================================================

#     def extract_task_id(self, message: str):

#         patterns = [

#             r"task\s*(?:id)?\s*(\d+)",

#             r"id\s*(\d+)",

#             r"#(\d+)",

#             r"(\d+)\s*wala\s*task",

#             r"task\s*number\s*(\d+)",

#             r"task\s*no\s*(\d+)",
#         ]

#         for pattern in patterns:

#             match = re.search(
#                 pattern,
#                 message,
#                 re.IGNORECASE,
#             )

#             if match:
#                 return int(match.group(1))

#         return None

#     def extract_mentions(self, message: str):

#         mentions = re.findall(
#             r"@(\w+)",
#             message,
#         )

#         if mentions:
#             return f"@{mentions[0]}"

#         return None

#     def extract_reject_reason(self, message: str):

#         # Extract reason after task reference patterns
#         patterns = [
#             r"(?:reject|rejection)\s+(?:task\s+)?(\d+)\s+(?:because|reason|:)?\s*(.+)",
#             r"(?:task\s+)?(\d+)\s+(?:is|was)\s+rejected\s+(?:because|as|since)?\s*(.+)",
#             r"wrong\s+department\s*(?:for\s+)?(?:task\s+)?(\d+)?",
#         ]

#         for pattern in patterns:
#             match = re.search(pattern, message, re.IGNORECASE)
#             if match:
#                 if len(match.groups()) == 2 and match.group(2):
#                     return match.group(2).strip()
#                 elif match.group(1) and not match.group(2):
#                     return "No reason provided"
#                 elif "wrong department" in message.lower():
#                     return "Wrong department"

#         # Check for common rejection phrases
#         if "wrong department" in message.lower():
#             return "Task assigned to wrong department"
#         if "not our scope" in message.lower():
#             return "Task not in department scope"
#         if "not my department" in message.lower():
#             return "Task does not belong to this department"

#         return None

#     # ========================================================
#     # LLM CLASSIFICATION
#     # ========================================================

#     def llm_classify(self, message: str):

#         response = client.chat.completions.create(
#             model=CHAT_MODEL,
#             temperature=0,
#             response_format={
#                 "type": "json_object"
#             },
#             messages=[
#                 {
#                     "role": "system",
#                     "content": self.build_system_prompt(),
#                 },
#                 {
#                     "role": "user",
#                     "content": message,
#                 },
#             ],
#         )

#         raw = response.choices[0].message.content

#         try:
#             return json.loads(raw)

#         except Exception:

#             return {
#                 "intent": "general_chat",
#                 "worker_slug": None,
#                 "depart_slug": None,
#                 "reject_reason": None,
#             }

#     # ========================================================
#     # MAIN PIPELINE
#     # ========================================================

#     def classify(self, message: str):

#         datetime_info = self.datetime_extractor.extract_date_from_message(message)

#         task_id = self.extract_task_id(message)

#         mention = self.extract_mentions(message)

#         reject_reason = self.extract_reject_reason(message)

#         llm_result = self.llm_classify(message)

#         intent = llm_result.get(
#             "intent",
#             "general_chat",
#         )

#         # validate intent
#         if intent not in self.VALID_INTENTS:
#             intent = "general_chat"

#         worker_slug = llm_result.get("worker_slug")

#         depart_slug = llm_result.get("depart_slug")

#         # For mgrreject, get reject reason from LLM result or extracted
#         reject_reason_from_llm = llm_result.get("reject_reason")
#         final_reject_reason = reject_reason_from_llm or reject_reason

#         # mention override
#         if mention and not worker_slug:
#             worker_slug = mention

#         # department validation
#         if depart_slug:

#             if depart_slug not in self.VALID_DEPARTMENTS:
#                 depart_slug = None

#         result = {
#             "intent": intent,
#             "id": task_id,
#             "worker_slug": worker_slug,
#             "depart_slug": depart_slug,
#             "deadline": datetime_info.get("deadline"),
#             "message": None,
#             "reject_reason": final_reject_reason if intent == "/mgrreject" else None,
#         }

#         # general response
#         if intent == "general_chat":

#             result["message"] = get_general_chat_response(message)

#         return result

#     # ========================================================
#     # SYSTEM PROMPT
#     # ========================================================

#     def build_system_prompt(self):

#         return """
#     You are an enterprise multilingual intent classification engine.

# You understand:
# - English
# - Hindi
# - Hinglish

# You ONLY return valid JSON.

# ========================================================
# CORE UNDERSTANDING RULE
# ========================================================

# You MUST understand SEMANTIC MEANING, not just keywords.

# VERY IMPORTANT:

# There is a BIG difference between:

# 1. INSTRUCTING someone to do work
# 2. CONFIRMING work is already completed

# Examples:

# "complete the work"
# -> instruction
# -> /assign or /depart_assign

# "finish the task"
# -> instruction
# -> /assign or /depart_assign

# "task complete ho gaya"
# -> already completed
# -> /complete

# "done"
# -> already completed
# -> /complete

# "kar diya"
# -> already completed
# -> /complete

# ========================================================
# SUPPORTED INTENTS
# ========================================================

# 1. /tasks
# User wants to view their tasks.

# Examples:
# - mera kaam dikhao
# - my tasks
# - pending tasks
# - mujhe kya karna hai
# - task list dikhao

# ========================================================

# 2. /assign

# Assigning NEW work to a specific person.

# This means:
# - user is instructing a person to do work
# - NO existing task reference

# Examples:
# - ajay ko warehouse khali karne bolo
# - @rahul invoice bhejdo
# - priya client ko call kare
# - ajay complete the work
# - complete the work ajay
# - rahul ye task finish karo

# IMPORTANT:
# If user is telling someone to complete/finish work,
# it is STILL assignment.

# Rules:
# - worker_slug required
# - depart_slug null

# ========================================================

# 3. /depart_assign

# Assigning work to a department WITHOUT naming a person.

# Departments:
# - operations
# - sales
# - purchase
# - it

# Examples:
# - warehouse khali karo
# - invoice bhejo
# - server theek karo
# - raw material order karo
# - complete the dispatch work
# - finish warehouse cleaning

# Rules:
# - depart_slug required
# - worker_slug null

# ========================================================

# 4. /mgrassign

# Manager assigning EXISTING TASK to another person.

# This ONLY applies when:
# - existing task reference present
# AND
# - another person mentioned

# Task references:
# - task 5
# - id 7
# - #9
# - 4 wala task

# Examples:
# - task 32 ajay ko do
# - task 5 @rahul ko assign karo
# - id 4 priya ko de do
# - task 9 ajay complete karo

# Rules:
# - worker_slug required
# - existing task reference required

# ========================================================

# 5. /mgrself

# Manager taking task themselves.

# Examples:
# - task 32 main karunga
# - main ye task kar lunga
# - i will do task 8
# - task 9 mai khud karunga

# Rules:
# - worker_slug null

# ========================================================

# 6. /complete

# ONLY when the user is CONFIRMING
# that work is ALREADY FINISHED.

# This is NOT an instruction.

# Examples:
# - ho gaya
# - kar diya
# - done
# - completed
# - task complete ho gaya
# - work finished
# - task khatam ho gaya
# - complete kar diya
# - dispatch done

# IMPORTANT:
# If user is INSTRUCTING someone to complete work,
# then it is NOT /complete.

# Examples:
# - complete the work
# - finish the task
# - ajay complete this
# - warehouse complete karo

# These are assignments.

# ========================================================

# 7. /update

# Updating status of existing work/task.

# Examples:
# - task delayed hai
# - task pending hai
# - update task 4
# - task 5 hold pe hai

# ========================================================

# 8. /issue

# Reporting a new issue/problem.

# Examples:
# - machine kharab hai
# - issue hai
# - server down hai
# - printer kaam nahi kar raha

# ========================================================

# 9. /issues

# Viewing issues.

# Examples:
# - active issues
# - show issues
# - issues dikhao

# ========================================================

# 10. /resolve

# Resolving issue.

# Examples:
# - resolve issue 4
# - issue theek ho gaya
# - problem solved

# ========================================================

# 11. /present

# Attendance present.

# Examples:
# - aa gaya hu
# - present hu
# - i am here
# - office aa gaya

# ========================================================

# 12. /absent

# Attendance absent.

# Examples:
# - absent hu
# - nahi aaunga
# - leave chahiye
# - aaj nahi aa paunga

# ========================================================

# 13. /members

# Viewing members/team.

# Examples:
# - members dikhao
# - team members
# - employee list

# ========================================================

# 14. /report

# Generating reports.

# Examples:
# - report generate karo
# - daily report
# - weekly report

# ========================================================

# 15. /help

# Help request.

# Examples:
# - help
# - commands batao
# - kaise use kare

# ========================================================

# 16. /mgrtransfer

# Transfer an existing task to another department.

# The task is sent to the target department's manager
# with a fresh routing prompt.

# Examples:
# - transfer task 12 to sales department
# - task 15 ko it department bhejo
# - move task 8 to operations
# - reassign task 20 to purchase

# Rules:
# - task id required
# - depart_slug required (operations|sales|purchase|it)

# ========================================================

# 17. /mgrreject

# Reject a task with a reason.

# Owner receives notification with reason and manager details.
# Task status becomes REJECTED_BY_MANAGER.

# Examples:
# - reject task 12 - wrong department
# - task 15 reject karo, not our scope
# - isko reject karo, ye sales ka kaam hai
# - reject task 8 - out of scope

# Rules:
# - task id required
# - reject_reason extracted from message

# ========================================================

# 18. general_chat

# Casual conversation only.

# Examples:
# - hello
# - hi
# - kaise ho
# - good morning

# ========================================================
# DEPARTMENT ROUTING RULES
# ========================================================

# operations:
# - warehouse
# - dispatch
# - logistics
# - delivery
# - inventory
# - production
# - machine
# - packaging
# - loading/unloading

# sales:
# - invoice
# - customer
# - client
# - quotation
# - payment
# - order

# purchase:
# - vendor
# - supplier
# - procurement
# - raw material
# - buying
# - sourcing

# it:
# - server
# - laptop
# - computer
# - software
# - internet
# - wifi
# - printer

# ========================================================
# OUTPUT FORMAT
# ========================================================

# Return ONLY valid JSON.

# For /mgrtransfer:
# {
#   "intent": "/mgrtransfer",
#   "worker_slug": null,
#   "depart_slug": "operations|sales|purchase|it"
# }

# For /mgrreject:
# {
#   "intent": "/mgrreject",
#   "worker_slug": null,
#   "depart_slug": null,
#   "reject_reason": "string"
# }

# For other intents:
# {
#   "intent": "string",
#   "worker_slug": "string or null",
#   "depart_slug": "operations|sales|purchase|it|null",
#   "reject_reason": null
# }

# ========================================================
# STRICT RULES
# ========================================================

# - /assign => worker_slug required
# - /mgrassign => worker_slug required
# - /depart_assign => depart_slug required
# - /mgrself => worker_slug null
# - /mgrtransfer => depart_slug required, worker_slug null
# - /mgrreject => reject_reason optional but recommended
# - all others => both null

# Never return explanations.
# Never return markdown.
# Only return JSON.
# """
















"""
bot_engine.py
Production Hybrid Intent Classification Engine

Architecture:
1. Slash command parser
2. Lightweight deterministic extraction
3. LLM semantic intent classification (with few-shot examples)
4. Validation layer
5. Structured JSON response

Supports:
- English
- Hindi
- Hinglish

Changes from v1:
- Added rich few-shot examples to LLM system prompt (primary fix for non-determinism)
- Added a second LLM "confidence check" call when intent is ambiguous
- Removed conflicting regex-based extract_reject_reason (LLM handles it)
- Tightened CLOCK_RE to avoid false matches on plain numbers
- Made department validation case-insensitive and slug-normalized
- Added deterministic pre-classification rules that short-circuit the LLM
  for the most commonly confused pairs (/assign vs /depart_assign,
  instruction vs /complete)
"""

import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from openai import OpenAI

# ============================================================
# ENV
# ============================================================

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CHAT_MODEL = "gpt-4.1-mini"

# ============================================================
# DATE EXTRACTOR
# ============================================================


class DateTimeExtractor:

    RELATIVE_KEYWORDS = {
        "today": 0,
        "aaj": 0,
        "आज": 0,
        "tomorrow": 1,
        "kal": 1,
        "कल": 1,
        "parso": 2,
        "परसों": 2,
        "day after tomorrow": 2,
    }

    # FIX: Added word-boundary anchors so "12 people" doesn't parse as 12:00
    CLOCK_RE = re.compile(
        r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|baje|bje|baj|बजे)\b",
        re.IGNORECASE,
    )

    @staticmethod
    def parse_clock(message: str):
        match = DateTimeExtractor.CLOCK_RE.search(message)
        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        ampm = match.group(3)

        if ampm:
            ampm = ampm.lower()
            if ampm == "pm" and hour != 12:
                hour += 12
            elif ampm == "am" and hour == 12:
                hour = 0
            elif ampm in ["baje", "bje", "baj", "बजे"]:
                if 1 <= hour <= 6:
                    hour += 12

        return hour, minute

    @staticmethod
    def extract_date_from_message(message: str):
        now = datetime.now()
        today = now.date()
        ml = message.lower()
        final_date = None

        for word, offset in DateTimeExtractor.RELATIVE_KEYWORDS.items():
            if word in ml:
                final_date = today + timedelta(days=offset)
                break

        if "next week" in ml or "agle hafte" in ml:
            final_date = today + timedelta(days=7)

        if "next month" in ml or "agle mahine" in ml:
            final_date = today + relativedelta(months=1)

        explicit_date = re.search(
            r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
            message,
        )

        if explicit_date:
            day, month, year = explicit_date.groups()
            try:
                final_date = datetime(int(year), int(month), int(day)).date()
            except Exception:
                pass

        if not final_date:
            return {"deadline": None, "type": None}

        clock = DateTimeExtractor.parse_clock(message)
        if clock:
            hour, minute = clock
            dt = datetime(
                final_date.year, final_date.month, final_date.day, hour, minute, 0
            )
            return {"deadline": dt.isoformat(), "type": "datetime"}

        return {"deadline": final_date.strftime("%Y-%m-%d"), "type": "date"}


# ============================================================
# GENERAL CHAT RESPONSE
# ============================================================


def get_general_chat_response(message: str):
    return (
        "Main task management, attendance, assignment aur reports mein help kar sakta hoon. "
        "Commands dekhne ke liye /help type karo."
    )


# ============================================================
# COMMAND PARSER
# ============================================================


class CommandParser:

    def __init__(self):
        self.datetime_extractor = DateTimeExtractor()

    def parse(self, message: str):
        message = message.strip()
        ml = message.lower()
        datetime_info = self.datetime_extractor.extract_date_from_message(message)

        def build(intent, id=None, worker_slug=None, depart_slug=None, reject_reason=None):
            return {
                "intent": intent,
                "id": id,
                "worker_slug": worker_slug,
                "depart_slug": depart_slug,
                "deadline": datetime_info.get("deadline"),
                "message": None,
                "reject_reason": reject_reason,
            }

        if ml.startswith("/tasks"):
            return build("/tasks")
        if ml.startswith("/present"):
            return build("/present")
        if ml.startswith("/absent"):
            return build("/absent")
        if ml.startswith("/help"):
            return build("/help")
        if ml.startswith("/report"):
            return build("/report")
        if ml.startswith("/members"):
            return build("/members")
        if ml.startswith("/issues"):
            return build("/issues")
        if ml.startswith("/issue"):
            return build("/issue")

        if ml.startswith("/resolve"):
            task_id = re.search(r"\d+", message)
            return build("/resolve", int(task_id.group()) if task_id else None)

        if ml.startswith("/complete"):
            task_id = re.search(r"\d+", message)
            return build("/complete", int(task_id.group()) if task_id else None)

        if ml.startswith("/update"):
            task_id = re.search(r"\d+", message)
            return build("/update", int(task_id.group()) if task_id else None)

        if ml.startswith("/mgrtransfer"):
            match = re.search(r"/mgrtransfer\s+(\d+)\s+(\w+)", message, re.IGNORECASE)
            if match:
                return build(
                    "/mgrtransfer",
                    id=int(match.group(1)),
                    depart_slug=match.group(2).lower(),
                )
            task_id = re.search(r"\d+", message)
            return build("/mgrtransfer", id=int(task_id.group()) if task_id else None)

        if ml.startswith("/mgrreject"):
            match = re.match(r"/mgrreject\s+(\d+)\s+(.*)", message, re.IGNORECASE)
            if match:
                return build(
                    "/mgrreject",
                    id=int(match.group(1)),
                    reject_reason=match.group(2).strip(),
                )
            task_id = re.search(r"\d+", message)
            return build("/mgrreject", id=int(task_id.group()) if task_id else None)

        return None


# ============================================================
# DETERMINISTIC PRE-CLASSIFIER
# Runs BEFORE the LLM to short-circuit high-confidence cases.
# Prevents the LLM from flip-flopping on common patterns.
# ============================================================

# Patterns that CONFIRM work is already done (→ /complete)
_COMPLETION_CONFIRMED_RE = re.compile(
    r"\b("
    r"ho\s*gaya|kar\s*diya|khatam\s*ho\s*gaya|khatam\s*kar\s*diya"
    r"|done|finished|completed|complete\s*ho\s*gaya|complete\s*kar\s*diya"
    r"|dispatch\s*done|kaam\s*ho\s*gaya|work\s*done|task\s*done"
    r")\b",
    re.IGNORECASE,
)

# Words that indicate an INSTRUCTION (block /complete mis-classification)
_INSTRUCTION_SIGNAL_RE = re.compile(
    r"\b("
    r"karo|kare|karein|bhejo|do\b|dedo|dijiye|bolo|boldo"
    r"|please|finish\s+the|complete\s+the|complete\s+this"
    r")\b",
    re.IGNORECASE,
)

# Patterns for @mention or explicit person name assignment
_MENTION_RE = re.compile(r"@(\w+)")

# Known department keywords → /depart_assign (no person named)
_DEPT_KEYWORDS = {
    "operations": ["warehouse", "dispatch", "logistics", "delivery", "inventory",
                   "production", "machine", "packaging", "loading", "unloading"],
    "sales":      ["invoice", "customer", "client", "quotation", "payment", "order"],
    "purchase":   ["vendor", "supplier", "procurement", "raw material", "buying", "sourcing"],
    "it":         ["server", "laptop", "computer", "software", "internet", "wifi", "printer"],
}


def _detect_department(message: str) -> Optional[str]:
    ml = message.lower()
    for dept, keywords in _DEPT_KEYWORDS.items():
        if any(kw in ml for kw in keywords):
            return dept
    return None


def deterministic_pre_classify(message: str) -> Optional[Dict[str, Any]]:
    """
    Returns a partial classification dict (intent + extracted fields) if
    we are highly confident, else returns None to fall through to the LLM.

    This eliminates the most common sources of LLM non-determinism.
    """
    ml = message.lower()

    # --- /complete detection ---
    # Only fire if completion language is present AND no instruction signal
    if _COMPLETION_CONFIRMED_RE.search(message) and not _INSTRUCTION_SIGNAL_RE.search(message):
        return {"intent": "/complete", "worker_slug": None, "depart_slug": None, "reject_reason": None}

    # --- /assign vs /depart_assign ---
    # If a @mention or recognised person pattern is present → /assign
    mention = _MENTION_RE.search(message)
    if mention:
        return {
            "intent": "/assign",
            "worker_slug": f"@{mention.group(1)}",
            "depart_slug": None,
            "reject_reason": None,
        }

    return None  # Let LLM handle it


# ============================================================
# INTENT CLASSIFIER
# ============================================================

VALID_INTENTS = {
    "/tasks", "/assign", "/depart_assign", "/mgrassign", "/mgrself",
    "/update", "/issue", "/issues", "/resolve", "/members", "/report",
    "/help", "/present", "/absent", "/complete", "/mgrtransfer",
    "/mgrreject", "general_chat",
}

VALID_DEPARTMENTS = {"operations", "sales", "purchase", "it"}


class IntentClassifier:

    def __init__(self):
        self.datetime_extractor = DateTimeExtractor()
        print("✅ Hybrid Intent Classifier Loaded (v2 - robust)")

    # --------------------------------------------------------
    # ENTITY EXTRACTION
    # --------------------------------------------------------

    def extract_task_id(self, message: str) -> Optional[int]:
        patterns = [
            r"task\s*(?:id)?\s*(\d+)",
            r"id\s*(\d+)",
            r"#(\d+)",
            r"(\d+)\s*wala\s*task",
            r"task\s*number\s*(\d+)",
            r"task\s*no\s*(\d+)",
        ]
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def extract_mentions(self, message: str) -> Optional[str]:
        mentions = _MENTION_RE.findall(message)
        return f"@{mentions[0]}" if mentions else None

    # --------------------------------------------------------
    # LLM CLASSIFICATION
    # --------------------------------------------------------

    def llm_classify(self, message: str) -> Dict[str, Any]:
        """
        Single LLM call with temperature=0 and rich few-shot examples.
        Few-shot examples are the #1 fix for non-determinism.
        """
        try:
            response = client.chat.completions.create(
                model=CHAT_MODEL,
                temperature=0,
                seed=42,          # Added: improves reproducibility where supported
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": self._build_system_prompt()},
                    {"role": "user",   "content": message},
                ],
            )
            raw = response.choices[0].message.content
            return json.loads(raw)
        except Exception:
            return {"intent": "general_chat", "worker_slug": None,
                    "depart_slug": None, "reject_reason": None}

    # --------------------------------------------------------
    # MAIN PIPELINE
    # --------------------------------------------------------

    def classify(self, message: str) -> Dict[str, Any]:

        datetime_info = self.datetime_extractor.extract_date_from_message(message)
        task_id       = self.extract_task_id(message)
        mention       = self.extract_mentions(message)

        # --- Step 1: deterministic pre-classification ---
        pre = deterministic_pre_classify(message)

        if pre is not None:
            # High-confidence deterministic path — skip LLM
            intent       = pre["intent"]
            worker_slug  = pre.get("worker_slug") or mention
            depart_slug  = pre.get("depart_slug")
            reject_reason = pre.get("reject_reason")
        else:
            # --- Step 2: LLM classification ---
            llm_result    = self.llm_classify(message)
            intent        = llm_result.get("intent", "general_chat")
            worker_slug   = llm_result.get("worker_slug")
            depart_slug   = llm_result.get("depart_slug")
            reject_reason = llm_result.get("reject_reason")

            # Validate intent
            if intent not in VALID_INTENTS:
                intent = "general_chat"

            # @mention overrides LLM worker_slug if LLM missed it
            if mention and not worker_slug:
                worker_slug = mention

            # Normalize and validate department slug
            if depart_slug:
                depart_slug = depart_slug.strip().lower()
                if depart_slug not in VALID_DEPARTMENTS:
                    depart_slug = None

        result = {
            "intent":       intent,
            "id":           task_id,
            "worker_slug":  worker_slug,
            "depart_slug":  depart_slug,
            "deadline":     datetime_info.get("deadline"),
            "message":      None,
            "reject_reason": reject_reason if intent == "/mgrreject" else None,
        }

        if intent == "general_chat":
            result["message"] = get_general_chat_response(message)

        return result

    # --------------------------------------------------------
    # SYSTEM PROMPT  (v2 — with few-shot examples)
    # --------------------------------------------------------

    def _build_system_prompt(self) -> str:
        return """
You are an enterprise multilingual intent classification engine.
You understand English, Hindi, and Hinglish.
You ONLY return valid JSON. No markdown, no explanations.

========================================================
CRITICAL DISAMBIGUATION RULE
========================================================

The single most important distinction:

INSTRUCTION (telling someone to do work in the future)
  → /assign  OR  /depart_assign  (depending on whether a person is named)

CONFIRMATION (reporting work is already done)
  → /complete

Signal words for INSTRUCTION:
  karo, kare, karein, bhejo, do, dedo, please, bolo, finish the, complete the

Signal words for CONFIRMATION:
  ho gaya, kar diya, done, finished, khatam ho gaya, dispatch done, complete ho gaya

========================================================
INTENT DEFINITIONS
========================================================

/tasks          → user wants to view their own task list
/assign         → instruct a NAMED person to do NEW work (no existing task id)
/depart_assign  → instruct a DEPARTMENT to do work (no person named, no existing task id)
/mgrassign      → reassign an EXISTING task (task id present) to a named person
/mgrself        → manager takes an existing task themselves
/complete       → CONFIRMING work is already finished
/update         → update status/details of an existing task
/issue          → report a new problem
/issues         → view existing issues
/resolve        → mark an issue as resolved
/present        → mark attendance as present
/absent         → mark attendance as absent
/members        → view team/member list
/report         → generate a report
/help           → user wants help or command list
/mgrtransfer    → transfer existing task to another department
/mgrreject      → reject a task with a reason
general_chat    → casual conversation, greetings only

========================================================
FEW-SHOT EXAMPLES
========================================================

--- /assign examples ---
Input:  ajay ko warehouse khali karne bolo
Output: {"intent":"/assign","worker_slug":"ajay","depart_slug":null,"reject_reason":null}

Input:  @rahul invoice bhejdo
Output: {"intent":"/assign","worker_slug":"@rahul","depart_slug":null,"reject_reason":null}

Input:  priya client ko call kare
Output: {"intent":"/assign","worker_slug":"priya","depart_slug":null,"reject_reason":null}

Input:  ajay complete the work
Output: {"intent":"/assign","worker_slug":"ajay","depart_slug":null,"reject_reason":null}

Input:  complete the work ajay
Output: {"intent":"/assign","worker_slug":"ajay","depart_slug":null,"reject_reason":null}

Input:  rahul ye task finish karo
Output: {"intent":"/assign","worker_slug":"rahul","depart_slug":null,"reject_reason":null}

--- /depart_assign examples ---
Input:  warehouse khali karo
Output: {"intent":"/depart_assign","worker_slug":null,"depart_slug":"operations","reject_reason":null}

Input:  invoice bhejo
Output: {"intent":"/depart_assign","worker_slug":null,"depart_slug":"sales","reject_reason":null}

Input:  server theek karo
Output: {"intent":"/depart_assign","worker_slug":null,"depart_slug":"it","reject_reason":null}

Input:  raw material order karo
Output: {"intent":"/depart_assign","worker_slug":null,"depart_slug":"purchase","reject_reason":null}

Input:  complete the dispatch work
Output: {"intent":"/depart_assign","worker_slug":null,"depart_slug":"operations","reject_reason":null}

--- /mgrassign examples ---
Input:  task 32 ajay ko do
Output: {"intent":"/mgrassign","worker_slug":"ajay","depart_slug":null,"reject_reason":null}

Input:  task 5 @rahul ko assign karo
Output: {"intent":"/mgrassign","worker_slug":"@rahul","depart_slug":null,"reject_reason":null}

Input:  id 4 priya ko de do
Output: {"intent":"/mgrassign","worker_slug":"priya","depart_slug":null,"reject_reason":null}

--- /mgrself examples ---
Input:  task 32 main karunga
Output: {"intent":"/mgrself","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  i will do task 8
Output: {"intent":"/mgrself","worker_slug":null,"depart_slug":null,"reject_reason":null}

--- /complete examples ---
Input:  ho gaya
Output: {"intent":"/complete","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  kar diya
Output: {"intent":"/complete","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  done
Output: {"intent":"/complete","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  task complete ho gaya
Output: {"intent":"/complete","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  dispatch done
Output: {"intent":"/complete","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  kaam khatam ho gaya
Output: {"intent":"/complete","worker_slug":null,"depart_slug":null,"reject_reason":null}

--- TRICKY: instruction vs completion ---
Input:  complete the work          (← instruction, no person named)
Output: {"intent":"/depart_assign","worker_slug":null,"depart_slug":"operations","reject_reason":null}

Input:  kaam complete karo         (← instruction)
Output: {"intent":"/depart_assign","worker_slug":null,"depart_slug":"operations","reject_reason":null}

Input:  complete kar diya          (← confirmed done)
Output: {"intent":"/complete","worker_slug":null,"depart_slug":null,"reject_reason":null}

--- /mgrtransfer examples ---
Input:  transfer task 12 to sales department
Output: {"intent":"/mgrtransfer","worker_slug":null,"depart_slug":"sales","reject_reason":null}

Input:  task 15 ko it department bhejo
Output: {"intent":"/mgrtransfer","worker_slug":null,"depart_slug":"it","reject_reason":null}

--- /mgrreject examples ---
Input:  reject task 12 - wrong department
Output: {"intent":"/mgrreject","worker_slug":null,"depart_slug":null,"reject_reason":"wrong department"}

Input:  task 15 reject karo, not our scope
Output: {"intent":"/mgrreject","worker_slug":null,"depart_slug":null,"reject_reason":"not our scope"}

--- /present examples ---
Input:  aa gaya hu
Output: {"intent":"/present","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  i am here
Output: {"intent":"/present","worker_slug":null,"depart_slug":null,"reject_reason":null}

--- /absent examples ---
Input:  aaj nahi aa paunga
Output: {"intent":"/absent","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  leave chahiye
Output: {"intent":"/absent","worker_slug":null,"depart_slug":null,"reject_reason":null}

--- general_chat examples ---
Input:  hello
Output: {"intent":"general_chat","worker_slug":null,"depart_slug":null,"reject_reason":null}

Input:  kaise ho
Output: {"intent":"general_chat","worker_slug":null,"depart_slug":null,"reject_reason":null}

========================================================
DEPARTMENT ROUTING
========================================================

operations : warehouse, dispatch, logistics, delivery, inventory, production, machine, packaging, loading, unloading
sales      : invoice, customer, client, quotation, payment, order
purchase   : vendor, supplier, procurement, raw material, buying, sourcing
it         : server, laptop, computer, software, internet, wifi, printer

========================================================
OUTPUT FORMAT
========================================================

Always return exactly:
{
  "intent": "<one of the valid intents>",
  "worker_slug": "<string or null>",
  "depart_slug": "<operations|sales|purchase|it|null>",
  "reject_reason": "<string or null>"
}

Rules:
- /assign      → worker_slug required, depart_slug null
- /depart_assign → depart_slug required, worker_slug null
- /mgrassign   → worker_slug required
- /mgrself     → worker_slug null
- /mgrtransfer → depart_slug required, worker_slug null
- /mgrreject   → reject_reason required if detectable
- all others   → both null unless explicitly present

NEVER return markdown. NEVER return explanations. ONLY return JSON.
"""