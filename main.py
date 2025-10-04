from __future__ import annotations

import asyncio
import logging
from typing import List, Optional
import json
import yaml
import os
import certifi
from bson import ObjectId
from dotenv import load_dotenv
from pathlib import Path
from agents import Runner
from flask_swagger_ui import get_swaggerui_blueprint

from flask import Flask, jsonify, request
from flask_cors import CORS
from pymongo import MongoClient

# ---- Agents ----
from ai_agents.job_agents import job_manager, tech_stack_researcher

# ---- Schema ----
from models.models import JobPosting, JobInsights

# ---- Providers (async) ----
from providers.providers_amazon import fetch_amazon_india
from providers.providers_workday import fetch_workday_jobs
from providers.providers_netflix import fetch_netflix_positions

# ---- Normalizers (sync) ----
from normalizers.normalize_india import norm_workday, norm_netflix, normalize_amazon_india

# -----------------------------------------------------------------------------
# App + logging
# -----------------------------------------------------------------------------
app = Flask(__name__)
CORS(app)

# -----------------------------------------------------------------------------
# Environment variables load
# -----------------------------------------------------------------------------
load_dotenv()
mongo_user = os.getenv("MONGODB_USER")
mongo_password = os.getenv("MONGODB_PASSWORD")
mongo_host = os.getenv("MONGODB_HOST")
mongo_db = os.getenv("MONGODB_DB")

# -----------------------------------------------------------------------------
# MongoDB initialize
# -----------------------------------------------------------------------------
uri = f"mongodb+srv://{mongo_user}:{mongo_password}@{mongo_host}/?retryWrites=true&w=majority&appName={mongo_db}"
client = MongoClient(uri, tlsCAFile=certifi.where())
db = client['jobs']
saved_jobs = db['saved-jobs']
saved_insights = db['saved-insights']

OPENAPI_PATH = Path(__file__).parent / "openapi.yaml"
SWAGGER_URL = "/docs"          # UI
OPENAPI_URL = "/openapi.json"  # what the UI will load

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(name)s:%(message)s"
)
log = logging.getLogger("jobs")

# -----------------------------------------------------------------------------
# Enforcer Agent (optional)
# -----------------------------------------------------------------------------
# NOTE: Ensure models.JobPosting uses url: Optional[str]


def enforce_jobs_strict(jobs: List[JobPosting]) -> List[JobPosting]:
    """Run the agent to validate/repair structure (sync wrapper for Flask)."""
    payload = [j.model_dump() for j in jobs]
    result = asyncio.run(Runner.run(
        job_manager,
        input=("Validate and strictly conform to JobPosting[].\n\n" + str(payload))
    ))
    return result.final_output

# -----------------------------------------------------------------------------
# Aggregation (async) - India focused
# -----------------------------------------------------------------------------
async def gather_jobs_india(
    fullstack_query: str = "Full Stack",
    city: Optional[str] = None,
    workday_targets: Optional[list[tuple[str, str, str]]] = None,
    include_netflix: bool = True,
    include_amazon: bool = True,
) -> List[JobPosting]:
    """
    Collect jobs concurrently from:
      - Amazon India (amazon.jobs)
      - Workday tenants (e.g., ('pwc','Global_Experienced_Careers','PwC'))
      - Netflix (Eightfold microsite)
    Returns list[JobPosting] (already normalized).
    """
    tasks = []

    # Amazon India
    if include_amazon:
        tasks.append(_wrap_fetch_amazon(fullstack_query, city))

    # Workday tenants
    wd_param = request.args.get("workday", "").strip()
    workday_targets = None
    if wd_param:
        triples = []
        for part in wd_param.split(","):
            try:
                host, site, hint = part.split(":")
                triples.append((host, site, hint))
            except ValueError:
                continue
        if triples:
            workday_targets = triples

    workday_targets = workday_targets or [
        ("pwc.wd3.myworkdayjobs.com", "Global_Experienced_Careers", "pwc"),
    ]
    for host, site, hint in workday_targets:
        tasks.append(_wrap_fetch_workday(host, site, hint, fullstack_query))

    # Netflix
    if include_netflix:
        tasks.append(_wrap_fetch_netflix())

    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: List[JobPosting] = []
    for idx, res in enumerate(results):
        if isinstance(res, Exception):
            log.exception("Provider task %s failed", idx)
            continue
        jobs.extend(res)

    log.info("Collected %d jobs (pre-filter)", len(jobs))
    return jobs

# ---- provider wrappers returning normalized JobPosting[] ----
async def _wrap_fetch_amazon(q: str, city: Optional[str]) -> List[JobPosting]:
    rows = await fetch_amazon_india(query=q, loc_query=city)
    jobs = normalize_amazon_india(rows)
    log.info("[amazon] %d rows (India-filtered)", len(jobs))
    return jobs

async def _wrap_fetch_workday(host: str, site: str, company_hint: str, q: str) -> List[JobPosting]:
    rows = await fetch_workday_jobs(host, site, search_text=q, limit=50, offset=0)
    jobs = norm_workday(rows, company_hint=company_hint)  # keeps India-only
    log.info("[workday:%s/%s] %d rows", host, site, len(jobs))
    return jobs

async def _wrap_fetch_netflix() -> List[JobPosting]:
    rows = await fetch_netflix_positions()
    jobs = norm_netflix(rows)  # norm filters to India inside
    log.info("[netflix] %d rows (India-filtered)", len(jobs))
    return jobs

# -----------------------------------------------------------------------------
# Filters (sync)
# -----------------------------------------------------------------------------
def filter_jobs(jobs: List[JobPosting], q: Optional[str], loc: Optional[str]) -> List[JobPosting]:
    if not q and not loc:
        return jobs
    tokens = q.lower().split() if q else []

    def ok(j: JobPosting) -> bool:
        blob = f"{j.title} {j.company} {j.location} {' '.join(j.tech_stack)} {(j.description_snippet or '')}".lower()
        match_q = True
        if tokens:
            # any-token match to avoid over-filtering
            match_q = any(t in blob for t in tokens)
        match_loc = True
        if loc:
            match_loc = (j.location or "").lower().find(loc.lower()) != -1
        return match_q and match_loc

    out = [j for j in jobs if ok(j)]
    log.info("Filtered down to %d jobs", len(out))
    return out

# -----------------------------------------------------------------------------
# HTTP API
# -----------------------------------------------------------------------------
@app.get("/jobs")
def jobs_endpoint():
    """
    Query params:
      q=Full%20Stack           # keyword(s)
      city=Bengaluru           # optional city narrowing for Amazon India
      strict=true|false        # pass through Agents SDK enforcer
      include_amazon=true|false
      include_netflix=true|false
      workday=tenant:site:hint,tenant:site:hint   # optional overrides
    """
    q = request.args.get("q", "Full Stack")
    city = request.args.get("city")
    strict = (request.args.get("strict", "true").lower() != "false")

    include_amazon = request.args.get("include_amazon", "true").lower() != "false"
    include_netflix = request.args.get("include_netflix", "true").lower() != "false"

    # Optional Workday overrides: "tenant:site:hint,tenant:site:hint"
    wd_param = request.args.get("workday", "").strip()
    workday_targets = None
    if wd_param:
        triples = []
        for part in wd_param.split(","):
            try:
                tenant, site, hint = part.split(":")
                triples.append((tenant, site, hint))
            except ValueError:
                continue
        if triples:
            workday_targets = triples

    # Run async providers
    jobs: List[JobPosting] = asyncio.run(
        gather_jobs_india(
            fullstack_query=q,
            city=city,
            workday_targets=workday_targets,
            include_netflix=include_netflix,
            include_amazon=include_amazon,
        )
    )

    # Optional extra filters
    loc = request.args.get("location")  # generic location filter
    if q or loc:
        jobs = filter_jobs(jobs, q=q, loc=loc)

    # Optional agent enforcement
    if strict:
        try:
            jobs = enforce_jobs_strict(jobs)
        except Exception:
            log.exception("Agent enforcement failed; returning raw normalized output")
            # fall back to raw normalized output

    return jsonify([j.model_dump() for j in jobs])

@app.get("/job-insights")
def job_insights():
    position = request.args.get("position")
    companies = request.args.getlist("company")
    years_experience = request.args.get("years_experience")
    remote = request.args.get("remote")

    result = asyncio.run(
        Runner.run(
            tech_stack_researcher,
            input=f"""
                Analyze the following job search parameters and provide detailed job insights including required skills,
                proficiency levels, and feedback for a candidate looking for a position as {position}
                at companies like {companies} with {years_experience} years of experience {" in a remote role" if remote else ""}
            """
        )
    )
    final_output = result.final_output
    if isinstance(final_output, str):
        return jsonify({"error": final_output}), 500
    if hasattr(final_output, "insights"):
        return jsonify([insight.model_dump() for insight in final_output.insights])
    return jsonify({"error": "Unexpected agent output format"}), 500

@app.post("/save-job")
def save_job():
    data = request.get_json()
    job = JobPosting(**data)
    result = saved_jobs.insert_one(job.model_dump())
    print(result.acknowledged)
    return jsonify({"message": "Job saved successfully!"}), 201

@app.get("/saved-jobs")
def fetch_saved_jobs():
    jobs = list(saved_jobs.find({}))
    for job in jobs:
        job["_id"] = str(job["_id"])  # Convert ObjectId to string
    return jsonify(jobs), 200

@app.delete("/delete-jobs/<string:job_id>")
def delete_job(job_id):
    try:
        object_id = ObjectId(job_id)
    except Exception:
        return jsonify({"error": "Invalid job ID"}), 400

    result = saved_jobs.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({"deleted_count": result.deleted_count}), 200

@app.post("/save-insight")
def save_insight():
    data = request.get_json()
    insight = JobInsights(**data)
    result = saved_insights.insert_one(insight.model_dump())
    print(result.acknowledged)
    return jsonify({"message": "Insight saved successfully!"}), 201

@app.get("/saved-insights")
def fetch_saved_insights():
    insights = list(saved_insights.find({}))
    for insight in insights:
        insight["_id"] = str(insight["_id"])  # Convert ObjectId to string
    return jsonify(insights), 200

@app.delete("/delete-insights/<string:insight_id>")
def delete_insight(insight_id):
    try:
        object_id = ObjectId(insight_id)
    except Exception:
        return jsonify({"error": "Invalid insight ID"}), 400

    result = saved_insights.delete_one({"_id": object_id})
    if result.deleted_count == 0:
        return jsonify({"error": "Insight not found"}), 404

    return jsonify({"deleted_count": result.deleted_count}), 200

@app.get("/openapi.yaml")
def openapi_yaml():
    # Serve the raw YAML file
    return app.send_static_file("openapi.yaml") if (Path(app.root_path) / "openapi.yaml").exists() \
        else (OPENAPI_PATH.read_text(), 200, {"Content-Type": "application/yaml"})

@app.get("/openapi.json")
def openapi_json():
    # Convert YAML → JSON on the fly for Swagger UI
    spec = yaml.safe_load(OPENAPI_PATH.read_text())
    return app.response_class(
        response=json.dumps(spec),
        status=200,
        mimetype="application/json",
    )

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,              # UI served at /docs
    OPENAPI_URL,              # OpenAPI served at /openapi.json
    config={ "app_name": "Job Searcher Backend" }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


# -----------------------------------------------------------------------------
# Entrypoint
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    # Run the classic dev server (sync); no flask[async] required.
    app.run(host="0.0.0.0", port=5057, debug=True)
