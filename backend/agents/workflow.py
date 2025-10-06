"""
Application workflow orchestration using LangGraph.

This module defines the multi-agent workflow for processing job applications:
1. Analyze job requirements
2. Optimize resume for the job
3. Generate personalized cover letter
4. Finalize application

Each step is logged and traced for monitoring and debugging.
"""

import time

from langgraph.graph import END, StateGraph

from agents.cover_letter_generator import cover_letter_generator
from agents.job_analyzer import job_analyzer
from agents.resume_optimizer import resume_optimizer
from agents.state import ApplicationState
from utils.logging import get_logger
from utils.tracing import AsyncTraceContext

logger = get_logger(__name__)


def create_application_workflow() -> StateGraph:
    """Create LangGraph workflow for job application process"""

    workflow = StateGraph(ApplicationState)

    # Define nodes
    workflow.add_node("analyze_job", analyze_job_node)
    workflow.add_node("optimize_resume", optimize_resume_node)
    workflow.add_node("generate_cover_letter", generate_cover_letter_node)
    workflow.add_node("finalize", finalize_node)

    # Define edges
    workflow.set_entry_point("analyze_job")
    workflow.add_edge("analyze_job", "optimize_resume")
    workflow.add_edge("optimize_resume", "generate_cover_letter")
    workflow.add_edge("generate_cover_letter", "finalize")
    workflow.add_edge("finalize", END)

    return workflow.compile()


async def analyze_job_node(state: ApplicationState) -> ApplicationState:
    """
    Analyze job requirements using JobAnalyzerAgent.

    Args:
        state: Current application state

    Returns:
        Updated state with job analysis results
    """
    state["stage"] = "analyzing"
    start_time = time.time()

    logger.info(
        "Starting job analysis workflow node",
        extra={
            "job_title": state["job_posting"].get("title"),
            "user_id": state.get("user_id"),
        },
    )

    try:
        async with AsyncTraceContext("workflow.analyze_job"):
            analysis_state = {
                "job_posting": state["job_posting"],
                "errors": [],
            }

            analyzed = await job_analyzer.analyze(analysis_state)

            state["compatibility_analysis"] = {
                "required_skills": analyzed.get("required_skills", []),
                "preferred_skills": analyzed.get("preferred_skills", []),
                "experience_level": analyzed.get("experience_level"),
            }

            logger.info(
                "Job analysis workflow node completed",
                extra={
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "required_skills_count": len(
                        state["compatibility_analysis"]["required_skills"]
                    ),
                },
            )

    except Exception as e:
        error_msg = f"Job analysis failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(
            "Job analysis workflow node failed",
            extra={"duration_ms": round((time.time() - start_time) * 1000, 2)},
            exc_info=True,
        )

    return state


async def optimize_resume_node(state: ApplicationState) -> ApplicationState:
    """
    Optimize resume for the job using ResumeOptimizerAgent.

    Args:
        state: Current application state with job analysis

    Returns:
        Updated state with optimized resume
    """
    state["stage"] = "optimizing"
    start_time = time.time()

    logger.info(
        "Starting resume optimization workflow node", extra={"user_id": state.get("user_id")}
    )

    try:
        async with AsyncTraceContext("workflow.optimize_resume"):
            optimized = await resume_optimizer.optimize(
                resume=state["user_profile"].get("resume_text", ""),
                job_requirements=state["compatibility_analysis"],
                user_profile=state["user_profile"],
            )

            state["tailored_resume"] = optimized["resume"]
            state["recommendations"] = optimized.get("recommendations", [])

            logger.info(
                "Resume optimization workflow node completed",
                extra={
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "recommendations_count": len(state["recommendations"]),
                },
            )

    except Exception as e:
        error_msg = f"Resume optimization failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(
            "Resume optimization workflow node failed",
            extra={"duration_ms": round((time.time() - start_time) * 1000, 2)},
            exc_info=True,
        )

    return state


async def generate_cover_letter_node(state: ApplicationState) -> ApplicationState:
    """
    Generate cover letter using CoverLetterGeneratorAgent.

    Args:
        state: Current application state with job analysis and optimized resume

    Returns:
        Updated state with generated cover letter
    """
    state["stage"] = "generating"
    start_time = time.time()

    logger.info(
        "Starting cover letter generation workflow node", extra={"user_id": state.get("user_id")}
    )

    try:
        async with AsyncTraceContext("workflow.generate_cover_letter"):
            cover_letter = await cover_letter_generator.generate(
                job_posting=state["job_posting"],
                user_profile=state["user_profile"],
                analysis=state["compatibility_analysis"],
            )

            state["cover_letter"] = cover_letter

            logger.info(
                "Cover letter generation workflow node completed",
                extra={
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "cover_letter_length": len(cover_letter),
                },
            )

    except Exception as e:
        error_msg = f"Cover letter generation failed: {str(e)}"
        state["errors"].append(error_msg)
        logger.error(
            "Cover letter generation workflow node failed",
            extra={"duration_ms": round((time.time() - start_time) * 1000, 2)},
            exc_info=True,
        )

    return state


async def finalize_node(state: ApplicationState) -> ApplicationState:
    """
    Finalize application workflow.

    Args:
        state: Current application state with all generated content

    Returns:
        Final state marked as complete
    """
    logger.info(
        "Finalizing application workflow",
        extra={
            "user_id": state.get("user_id"),
            "has_resume": bool(state.get("tailored_resume")),
            "has_cover_letter": bool(state.get("cover_letter")),
            "errors_count": len(state.get("errors", [])),
        },
    )

    state["stage"] = "complete"
    return state


# Singleton workflow instance
application_workflow = create_application_workflow()
