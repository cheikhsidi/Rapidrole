"""
Test the AI agents directly without API calls
"""

import asyncio
from agents.job_analyzer import job_analyzer
from agents.resume_optimizer import resume_optimizer
from agents.cover_letter_generator import cover_letter_generator


async def test_job_analyzer():
    """Test job analysis agent"""
    print("🔍 Testing Job Analyzer Agent...\n")
    
    state = {
        "job_posting": {
            "title": "Senior AI Engineer",
            "company": "TechCorp AI",
            "description": """
            We're looking for a Senior AI Engineer to join our team building 
            next-generation AI applications. You'll work with LLMs, vector databases,
            and modern Python frameworks to create intelligent systems.
            """,
            "requirements": """
            - 5+ years Python experience
            - Experience with LangChain, LangGraph, or similar frameworks
            - Strong understanding of LLMs and prompt engineering
            - PostgreSQL and vector databases (pgvector, Pinecone, etc.)
            - FastAPI or similar async frameworks
            - Docker and cloud deployment (AWS/GCP)
            """,
        },
        "errors": [],
    }
    
    result = await job_analyzer.analyze(state)
    
    print("Required Skills:", result.get("required_skills"))
    print("Preferred Skills:", result.get("preferred_skills"))
    print("Experience Level:", result.get("experience_level"))
    print("Confidence:", result.get("confidence_score"))
    print()


async def test_resume_optimizer():
    """Test resume optimization agent"""
    print("📝 Testing Resume Optimizer Agent...\n")
    
    original_resume = """
    John Doe
    Software Engineer
    
    Experience:
    - Built web applications using Python and Django
    - Worked with databases and APIs
    - Collaborated with team members
    """
    
    job_requirements = {
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "LangChain"],
        "preferred_skills": ["Docker", "AWS"],
        "experience_level": "senior",
    }
    
    user_profile = {
        "skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "experience": {"total_years": 5},
    }
    
    result = await resume_optimizer.optimize(
        resume=original_resume,
        job_requirements=job_requirements,
        user_profile=user_profile,
    )
    
    print("Optimized Resume:")
    print(result["resume"][:500] + "...")
    print("\nRecommendations:", result["recommendations"])
    print()


async def test_cover_letter_generator():
    """Test cover letter generation agent"""
    print("✉️ Testing Cover Letter Generator Agent...\n")
    
    job_posting = {
        "title": "Senior AI Engineer",
        "company": "TechCorp AI",
        "description": "Building next-generation AI applications with LLMs and vector databases.",
    }
    
    user_profile = {
        "skills": ["Python", "FastAPI", "LangChain", "PostgreSQL"],
        "experience": {
            "positions": [
                {
                    "title": "Senior Software Engineer",
                    "company": "Previous Corp",
                    "achievements": ["Built scalable AI systems"]
                }
            ]
        },
        "career_goals": "Work on cutting-edge AI applications",
    }
    
    analysis = {
        "required_skills": ["Python", "LangChain", "FastAPI"],
        "key_responsibilities": ["Build AI systems", "Work with LLMs", "Deploy to production"],
    }
    
    cover_letter = await cover_letter_generator.generate(
        job_posting=job_posting,
        user_profile=user_profile,
        analysis=analysis,
    )
    
    print("Generated Cover Letter:")
    print(cover_letter[:500] + "...")
    print()


async def main():
    print("🤖 Testing AI Agents\n")
    print("=" * 60)
    print()
    
    await test_job_analyzer()
    print("=" * 60)
    print()
    
    await test_resume_optimizer()
    print("=" * 60)
    print()
    
    await test_cover_letter_generator()
    print("=" * 60)
    print()
    
    print("✅ All agent tests complete!")


if __name__ == "__main__":
    asyncio.run(main())
