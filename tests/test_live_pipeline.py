"""Optional LIVE tests: run the real multi-agent pipeline with Gemini.
They use API quota (about 4 requests), so they are skipped by default.
Run them on purpose with:  python -m pytest -m live -v
"""
import asyncio
import os
from datetime import date, timedelta
import pytest
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from studypilot_ai.agent import root_agent  # importing the agents also loads .env (via config.py)
from studypilot_ai.tools.formatting import to_dict
from studypilot_ai.tools.validation import validate_study_plan
pytestmark = pytest.mark.live  # every test in this file is a "live" test
APP_NAME = "studypilot_live_test"
USER_ID = "live_tester"

async def _run_pipeline(message_text):
   """Send one message through the full pipeline. Returns (final answer text, session state)."""
   session_service = InMemorySessionService()
   session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
   runner = Runner(agent=root_agent, app_name=APP_NAME, session_service=session_service)
   message = types.Content(role="user", parts=[types.Part(text=message_text)])
   final_text = ""
   async for event in runner.run_async(user_id=USER_ID, session_id=session.id, new_message=message):
       # The coordinator's message (from present_final_answer) is the student's final answer.
       if event.author == root_agent.name and event.content and event.content.parts:
           final_text = event.content.parts[0].text or final_text
   updated = await session_service.get_session(
       app_name=APP_NAME, user_id=USER_ID, session_id=session.id
   )
   return final_text, updated.state

def run_pipeline(message_text):
   """Run the pipeline, skipping (not failing) if Gemini is busy or out of quota."""
   if not os.getenv("GOOGLE_API_KEY"):
       pytest.skip("GOOGLE_API_KEY is not set")
   try:
       return asyncio.run(_run_pipeline(message_text))
   except Exception as error:
       busy_signs = ("429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE")
       if any(sign in str(error) for sign in busy_signs):
           pytest.skip(f"Gemini is busy or out of quota, try again later: {type(error).__name__}")
       raise  # any other error is a real failure

def test_live_exam_request_produces_a_valid_plan():
   maths_exam = date.today() + timedelta(days=7)
   physics_exam = date.today() + timedelta(days=10)
   text, state = run_pipeline(
       f"I have exams in Maths on {maths_exam.isoformat()} and Physics on "
       f"{physics_exam.isoformat()}. I am average in Maths and weak in Physics. "
       "I can study 3 hours a day."
   )
   requirements = to_dict(state.get("student_requirements"))
   assert requirements.get("is_complete") is True
   assert requirements.get("use_case") == "exam_preparation"
   assert "Status:" in text  # the final, formatted answer was produced
   plan = to_dict(state.get("final_plan"))
   assert plan.get("daily_schedule"), "a non-empty timetable should be saved in final_plan"
   if state.get("plan_approved"):
       # Our key safety rule: an approved plan must pass the Python checks.
       assert validate_study_plan(requirements, plan)["is_valid"] is True

def test_live_incomplete_request_asks_questions():
   text, state = run_pipeline("I want to learn Python.")
   assert to_dict(state.get("student_requirements")).get("is_complete") is False
   assert "I need a little more information" in text
   assert not to_dict(state.get("final_plan")).get("daily_schedule")  # no plan was made