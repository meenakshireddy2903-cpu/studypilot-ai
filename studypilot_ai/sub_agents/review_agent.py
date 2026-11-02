"""Agent 3: Review Agent - checks the draft plan with Python, then judges its quality."""
from google.adk.agents import LlmAgent
from google.genai import types
from ..config import MODEL_NAME, generation_config
from ..schemas import ReviewResult
from ..tools.validation import validate_study_plan
from ..callbacks import record_review_outcome, skip_review_if_not_needed

def run_plan_validation(callback_context):
   """Runs automatically before the Review Agent. Saves a Python validation report to state."""
   skip = skip_review_if_not_needed(callback_context)
   if skip is not None:
      return skip
   state = callback_context.state.to_dict()
   report = validate_study_plan(
       state.get("student_requirements"),
       state.get("draft_plan"),
   )
   callback_context.state["validation_report"] = report
   return None  # None means: continue and run the Review Agent normally

REVIEW_INSTRUCTION = """
You are the Review Agent of StudyPilot AI. You check study timetables before the student sees them.
Student requirements:
{student_requirements}
Draft study plan from the Study Planner Agent:
{draft_plan}
Validation report calculated by Python. It is always correct. Trust it over your own arithmetic:
{validation_report}
Your task:
1. Copy every item from the report's problems list into your problems list.
2. Then check the things Python cannot judge:
  - Do high-priority and weak subjects get enough time?
  - Is there revision or a mock test before each deadline?
  - Is there one lighter day each week?
  - Does the plan suit the use_case?
  Add only clear, significant issues. Small style preferences are not problems.
3. Mention a warning from the report only if it really matters for the student.
4. approved must be false if the report's is_valid is false.
  Otherwise set approved to true, unless you found a significant issue in step 2.
5. feedback_for_planner: if not approved, give specific instructions that name the dates and
  subjects to change. If approved, leave it empty.
6. summary_for_student: two or three friendly sentences about the plan.
Never do arithmetic yourself. Use the numbers in the validation report.
"""
review_agent = LlmAgent(
   name="review_agent",
   model=MODEL_NAME,
   description="Reviews the draft study plan using Python checks and approves it or gives feedback.",
   instruction=REVIEW_INSTRUCTION,
   before_agent_callback=run_plan_validation,
   after_agent_callback=record_review_outcome,
   output_schema=ReviewResult,
   output_key="review_feedback",
   generate_content_config=generation_config(0.2),
)