"""Workflow callbacks: plain Python functions that ADK runs at fixed moments in the pipeline."""
from google.genai import types
from .schemas import ReviewResult, StudyPlan
from .tools.formatting import format_final_answer, to_dict

def _as_content(text):
   """Wrap text in ADK's message format."""
   return types.Content(role="model", parts=[types.Part(text=text)])

def _skip_reason(state):
   """Return why the Planner/Reviewer should be skipped, or None if it should run."""
   if not to_dict(state.get("student_requirements")).get("is_complete", False):
       return "Skipped: more information is needed from the student."
   if state.get("plan_approved"):
       return "Skipped: the plan is already approved."
   return None

def skip_planner_if_not_needed(callback_context):
   """Before the Planner. To skip, return a placeholder that still matches the StudyPlan schema."""
   reason = _skip_reason(callback_context.state.to_dict())
   if reason is None:
       return None  # run the Planner normally
   placeholder = StudyPlan(plan_title=reason, daily_schedule=[], notes=[reason])
   return _as_content(placeholder.model_dump_json())

def skip_review_if_not_needed(callback_context):
   """Before the Reviewer. To skip, return a placeholder that still matches the ReviewResult schema."""
   state = callback_context.state.to_dict()
   reason = _skip_reason(state)
   if reason is None:
       return None  # run the Reviewer normally
   placeholder = ReviewResult(approved=bool(state.get("plan_approved")), summary_for_student=reason)
   return _as_content(placeholder.model_dump_json())

def reset_pipeline_state(callback_context):
   """Runs before the whole pipeline. Clears results left over from an earlier request."""
   callback_context.state["draft_plan"] = ""
   callback_context.state["review_feedback"] = ""
   callback_context.state["validation_report"] = ""
   callback_context.state["plan_approved"] = False
   callback_context.state["review_rounds"] = 0
   callback_context.state["final_plan"] = ""
   callback_context.state["final_summary"] = ""
   callback_context.state["final_problems"] = []
   return None

def record_review_outcome(callback_context):
   """Runs after each Review Agent turn. Python makes the final approval decision."""
   state = callback_context.state.to_dict()
   if state.get("plan_approved"):
       return None  # an earlier round already approved a plan, so keep that one
   if not to_dict(state.get("student_requirements")).get("is_complete", False):
      return None
   review = to_dict(state.get("review_feedback"))
   report = to_dict(state.get("validation_report"))
   approved = bool(review.get("approved")) and bool(report.get("is_valid"))
   callback_context.state["plan_approved"] = approved
   callback_context.state["review_rounds"] = state.get("review_rounds", 0) + 1
   callback_context.state["final_plan"] = state.get("draft_plan")
   callback_context.state["final_summary"] = review.get("summary_for_student", "")
   callback_context.state["final_problems"] = review.get("problems", [])
   return None

def present_final_answer(callback_context):
   """Runs after the whole pipeline. Returns a readable timetable as the final message."""
   text = format_final_answer(callback_context.state.to_dict())
   return types.Content(role="model", parts=[types.Part(text=text)])