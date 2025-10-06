from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain.prompts import ChatPromptTemplate
from typing import Dict, List
import json
import time

from config.settings import settings
from agents.state import JobAnalysisState
from utils.logging import get_logger, log_api_call, log_agent_execution
from utils.tracing import trace_function


logger = get_logger(__name__)


class JobAnalyzerAgent:
    """
    Agent for analyzing job postings and extracting structured information.
    
    This agent uses LLM to parse job descriptions and extract:
    - Required and preferred skills
    - Experience level requirements
    - Salary information
    - Company culture indicators
    - Key responsibilities
    
    The agent is designed to be stateless and can be called multiple times
    with different job postings.
    """
    
    def __init__(self):
        """Initialize the job analyzer agent with LLM client"""
        logger.info("Initializing JobAnalyzerAgent")
        self.llm = ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0.1,
        )
        logger.debug(f"Using OpenAI model: {settings.openai_model}")
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert job market analyst. Analyze the job posting and extract structured information.
            
Extract:
1. Required skills (must-have technical and soft skills)
2. Preferred skills (nice-to-have)
3. Experience level (entry/mid/senior)
4. Salary range if mentioned
5. Company culture indicators
6. Key responsibilities

Return valid JSON only."""),
            ("user", "Job Title: {title}\n\nCompany: {company}\n\nDescription:\n{description}\n\nRequirements:\n{requirements}")
        ])
    
    @trace_function("job_analyzer.analyze")
    async def analyze(self, state: JobAnalysisState) -> JobAnalysisState:
        """
        Analyze job posting and update state with extracted information.
        
        Args:
            state: Current job analysis state containing job posting data
            
        Returns:
            Updated state with analysis results
        """
        start_time = time.time()
        job = state["job_posting"]
        
        logger.info(
            "Starting job analysis",
            extra={
                "job_title": job.get("title"),
                "company": job.get("company"),
            }
        )
        
        try:
            # Create prompt
            messages = self.prompt.format_messages(
                title=job.get("title", ""),
                company=job.get("company", ""),
                description=job.get("description", ""),
                requirements=job.get("requirements", ""),
            )
            
            # Get structured output from LLM
            logger.debug("Calling OpenAI API for job analysis")
            api_start = time.time()
            response = await self.llm.ainvoke(messages)
            api_duration = time.time() - api_start
            
            # Log API call
            log_api_call(
                provider="openai",
                model=settings.openai_model,
                duration=api_duration,
            )
            
            # Parse response
            analysis = json.loads(response.content)
            
            # Update state
            state["required_skills"] = analysis.get("required_skills", [])
            state["preferred_skills"] = analysis.get("preferred_skills", [])
            state["experience_level"] = analysis.get("experience_level", "mid")
            state["salary_range"] = analysis.get("salary_range")
            state["company_culture"] = analysis.get("company_culture")
            state["key_responsibilities"] = analysis.get("key_responsibilities", [])
            state["confidence_score"] = 0.9
            
            # Log success
            log_agent_execution(
                agent_name="JobAnalyzerAgent",
                stage="analyze",
                duration=time.time() - start_time,
                success=True,
                metadata={
                    "required_skills_count": len(state["required_skills"]),
                    "preferred_skills_count": len(state["preferred_skills"]),
                    "experience_level": state["experience_level"],
                }
            )
            
            logger.info(
                "Job analysis completed successfully",
                extra={
                    "job_title": job.get("title"),
                    "required_skills": len(state["required_skills"]),
                    "confidence_score": state["confidence_score"],
                }
            )
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse LLM response: {str(e)}"
            logger.error(error_msg, exc_info=True)
            state["errors"].append(error_msg)
            state["confidence_score"] = 0.0
            
            log_agent_execution(
                agent_name="JobAnalyzerAgent",
                stage="analyze",
                duration=time.time() - start_time,
                success=False,
                error=error_msg,
            )
            
        except Exception as e:
            error_msg = f"Job analysis failed: {str(e)}"
            logger.error(
                error_msg,
                extra={"job_title": job.get("title")},
                exc_info=True
            )
            state["errors"].append(error_msg)
            state["confidence_score"] = 0.0
            
            log_agent_execution(
                agent_name="JobAnalyzerAgent",
                stage="analyze",
                duration=time.time() - start_time,
                success=False,
                error=error_msg,
            )
        
        return state
    
    @trace_function("job_analyzer.extract_skills")
    async def extract_skills(self, job_description: str) -> List[str]:
        """
        Quick skill extraction from job description.
        
        Args:
            job_description: Raw job description text
            
        Returns:
            List of extracted skills
        """
        logger.debug("Extracting skills from job description")
        
        prompt = f"""Extract technical skills from this job description. Return only a JSON array of skills.

Job Description:
{job_description[:2000]}

Return format: ["skill1", "skill2", ...]"""
        
        try:
            start_time = time.time()
            response = await self.llm.ainvoke(prompt)
            
            log_api_call(
                provider="openai",
                model=settings.openai_model,
                duration=time.time() - start_time,
            )
            
            skills = json.loads(response.content)
            result = skills if isinstance(skills, list) else []
            
            logger.info(f"Extracted {len(result)} skills from job description")
            return result
            
        except Exception as e:
            logger.error("Failed to extract skills", exc_info=True)
            return []


# Singleton instance
job_analyzer = JobAnalyzerAgent()
