from agents import Agent
from typing import List as _List

from models.models import JobPosting, JobInsights

# ---- Agents SDK strict enforcer ----
enforcer = Agent(
    name="JobsNormalizerIndia",
    instructions=(
        "Return ONLY a JSON array of JobPosting objects. "
        "Do not invent salary; infer tech_stack only if clearly evidenced in title/description."
    ),
    handoff_description="A job search assistant",
    output_type=_List[JobPosting]
)

# ---- Agents SDK tech stack researcher ----
tech_stack_researcher = Agent(
    name="TechStackResearcherIndia",
    instructions=(
        "You are an insightful and helpful researcher."
        "Given a JSON array of JobPosting objects, use the tools provided to search the web and create a JobInsights object."
        "Provide a short summary of the skills required in the summary field, and the list of the required skills in the skill_set field"
    ),
    handoff_description="A job insights researcher",
    output_type=JobInsights
)
