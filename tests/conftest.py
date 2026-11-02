"""Shared test helpers. pytest loads this file automatically."""
import pytest

class FakeState(dict):
   """A stand-in for ADK's session state: a normal dict that also has to_dict()."""
   def to_dict(self):
       return dict(self)

class FakeCallbackContext:
   """A stand-in for ADK's callback_context. Our callbacks only use .state."""
   def __init__(self, state=None):
       self.state = FakeState(state or {})

@pytest.fixture
def make_context():
   """Lets a test create a fake callback_context: make_context({...state...})."""
   return FakeCallbackContext

@pytest.fixture
def exam_requirements():
   """Two exams, 3 hours per day - the example we used throughout the project."""
   return {
       "use_case": "exam_preparation",
       "subjects": [
           {"name": "Maths", "skill_level": "intermediate", "deadline": "2026-11-06", "priority": "medium"},
           {"name": "Physics", "skill_level": "beginner", "deadline": "2026-11-09", "priority": "high"},
       ],
       "daily_study_hours": 3,
       "start_date": "2026-10-30",
       "missing_information": [],
       "is_complete": True,
   }

@pytest.fixture
def valid_plan():
   """A small plan that follows every rule for exam_requirements."""
   return {
       "plan_title": "Maths and Physics Plan",
       "daily_schedule": [
           {"date": "2026-10-30", "sessions": [
               {"subject": "Maths", "topic": "Algebra", "activity": "learn", "hours": 1.5},
               {"subject": "Physics", "topic": "Mechanics", "activity": "learn", "hours": 1.5},
           ]},
           {"date": "2026-10-31", "sessions": [
               {"subject": "Maths", "topic": "Calculus", "activity": "practice", "hours": 1.0},
               {"subject": "Physics", "topic": "Optics", "activity": "learn", "hours": 2.0},
           ]},
       ],
       "weekly_summary": ["Week 1: basics"],
       "notes": ["Take a 10-minute break every hour."],
   }