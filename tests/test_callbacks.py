"""Tests for the workflow callbacks, using a fake callback_context. No ADK runner, no Gemini."""
from studypilot_ai.callbacks import (
   present_final_answer,
   record_review_outcome,
   reset_pipeline_state,
   skip_planner_if_not_needed,
   skip_review_if_not_needed,
)
from studypilot_ai.schemas import ReviewResult, StudyPlan

# ---------- reset_pipeline_state ----------
def test_reset_clears_results_from_an_earlier_request(make_context):
   ctx = make_context({"plan_approved": True, "final_plan": {"x": 1}, "review_rounds": 2})
   assert reset_pipeline_state(ctx) is None
   assert ctx.state["plan_approved"] is False
   assert ctx.state["final_plan"] == ""
   assert ctx.state["review_rounds"] == 0

# ---------- skip callbacks ----------
def test_planner_runs_when_requirements_complete(make_context, exam_requirements):
   ctx = make_context({"student_requirements": exam_requirements})
   assert skip_planner_if_not_needed(ctx) is None

def test_planner_skipped_when_information_incomplete(make_context):
   ctx = make_context({"student_requirements": {"is_complete": False}})
   result = skip_planner_if_not_needed(ctx)
   placeholder = StudyPlan.model_validate_json(result.parts[0].text)  # must be valid JSON
   assert placeholder.daily_schedule == []
   assert "more information" in placeholder.plan_title

def test_planner_skipped_when_plan_already_approved(make_context, exam_requirements):
   ctx = make_context({"student_requirements": exam_requirements, "plan_approved": True})
   result = skip_planner_if_not_needed(ctx)
   assert "already approved" in StudyPlan.model_validate_json(result.parts[0].text).plan_title

def test_review_skip_placeholder_matches_schema(make_context, exam_requirements):
   ctx = make_context({"student_requirements": exam_requirements, "plan_approved": True})
   review = ReviewResult.model_validate_json(skip_review_if_not_needed(ctx).parts[0].text)
   assert review.approved is True

# ---------- record_review_outcome: Python makes the final decision ----------
def test_approved_only_when_gemini_and_python_agree(make_context, exam_requirements, valid_plan):
   ctx = make_context({
       "student_requirements": exam_requirements,
       "draft_plan": valid_plan,
       "review_feedback": {"approved": True, "summary_for_student": "Good plan"},
       "validation_report": {"is_valid": True},
       "review_rounds": 0,
   })
   record_review_outcome(ctx)
   assert ctx.state["plan_approved"] is True
   assert ctx.state["final_plan"] == valid_plan
   assert ctx.state["review_rounds"] == 1

def test_not_approved_if_python_finds_problems(make_context, exam_requirements, valid_plan):
   ctx = make_context({
       "student_requirements": exam_requirements,
       "draft_plan": valid_plan,
       "review_feedback": {"approved": True},          # Gemini says yes...
       "validation_report": {"is_valid": False},        # ...but Python says no
   })
   record_review_outcome(ctx)
   assert ctx.state["plan_approved"] is False

def test_approved_plan_is_frozen(make_context, exam_requirements, valid_plan):
   ctx = make_context({
       "student_requirements": exam_requirements,
       "plan_approved": True,
       "final_plan": valid_plan,
       "draft_plan": {"plan_title": "A different, later plan"},
   })
   record_review_outcome(ctx)
   assert ctx.state["final_plan"] == valid_plan

def test_nothing_recorded_when_information_incomplete(make_context):
   ctx = make_context({"student_requirements": {"is_complete": False}, "review_rounds": 0})
   record_review_outcome(ctx)
   assert ctx.state["review_rounds"] == 0

# ---------- present_final_answer ----------
def test_final_answer_is_returned_as_a_message(make_context, exam_requirements, valid_plan):
   ctx = make_context({
       "student_requirements": exam_requirements, "final_plan": valid_plan, "plan_approved": True,
   })
   message = present_final_answer(ctx)
   assert message.role == "model"
   assert "Status: APPROVED" in message.parts[0].text