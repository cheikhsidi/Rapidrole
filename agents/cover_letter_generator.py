import time

from langchain.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic

from config.settings import settings
from utils.logging import get_logger, log_agent_execution, log_api_call
from utils.tracing import trace_function

logger = get_logger(__name__)


class CoverLetterGeneratorAgent:
    """
    Agent for generating personalized cover letters.

    This agent uses Claude 3.5 Sonnet to create compelling, personalized
    cover letters that:
    - Show genuine interest in the company and role
    - Highlight relevant experience and achievements
    - Demonstrate cultural fit
    - Maintain a professional yet warm tone

    The agent is designed to be stateless and can generate multiple
    cover letters concurrently.
    """

    def __init__(self):
        """Initialize the cover letter generator agent with Anthropic client"""
        logger.info("Initializing CoverLetterGeneratorAgent")
        self.llm = ChatAnthropic(
            model=settings.anthropic_model,
            api_key=settings.anthropic_api_key,
            temperature=0.7,
        )
        logger.debug(f"Using Anthropic model: {settings.anthropic_model}")

        self.prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert career coach and cover letter writer.

Write a compelling, personalized cover letter that:
1. Shows genuine interest in the company and role
2. Highlights relevant experience and achievements
3. Demonstrates cultural fit
4. Is concise (3-4 paragraphs)
5. Has a professional yet warm tone

Return only the cover letter text, no additional commentary.""",
                ),
                (
                    "user",
                    """Job Details:
Title: {title}
Company: {company}
Description: {description}

Candidate Profile:
Skills: {skills}
Experience: {experience}
Career Goals: {goals}

Job Analysis:
Required Skills: {required_skills}
Key Responsibilities: {responsibilities}

Write a cover letter for this application.""",
                ),
            ]
        )

    @trace_function("cover_letter_generator.generate")
    async def generate(
        self,
        job_posting: dict,
        user_profile: dict,
        analysis: dict,
    ) -> str:
        """
        Generate personalized cover letter for a job application.

        Args:
            job_posting: Job posting details (title, company, description)
            user_profile: User profile with skills, experience, and goals
            analysis: Job analysis results with required skills and responsibilities

        Returns:
            Generated cover letter text

        Raises:
            Exception: If cover letter generation fails
        """
        start_time = time.time()

        logger.info(
            "Starting cover letter generation",
            extra={
                "job_title": job_posting.get("title"),
                "company": job_posting.get("company"),
            },
        )

        try:
            # Format prompt with job and user data
            messages = self.prompt.format_messages(
                title=job_posting.get("title", ""),
                company=job_posting.get("company", ""),
                description=job_posting.get("description", "")[:500],
                skills=", ".join(user_profile.get("skills", [])),
                experience=str(user_profile.get("experience", {}))[:500],
                goals=user_profile.get("career_goals", ""),
                required_skills=", ".join(analysis.get("required_skills", [])),
                responsibilities=", ".join(analysis.get("key_responsibilities", [])[:3]),
            )

            # Call Anthropic API
            logger.debug("Calling Anthropic API for cover letter generation")
            api_start = time.time()
            response = await self.llm.ainvoke(messages)
            api_duration = time.time() - api_start

            # Log API call
            log_api_call(
                provider="anthropic",
                model=settings.anthropic_model,
                duration=api_duration,
            )

            cover_letter = response.content

            # Log success
            log_agent_execution(
                agent_name="CoverLetterGeneratorAgent",
                stage="generate",
                duration=time.time() - start_time,
                success=True,
                metadata={
                    "cover_letter_length": len(cover_letter),
                    "job_title": job_posting.get("title"),
                },
            )

            logger.info(
                "Cover letter generated successfully",
                extra={
                    "job_title": job_posting.get("title"),
                    "cover_letter_length": len(cover_letter),
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                },
            )

            return cover_letter

        except Exception as e:
            error_msg = f"Cover letter generation failed: {str(e)}"
            logger.error(
                error_msg,
                extra={
                    "job_title": job_posting.get("title"),
                    "company": job_posting.get("company"),
                },
                exc_info=True,
            )

            log_agent_execution(
                agent_name="CoverLetterGeneratorAgent",
                stage="generate",
                duration=time.time() - start_time,
                success=False,
                error=error_msg,
            )

            raise Exception(error_msg)


# Singleton instance
cover_letter_generator = CoverLetterGeneratorAgent()
