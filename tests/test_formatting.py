"""Tests for the final answer shown to the student. No Gemini calls."""
from studypilot_ai.tools.formatting import format_final_answer, to_dict

def test_to_dict_handles_all_state_value_types():
   assert to_dict({"a": 1}) == {"a": 1}
   assert to_dict('{"a": 1}') == {"a": 1}
   assert to_dict("") == {}
   assert to_dict(None) == {}
   assert to_dict("not json") == {}

def test_scenario_6_incomplete_information_shows_questions():
   state = {"student_requirements": {
       "is_complete": False,
       "missing_information": ["How many hours can you study per day?"],
   }}
   text = format_final_answer(state)
   assert "I need a little more information" in text
   assert "- How many hours can you study per day?" in text

def test_incomplete_without_questions_uses_default_questions():
   text = format_final_answer({"student_requirements": ""})
   assert "How many hours can you study per day?" in text

def test_approved_plan_shows_timetable(exam_requirements, valid_plan):
   state = {
       "student_requirements": exam_requirements,
       "final_plan": valid_plan,
       "plan_approved": True,
       "review_rounds": 1,
       "final_summary": "Looks great!",
   }
   text = format_final_answer(state)
   assert text.startswith("# Maths and Physics Plan")
   assert "Status: APPROVED by the Review Agent (review rounds: 1)." in text
   assert "### 2026-10-30 (Fri) - 3.0 h" in text
   assert "Maths 2.5 h, Physics 3.5 h" in text
   assert "## Reviewer's note" in text

def test_unapproved_plan_lists_remaining_issues(exam_requirements, valid_plan):
   valid_plan["daily_schedule"][0]["sessions"][0]["hours"] = 3.0  # makes that day 4.5 h
   state = {
       "student_requirements": exam_requirements,
       "final_plan": valid_plan,
       "plan_approved": False,
       "review_rounds": 2,
       "final_problems": ["No revision before the Maths exam."],
   }
   text = format_final_answer(state)
   assert "NOT fully approved after 2 review rounds" in text
   assert "4.5 hours planned" in text
   assert "No revision before the Maths exam." in text

def test_rest_day_is_shown(exam_requirements, valid_plan):
   valid_plan["daily_schedule"].append({"date": "2026-11-01", "sessions": []})
   text = format_final_answer({
       "student_requirements": exam_requirements, "final_plan": valid_plan, "plan_approved": True,
   })
   assert "- Rest day" in text

def test_missing_plan_gives_polite_message(exam_requirements):
   text = format_final_answer({"student_requirements": exam_requirements, "final_plan": ""})
   assert "could not create a study plan" in text