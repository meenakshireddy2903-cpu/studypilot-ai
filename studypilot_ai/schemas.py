"""Data shapes (schemas) that StudyPilot agents must produce."""
from typing import Literal, Optional
from pydantic import BaseModel, Field

class SubjectRequirement(BaseModel):
   """One subject or skill area the student wants to study."""
   name: str = Field(description="Subject name, e.g. 'Mathematics' or 'SQL'.")
   topics: list[str] = Field(
       default_factory=list,
       description="Specific topics the student mentioned. Empty list if none.",
   )
   skill_level: Literal["beginner", "intermediate", "advanced", "unknown"] = Field(
       description="The student's current level in this subject."
   )
   deadline: Optional[str] = Field(
       default=None,
       description="Exam date or target finish date as YYYY-MM-DD, or null if not given.",
   )
   priority: Literal["high", "medium", "low"] = Field(
       description="How urgent or important this subject is."
   )

class StudentRequirements(BaseModel):
   """Everything the Goal Analysis Agent understood from the student's message."""
   use_case: Literal[
       "exam_preparation", "placement_preparation", "learning_roadmap", "unknown"
   ] = Field(description="Which kind of plan the student needs.")
   goal_summary: str = Field(description="One-sentence summary of the student's goal.")
   subjects: list[SubjectRequirement] = Field(description="All subjects or skills to cover.")
   daily_study_hours: Optional[float] = Field(
       default=None,
       description="Study hours available per day, or null if the student did not say.",
   )
   start_date: str = Field(description="Date the plan starts, as YYYY-MM-DD.")
   missing_information: list[str] = Field(
       default_factory=list,
       description="Critical details the student did not give, each written as a short question.",
   )
   is_complete: bool = Field(
       description="True only if subjects, daily hours and a deadline or target date are known."
   )

class StudySession(BaseModel):
   """One block of study time on one day."""
   subject: str = Field(description="Subject name, exactly as in the student requirements.")
   topic: str = Field(description="What to study in this session.")
   activity: Literal["learn", "practice", "revision", "mock_test"] = Field(
       description="Type of session."
   )
   hours: float = Field(description="Length of the session in hours, e.g. 1.5.")

class DayPlan(BaseModel):
   """All study sessions planned for one date."""
   date: str = Field(description="The date, as YYYY-MM-DD.")
   sessions: list[StudySession] = Field(
       default_factory=list,
       description="Study sessions on this day. Empty list for a rest day.",
   )

class StudyPlan(BaseModel):
   """The timetable produced by the Study Planner Agent."""
   plan_title: str = Field(description="A short title for the plan.")
   daily_schedule: list[DayPlan] = Field(description="Day-by-day schedule, in date order.")
   weekly_summary: list[str] = Field(
       default_factory=list,
       description="One line per week describing that week's focus.",
   )
   notes: list[str] = Field(
       default_factory=list,
       description="Advice for the student, such as when to take breaks.",
   )


class ReviewResult(BaseModel):
   """The Review Agent's verdict on a draft study plan."""
   approved: bool = Field(
       description="True only if the plan has no problems that must be fixed."
   )
   problems: list[str] = Field(
       default_factory=list,
       description="Every problem found, from the Python report and from your own review.",
   )
   feedback_for_planner: str = Field(
       default="",
       description="Specific instructions for the Study Planner on what to change. Empty if approved.",
   )
   summary_for_student: str = Field(
       description="Two or three friendly sentences for the student about the plan."
   )