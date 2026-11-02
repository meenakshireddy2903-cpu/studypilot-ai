"""StudyPilot AI entry point. ADK looks for a variable named `root_agent` in this file."""
from google.adk.agents import LoopAgent, SequentialAgent
from .callbacks import present_final_answer, reset_pipeline_state
from .sub_agents.goal_analysis_agent import goal_analysis_agent
from .sub_agents.review_agent import review_agent
from .sub_agents.study_planner_agent import study_planner_agent
MAX_REVIEW_ROUNDS = 2
# Planner and Reviewer take turns: plan -> review -> (improved) plan -> review.
plan_review_loop = LoopAgent(
   name="plan_review_loop",
   description="Creates a study plan and reviews it, with at most two rounds.",
   sub_agents=[study_planner_agent, review_agent],
   max_iterations=MAX_REVIEW_ROUNDS,
)
# The main coordinator: runs each step once, in this exact order.
root_agent = SequentialAgent(
   name="studypilot_coordinator",
   description="Analyses the student's goals, plans and reviews a timetable, then presents it.",
   sub_agents=[goal_analysis_agent, plan_review_loop],
   before_agent_callback=reset_pipeline_state,
   after_agent_callback=present_final_answer,
)