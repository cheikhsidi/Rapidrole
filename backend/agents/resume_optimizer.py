from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from typing import Dict
import json
import time

from config.settings import settings
from utils.logging import get_logger, log_api_call, log_agent_execution
from utils.tracing import trace_function


logger = get_logger(__name__)


class ResumeOptimizerAgent:
    """
    Agent for optimizing resumes for specific job postings.
    
    This agent uses GPT-4o to tailor resumes by:
    - Highlighting relevant skills and experience
    - Using keywords from job requirements
    - Quantifying achievements where possible
    - Maintaining ATS-friendly formatting
    - Keeping content concise and impactful
    
    The agent ensures authenticity while maximizing job match.
    """
    
    def __init__(self):
        """Initialize the resume optimizer agent with OpenAI client"""
        logger.info("Initializing ResumeOptimizerAgent")
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.3,
        )
        logger.debug(f"Using OpenAI model: {settings.openai_model}")
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert resume writer and ATS optimization specialist.
            
Your task: Optimize the resume to match the job requirements while maintaining authenticity.

Guidelines:
1. Highlight relevant skills and experience
2. Use keywords from job requirements
3. Quantify achievements where possible
4. Maintain ATS-friendly formatting
5. Keep it concise and impactful

Return the optimized resume text."""),
            ("user", """Original Resume:
{resume}

Job Requirements:
Required Skills: {required_skills}
Preferred Skills: {preferred_skills}
Experience Level: {experience_level}

User Profile:
Skills: {user_skills}
Experience: {user_experience}

Optimize this resume for the job.""")
        ])
    
    @trace_function("resume_optimizer.optimize")
    async def optimize(
        self,
        resume: str,
        job_requirements: Dict,
        user_profile: Dict,
    ) -> Dict:
        """
        Optimize resume for specific job requirements.
        
        Args:
            resume: Original resume text
            job_requirements: Job requirements including skills and experience level
            user_profile: User profile with skills and experience
            
        Returns:
            Dictionary with optimized resume, recommendations, and ATS score
            
        Raises:
            Exception: If resume optimization fails
        """
        start_time = time.time()
        
        logger.info(
            "Starting resume optimization",
            extra={
                "resume_length": len(resume),
                "required_skills_count": len(job_requirements.get("required_skills", [])),
            }
        )
        
        try:
            # Format prompt
            messages = self.prompt.format_messages(
                resume=resume,
                required_skills=", ".join(job_requirements.get("required_skills", [])),
                preferred_skills=", ".join(job_requirements.get("preferred_skills", [])),
                experience_level=job_requirements.get("experience_level", "mid"),
                user_skills=", ".join(user_profile.get("skills", [])),
                user_experience=str(user_profile.get("experience", {})),
            )
            
            # Call OpenAI API
            logger.debug("Calling OpenAI API for resume optimization")
            api_start = time.time()
            response = await self.llm.ainvoke(messages)
            api_duration = time.time() - api_start
            
            # Log API call
            log_api_call(
                provider="openai",
                model=settings.openai_model,
                duration=api_duration,
            )
            
            optimized_resume = response.content
            
            # Generate recommendations
            logger.debug("Generating optimization recommendations")
            recommendations = await self._generate_recommendations(
                job_requirements,
                user_profile,
            )
            
            result = {
                "resume": optimized_resume,
                "recommendations": recommendations,
                "ats_score": 0.85,  # Placeholder - could be calculated
            }
            
            # Log success
            log_agent_execution(
                agent_name="ResumeOptimizerAgent",
                stage="optimize",
                duration=time.time() - start_time,
                success=True,
                metadata={
                    "original_length": len(resume),
                    "optimized_length": len(optimized_resume),
                    "recommendations_count": len(recommendations),
                    "ats_score": result["ats_score"],
                }
            )
            
            logger.info(
                "Resume optimization completed successfully",
                extra={
                    "original_length": len(resume),
                    "optimized_length": len(optimized_resume),
                    "ats_score": result["ats_score"],
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                }
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Resume optimization failed: {str(e)}"
            logger.error(
                error_msg,
                extra={"resume_length": len(resume)},
                exc_info=True
            )
            
            log_agent_execution(
                agent_name="ResumeOptimizerAgent",
                stage="optimize",
                duration=time.time() - start_time,
                success=False,
                error=error_msg,
            )
            
            raise Exception(error_msg)
    
    @trace_function("resume_optimizer.generate_recommendations")
    async def _generate_recommendations(
        self,
        job_requirements: Dict,
        user_profile: Dict,
    ) -> list:
        """
        Generate improvement recommendations based on skill gaps.
        
        Args:
            job_requirements: Job requirements with required skills
            user_profile: User profile with current skills
            
        Returns:
            List of recommendation strings
        """
        logger.debug("Generating resume improvement recommendations")
        
        recommendations = []
        
        required_skills = set(job_requirements.get("required_skills", []))
        user_skills = set(user_profile.get("skills", []))
        
        missing_skills = required_skills - user_skills
        if missing_skills:
            recommendation = f"Consider highlighting transferable skills related to: {', '.join(list(missing_skills)[:3])}"
            recommendations.append(recommendation)
            logger.debug(
                "Identified skill gaps",
                extra={"missing_skills_count": len(missing_skills)}
            )
        
        logger.debug(f"Generated {len(recommendations)} recommendations")
        return recommendations


# Singleton instance
resume_optimizer = ResumeOptimizerAgent()
