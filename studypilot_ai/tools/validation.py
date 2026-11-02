"""Deterministic (pure Python) checks for a study plan. No AI is used in this file."""
import json
from datetime import date
TOLERANCE = 0.01  # allow tiny rounding differences, e.g. 2.9999 instead of 3.0
MIN_HOURS_PER_SUBJECT = 2.0  # below this, we warn that a subject is barely covered

def _as_dict(value):
   """Values in session state may be a dict or a JSON string. Always return a dict."""
   if isinstance(value, str):
       return json.loads(value)
   return value or {}

def _parse_date(text):
   """Turn 'YYYY-MM-DD' into a date object, or return None if missing or invalid."""
   try:
       return date.fromisoformat(text)
   except (TypeError, ValueError):
       return None

def validate_study_plan(requirements, plan):
   """Check a study plan against the student's requirements.
   Returns a dict with:
     is_valid          - True if there are no problems
     problems          - rule violations that MUST be fixed
     warnings          - things that look weak but are not strictly wrong
     hours_per_subject - total planned hours for each subject
   """
   requirements = _as_dict(requirements)
   plan = _as_dict(plan)
   problems = []
   warnings = []
   limit = requirements.get("daily_study_hours")
   start = _parse_date(requirements.get("start_date"))
   # Look up each subject by its lowercase name, so "maths" matches "Maths".
   names = {}
   deadlines = {}
   hours_per_subject = {}
   for subject in requirements.get("subjects", []):
       key = subject["name"].lower()
       names[key] = subject["name"]
       deadlines[key] = _parse_date(subject.get("deadline"))
       hours_per_subject[key] = 0.0
   seen_dates = set()
   for day in plan.get("daily_schedule", []):
       day_date = _parse_date(day.get("date"))
       if day_date is None:
           problems.append(f"Invalid date {day.get('date')!r}. Dates must be YYYY-MM-DD.")
           continue
       if day_date in seen_dates:
           problems.append(f"{day_date} appears more than once in the schedule.")
       seen_dates.add(day_date)
       if start and day_date < start:
           problems.append(f"{day_date} is before the start date {start}.")
       # Rule 1: daily hours must not exceed the student's limit.
       total = round(sum(s.get("hours", 0) for s in day.get("sessions", [])), 2)
       if limit is not None and total > limit + TOLERANCE:
           problems.append(f"{day_date}: {total} hours planned, but the limit is {limit} hours per day.")
       for session in day.get("sessions", []):
           key = session.get("subject", "").lower()
           if key not in deadlines:
               warnings.append(f"{day_date}: '{session.get('subject')}' is not one of the student's subjects.")
               continue
           hours_per_subject[key] += session.get("hours", 0)
           # Rule 2: no study for a subject on or after its deadline.
           deadline = deadlines[key]
           if deadline and day_date >= deadline:
               problems.append(f"{day_date}: {names[key]} is scheduled on or after its deadline {deadline}.")
   for key, deadline in deadlines.items():
       # Rule 3: the deadline must leave time to prepare.
       if start and deadline and deadline <= start:
           problems.append(f"{names[key]}: deadline {deadline} is not after the start date {start}, so there is no time to prepare.")
       # Rule 4: every subject must be covered.
       if hours_per_subject[key] == 0:
           problems.append(f"{names[key]} is not covered in the plan.")
       elif hours_per_subject[key] < MIN_HOURS_PER_SUBJECT:
           warnings.append(f"{names[key]} gets only {hours_per_subject[key]} hours in total, which may not be enough.")
   return {
       "is_valid": len(problems) == 0,
       "problems": problems,
       "warnings": warnings,
       "hours_per_subject": {names[k]: round(v, 2) for k, v in hours_per_subject.items()},
   }