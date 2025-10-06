from typing import TypedDict, List, Dict, Optional
from datetime import datetime


class ApplicationState(TypedDict):
    """State for application workflow"""
    
    # Input data
    user_id: str
    job_id: str
    job_posting: Dict
    user_profile: Dict
    
    # Workflow stage
    stage: str  # analyzing, optimizing, generating, submitting
    
    # Analysis results
    compatibility_analysis: Optional[Dict]
    skill_gaps: Optional[List[str]]
    recommendations: Optional[List[str]]
    
    # Generated documents
    tailored_resume: Optional[str]
    cover_letter: Optional[str]
    
    # Metadata
    started_at: datetime
    errors: List[str]
    human_feedback: Optional[str]


class JobAnalysisState(TypedDict):
    """State for job analysis workflow"""
    
    job_posting: Dict
    
    # Analysis results
    required_skills: List[str]
    preferred_skills: List[str]
    experience_level: str
    salary_range: Optional[Dict]
    company_culture: Optional[str]
    key_responsibilities: List[str]
    
    # Metadata
    confidence_score: float
    errors: List[str]


class ResumeOptimizationState(TypedDict):
    """State for resume optimization workflow"""
    
    original_resume: str
    job_requirements: Dict
    user_profile: Dict
    
    # Optimization results
    optimized_resume: str
    changes_made: List[str]
    keyword_matches: Dict
    ats_score: float
    
    # Metadata
    optimization_strategy: str
    errors: List[str]
