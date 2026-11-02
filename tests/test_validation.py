"""Tests for the deterministic validation rules. No Gemini calls."""
import json
from studypilot_ai.tools.validation import validate_study_plan

def session(subject, hours, activity="learn"):
   """Small helper to build one study session."""
   return {"subject": subject, "topic": "Topic", "activity": activity, "hours": hours}

# ---------- Basic rules ----------
def test_valid_plan_has_no_problems(exam_requirements, valid_plan):
   report = validate_study_plan(exam_requirements, valid_plan)
   assert report["is_valid"] is True
   assert report["problems"] == []
   assert report["hours_per_subject"] == {"Maths": 2.5, "Physics": 3.5}

def test_day_over_the_daily_limit_is_a_problem(exam_requirements):
   plan = {"daily_schedule": [
       {"date": "2026-10-30", "sessions": [session("Maths", 2.0), session("Physics", 2.0)]},
   ]}
   report = validate_study_plan(exam_requirements, plan)
   assert report["is_valid"] is False
   assert any("4.0 hours planned" in p for p in report["problems"])

def test_small_rounding_difference_is_allowed(exam_requirements):
   plan = {"daily_schedule": [
       {"date": "2026-10-30", "sessions": [session("Maths", 1.1), session("Physics", 1.9)]},
   ]}
   report = validate_study_plan(exam_requirements, plan)
   assert not any("hours planned" in p for p in report["problems"])

def test_study_on_or_after_deadline_is_a_problem(exam_requirements, valid_plan):
   valid_plan["daily_schedule"].append(
       {"date": "2026-11-06", "sessions": [session("Maths", 1.0)]}  # the Maths exam day
   )
   report = validate_study_plan(exam_requirements, valid_plan)
   assert any("Maths is scheduled on or after its deadline" in p for p in report["problems"])

def test_missing_subject_is_a_problem(exam_requirements):
   plan = {"daily_schedule": [{"date": "2026-10-30", "sessions": [session("Physics", 3.0)]}]}
   report = validate_study_plan(exam_requirements, plan)
   assert "Maths is not covered in the plan." in report["problems"]

def test_duplicate_and_invalid_dates_are_problems(exam_requirements, valid_plan):
   valid_plan["daily_schedule"].append({"date": "2026-10-30", "sessions": []})
   valid_plan["daily_schedule"].append({"date": "6th Nov", "sessions": []})
   report = validate_study_plan(exam_requirements, valid_plan)
   assert any("appears more than once" in p for p in report["problems"])
   assert any("Invalid date" in p for p in report["problems"])

def test_unknown_subject_name_is_a_warning(exam_requirements, valid_plan):
   valid_plan["daily_schedule"][0]["sessions"].append(session("Mathematics", 0.0))
   report = validate_study_plan(exam_requirements, valid_plan)
   assert any("'Mathematics' is not one of the student's subjects" in w for w in report["warnings"])

def test_subject_names_match_case_insensitively(exam_requirements, valid_plan):
   valid_plan["daily_schedule"][0]["sessions"][0]["subject"] = "maths"
   report = validate_study_plan(exam_requirements, valid_plan)
   assert report["is_valid"] is True

def test_accepts_json_strings_from_state(exam_requirements, valid_plan):
   report = validate_study_plan(json.dumps(exam_requirements), json.dumps(valid_plan))
   assert report["is_valid"] is True

# ---------- The six project scenarios (hand-made data, no Gemini) ----------
def test_scenario_1_three_exams():
   requirements = {
       "subjects": [
           {"name": "Maths", "deadline": "2026-11-20"},
           {"name": "Physics", "deadline": "2026-11-25"},
           {"name": "Chemistry", "deadline": "2026-12-01"},
       ],
       "daily_study_hours": 4, "start_date": "2026-10-30",
   }
   plan = {"daily_schedule": [
       {"date": "2026-10-30", "sessions": [session("Maths", 2), session("Physics", 2)]},
       {"date": "2026-10-31", "sessions": [session("Chemistry", 2), session("Physics", 2)]},
       {"date": "2026-11-01", "sessions": [session("Maths", 1), session("Chemistry", 1)]},
   ]}
   report = validate_study_plan(requirements, plan)
   assert report["is_valid"] is True
   assert report["hours_per_subject"] == {"Maths": 3.0, "Physics": 4.0, "Chemistry": 3.0}

def test_scenario_2_placement_preparation():
   subjects = ["Python", "SQL", "Aptitude", "Technical Interview", "HR Interview"]
   requirements = {
       "subjects": [{"name": s, "deadline": "2026-12-15"} for s in subjects],
       "daily_study_hours": 5, "start_date": "2026-10-30",
   }
   plan = {"daily_schedule": [
       {"date": "2026-10-30", "sessions": [session("Python", 2), session("SQL", 2), session("Aptitude", 1)]},
       {"date": "2026-10-31", "sessions": [session("Technical Interview", 2.5), session("HR Interview", 2.5)]},
   ]}
   report = validate_study_plan(requirements, plan)
   assert report["is_valid"] is True

def test_scenario_3_python_from_scratch_roadmap():
   requirements = {
       "subjects": [{"name": "Python", "skill_level": "beginner", "deadline": "2026-12-31"}],
       "daily_study_hours": 2, "start_date": "2026-10-30",
   }
   plan = {"daily_schedule": [
       {"date": f"2026-11-0{d}", "sessions": [session("Python", 2, "learn")]} for d in range(1, 8)
   ]}
   report = validate_study_plan(requirements, plan)
   assert report["is_valid"] is True
   assert report["hours_per_subject"] == {"Python": 14.0}

def test_scenario_4_only_two_hours_per_day():
   requirements = {
       "subjects": [{"name": "Maths", "deadline": "2026-11-10"}],
       "daily_study_hours": 2, "start_date": "2026-10-30",
   }
   ok = {"daily_schedule": [{"date": "2026-10-30", "sessions": [session("Maths", 2)]}]}
   too_much = {"daily_schedule": [{"date": "2026-10-30", "sessions": [session("Maths", 2.5)]}]}
   assert validate_study_plan(requirements, ok)["is_valid"] is True
   assert validate_study_plan(requirements, too_much)["is_valid"] is False

def test_scenario_5_unrealistic_deadline():
   requirements = {
       "subjects": [{"name": "Maths", "deadline": "2026-10-30"}],  # exam is TODAY
       "daily_study_hours": 3, "start_date": "2026-10-30",
   }
   report = validate_study_plan(requirements, {"daily_schedule": []})
   assert report["is_valid"] is False
   assert any("no time to prepare" in p for p in report["problems"])

def test_scenario_5b_very_little_time_gives_a_warning():
   requirements = {
       "subjects": [{"name": "Maths", "deadline": "2026-10-31"}],  # exam TOMORROW
       "daily_study_hours": 1, "start_date": "2026-10-30",
   }
   plan = {"daily_schedule": [{"date": "2026-10-30", "sessions": [session("Maths", 1)]}]}
   report = validate_study_plan(requirements, plan)
   assert report["is_valid"] is True
   assert any("may not be enough" in w for w in report["warnings"])