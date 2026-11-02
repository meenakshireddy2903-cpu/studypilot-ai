"""Agent 2: Study Planner Agent - builds a day-by-day timetable from the analysed requirements."""
from google.adk.agents import LlmAgent
from google.genai import types
from ..config import MODEL_NAME, generation_config
from ..schemas import StudyPlan
from ..callbacks import skip_planner_if_not_needed
PLANNER_INSTRUCTION = """
You are the Study Planner Agent of StudyPilot AI.
Student requirements (prepared by the Goal Analysis Agent):
{student_requirements}
Feedback from the Review Agent on your previous plan (empty on the first attempt):
{review_feedback?}
Create a realistic, personalised study timetable.
Rules:
1. If is_complete is false, do not create a plan. Return an empty daily_schedule
  and copy each question from missing_information into notes.
2. Start on start_date. Each subject's study must finish before its deadline.
  Never schedule a subject on or after its deadline.
3. The total hours of all sessions on one day must never exceed daily_study_hours.
4. Give more time to high-priority subjects, weaker skill levels and nearer deadlines.
5. Use these activities: "learn" for new material, "practice" for exercises,
  "revision" for reviewing, and "mock_test" shortly before a deadline.
  Put revision in the last days before each deadline.
6. Use sessions of 0.5 to 2 hours. Make one day per week lighter, about half the usual hours.
7. Adapt to the use_case:
  - exam_preparation: cover the syllabus first, then revision and mock tests before each exam.
  - placement_preparation: rotate aptitude, technical topics and interview practice.
  - learning_roadmap: order topics from basics to advanced, with practice after each topic.
8. If the period is longer than 28 days, give daily_schedule for the first 28 days only,
  and describe the remaining weeks in weekly_summary.
9. In notes, include short advice on breaks, for example a 10-minute break after each hour.
10. If review feedback is given above, fix every problem it mentions.
"""
study_planner_agent = LlmAgent(
   name="study_planner_agent",
   model=MODEL_NAME,
   description="Creates a day-by-day study timetable from the student's analysed requirements.",
   instruction=PLANNER_INSTRUCTION,
   before_agent_callback=skip_planner_if_not_needed,
   output_schema=StudyPlan,
   output_key="draft_plan",
   generate_content_config=types.GenerateContentConfig(temperature=0.3),
)