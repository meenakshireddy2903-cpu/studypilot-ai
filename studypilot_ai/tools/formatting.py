"""Turns the pipeline's results (in session state) into a readable answer for the student.
Pure Python, no AI, so it can be tested without calling Gemini.
"""
import json
from datetime import date
from .validation import validate_study_plan

def to_dict(value):
   """State values may be a dict, a JSON string, an empty string or None. Always return a dict."""
   if isinstance(value, dict):
       return value
   if isinstance(value, str) and value.strip():
       try:
           return json.loads(value)
       except json.JSONDecodeError:
           return {}
   return {}

def _weekday(text):
   """'2026-10-30' -> 'Fri'. Returns '' if the date is invalid."""
   try:
       return date.fromisoformat(text).strftime("%a")
   except (TypeError, ValueError):
       return ""

def format_final_answer(state):
   """Build the final message from session state."""
   requirements = to_dict(state.get("student_requirements"))
   # Case 1: the student did not give enough information.
   if not requirements.get("is_complete", False):
       questions = requirements.get("missing_information") or [
           "Which subjects or skills do you want to study?",
           "What are your deadlines or exam dates?",
           "How many hours can you study per day?",
       ]
       lines = ["I need a little more information before I can build your study plan:", ""]
       lines += [f"- {q}" for q in questions]
       return "\n".join(lines)
   # Case 2: no plan was produced at all.
   plan = to_dict(state.get("final_plan"))
   if not plan.get("daily_schedule"):
       return "Sorry, I could not create a study plan this time. Please try again."
   # Case 3: we have a plan. Re-check it with Python so the numbers shown are always correct.
   report = validate_study_plan(requirements, plan)
   rounds = state.get("review_rounds", 0)
   lines = [f"# {plan.get('plan_title', 'Your Study Plan')}", ""]
   if state.get("plan_approved"):
       lines.append(f"Status: APPROVED by the Review Agent (review rounds: {rounds}).")
   else:
       lines.append(f"Status: NOT fully approved after {rounds} review rounds. Remaining issues:")
       issues = list(dict.fromkeys(report["problems"] + list(state.get("final_problems") or [])))
       lines += [f"- {issue}" for issue in issues] or ["- The reviewer asked for changes that were not completed."]
   lines.append("")
   limit = requirements.get("daily_study_hours")
   per_subject = ", ".join(f"{name} {hours} h" for name, hours in report["hours_per_subject"].items())
   lines += [f"Daily limit: {limit} h | Total hours per subject: {per_subject}", ""]
   lines += ["## Day-by-day timetable", ""]
   for day in plan["daily_schedule"]:
       sessions = day.get("sessions", [])
       total = round(sum(s.get("hours", 0) for s in sessions), 2)
       lines.append(f"### {day.get('date')} ({_weekday(day.get('date'))}) - {total} h")
       if not sessions:
           lines.append("- Rest day")
       for s in sessions:
           lines.append(f"- {s.get('hours')} h | {s.get('activity')} | {s.get('subject')}: {s.get('topic')}")
       lines.append("")
   if plan.get("weekly_summary"):
       lines += ["## Weekly overview", ""] + [f"- {w}" for w in plan["weekly_summary"]] + [""]
   if plan.get("notes"):
       lines += ["## Study tips", ""] + [f"- {n}" for n in plan["notes"]] + [""]
   if state.get("final_summary"):
       lines += ["## Reviewer's note", "", state["final_summary"]]
   return "\n".join(lines).strip()