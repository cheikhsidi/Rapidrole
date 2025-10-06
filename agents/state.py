from datetime import datetime
from typing import TypedDict


class ApplicationState(TypedDict):
    """State for application workflow"""

    # Input data
    user_id: str
    job_id: str
    job_posting: dict
    user_profile: dict

    # Workflow stage
    stage: str  # analyzing, optimizing, generating, submitting

    # Analysis results
    compatibility_analysis: dict | None
    skill_gaps: list[str] | None
    recommendations: list[str] | None

    # Generated documents
    tailored_resume: str | None
    cover_letter: str | None

    # Metadata
    started_at: datetime
    errors: list[str]
    human_feedback: str | None


class JobAnalysisState(TypedDict):
    """State for job analysis workflow"""

    job_posting: dict

    # Analysis results
    required_skills: list[str]
    preferred_skills: list[str]
    experience_level: str
    salary_range: dict | None
    company_culture: str | None
    key_responsibilities: list[str]

    # Metadata
    confidence_score: float
    errors: list[str]


class ResumeOptimizationState(TypedDict):
    """State for resume optimization workflow"""

    original_resume: str
    job_requirements: dict
    user_profile: dict

    # Optimization results
    optimized_resume: str
    changes_made: list[str]
    keyword_matches: dict
    ats_score: float

    # Metadata
    optimization_strategy: str
    errors: list[str]
