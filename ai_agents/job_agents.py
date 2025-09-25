from agents import Agent
from typing import List as _List

from models.models import JobPosting, JobInsights
from helpers.site_scraper import scrape_page_content
from helpers.web_searcher import serper_web_search
from helpers.job_emailer import send_shortlisted_jobs_email

# ---- Agents SDK strict enforcer ----
enforcer = Agent(
    name="JobsNormalizerIndia",
    instructions=(
        "Return ONLY a JSON array of JobPosting objects. "
        "Do not invent salary; infer tech_stack only if clearly evidenced in title/description."
    ),
    output_type=_List[JobPosting]
)

# ---- Agents SDK web scraper ----
job_scraper = Agent(
    name="JobScraperIndia",
    instructions=(
        "You are a helpful agent scraping the web for tech jobs based in India."
        "Use the tools provided to scrape the job websites as per the keywords provided and return ONLY a JSON array of JobPosting objects."
        "Do not invent salary; infer tech_stack only if clearly evidenced in title/description."
    ),
    tools=[scrape_page_content],
    output_type=_List[JobPosting]
)

# ---- Agents SDK web searcher ----
web_searcher = Agent(
    name="JobsWebSearcherIndia",
    instructions=(
        "You are a helpful agent searching the web for tech jobs based in India."
        "Use the tools provided to search the web as per the keywords provided and return ONLY a JSON array of JobPosting objects."
        "Do not invent salary; infer tech_stack only if clearly evidenced in title/description."
    ),
    tools=[serper_web_search],
    output_type=_List[JobPosting]
)

# ---- Agents SDK job emailer ----
job_emailer = Agent(
    name="JobsEmailerIndia",
    instructions=(
        "You are a helpful agent tasked with sending emails containing the listed jobs as an array of JobPosting objects."
        "Use the tools provided to send emails containing the listed jobs."
    ),
    tools=[send_shortlisted_jobs_email],
    handoff_description="An emailing agent"
)

# ---- Redefining the job agents as tools ----
enforcer_tool = enforcer.as_tool(tool_name="JobsNormalizerIndia", tool_description="Normalize Jobs")
job_scraper_tool = job_scraper.as_tool(tool_name="JobScraperIndia", tool_description="Scrape Jobs Sites")
web_searcher_tool = web_searcher.as_tool(tool_name="JobsWebSearcherIndia", tool_description="Search Jobs Sites")

# ---- Grouping the tools and handoffs ----
tools = [enforcer_tool, job_scraper_tool, web_searcher_tool]
handoffs = [job_emailer]

# ---- Agents SDK job manager ----
job_manager = Agent(
    name="JobManagerIndia",
    instructions=(
        "You are a helpful job agent manager. Your job is to find the best jobs that match the given keywords."
        "Use the three agent tools outputs to generate the most relevant jobs as an array of JobPosting objects."
        "Pass the listed jobs to the 'JobsEmailerIndia' agent along with displaying the output at the endpoint as a structured output."
        "Do not invent salary; infer tech_stack only if clearly evidenced in title/description."
    ),
    tools=tools,
    handoffs=handoffs,
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
