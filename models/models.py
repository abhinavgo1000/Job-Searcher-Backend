from __future__ import annotations

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class Compensation(BaseModel):
    currency: Optional[str] = Field(None, description="ISO code like USD, EUR, INR")
    min: Optional[float] = None
    max: Optional[float] = None
    period: Optional[Literal["hour","day","month","year","total"]] = None
    notes: Optional[str] = None  # e.g., “plus equity”

class JobPosting(BaseModel):
    id: str | None = Field(default=None, description="Deterministic id if url/job_id present, else random")
    source: str = Field(..., description="greenhouse, lever, etc.")
    company: str
    title: str
    location: Optional[str] = None
    remote: Optional[bool] = None
    tech_stack: List[str] = Field(default_factory=list)
    compensation: Optional[Compensation] = None
    url: Optional[str] = Field(
        default = None,
        description = "HTTP(S) URL as a string. Example: https://company.com/job/123"
    )
    job_id: Optional[str] = None
    description_snippet: Optional[str] = None

class SkillDetail(BaseModel):
    name: str
    description: str
    proficiency_level: str  # e.g., "Beginner", "Intermediate", "Expert"
    category: Optional[str] = None  # e.g., "Frontend", "Backend", "DevOps"

class JobInsights(BaseModel):
    summary: str
    skills: List[SkillDetail]
    feedback: Optional[str] = None  # Agent feedback or notes
    postings: Optional[List[JobPosting]] = None

class MultiJobInsights(BaseModel):# List of job IDs or titles
    insights: List[JobInsights]
