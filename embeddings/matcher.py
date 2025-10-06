"""
Semantic matching between jobs and candidates using vector embeddings.

This module provides advanced multi-dimensional semantic matching that goes
beyond keyword matching to understand the deeper compatibility between
job requirements and candidate profiles.
"""

import time

import numpy as np
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import JobPosting, UserProfile
from utils.logging import get_logger, log_database_query
from utils.tracing import AsyncTraceContext, trace_function

logger = get_logger(__name__)


class SemanticMatcher:
    """
    Advanced semantic matching between jobs and candidates.

    This class implements multi-dimensional vector similarity matching to find
    the best job-candidate matches based on:
    - Skills alignment (40% weight)
    - Experience match (35% weight)
    - Career goals alignment (25% weight)

    The matcher uses cosine similarity on 768-dimensional embeddings to
    calculate compatibility scores.
    """

    def __init__(self):
        """Initialize the semantic matcher with default weights"""
        logger.info("Initializing SemanticMatcher")
        self.weights = {
            "skills": 0.4,
            "experience": 0.35,
            "goals": 0.25,
        }
        logger.debug(f"Matcher weights: {self.weights}")

    @trace_function("semantic_matcher.find_compatible_jobs")
    async def find_compatible_jobs(
        self,
        db: AsyncSession,
        user_profile: UserProfile,
        limit: int = 20,
        min_score: float = 0.6,
    ) -> list[dict]:
        """
        Find jobs compatible with user profile using multi-vector similarity.

        This method performs a sophisticated vector search that:
        1. Calculates weighted similarity across multiple dimensions
        2. Filters by minimum compatibility score
        3. Returns detailed compatibility breakdowns

        Args:
            db: Database session
            user_profile: User profile with embeddings
            limit: Maximum number of results to return
            min_score: Minimum compatibility score (0.0-1.0)

        Returns:
            List of compatible jobs with scores and breakdowns

        Example:
            compatible_jobs = await matcher.find_compatible_jobs(
                db=db,
                user_profile=profile,
                limit=20,
                min_score=0.7
            )
        """
        start_time = time.time()

        logger.info(
            "Finding compatible jobs",
            extra={
                "user_id": str(user_profile.user_id),
                "limit": limit,
                "min_score": min_score,
            },
        )

        async with AsyncTraceContext(
            "semantic_matcher.vector_search", {"limit": limit, "min_score": min_score}
        ):
            # Multi-vector similarity search using PostgreSQL + pgvector
            logger.debug("Executing multi-vector similarity query")
            query_start = time.time()

            query = (
                select(
                    JobPosting,
                    (
                        # Cosine similarity for skills (40% weight)
                        (
                            1
                            - func.cosine_distance(
                                JobPosting.description_embedding, user_profile.skills_embedding
                            )
                        )
                        * self.weights["skills"]
                        +
                        # Cosine similarity for experience (35% weight)
                        (
                            1
                            - func.cosine_distance(
                                JobPosting.requirements_embedding, user_profile.experience_embedding
                            )
                        )
                        * self.weights["experience"]
                        +
                        # Cosine similarity for goals (25% weight)
                        (
                            1
                            - func.cosine_distance(
                                JobPosting.description_embedding, user_profile.goals_embedding
                            )
                        )
                        * self.weights["goals"]
                    ).label("compatibility_score"),
                )
                .where(JobPosting.is_active == 1)
                .order_by("compatibility_score DESC")
                .limit(limit)
            )

            result = await db.execute(query)
            rows = result.all()

            query_duration = time.time() - query_start
            log_database_query(
                operation="vector_search",
                table="job_postings",
                duration=query_duration,
                rows_affected=len(rows),
            )

            logger.debug(
                f"Vector search returned {len(rows)} results",
                extra={"query_duration_ms": round(query_duration * 1000, 2)},
            )

            # Filter by minimum score and format results
            compatible_jobs = []
            for job, score in rows:
                if score >= min_score:
                    breakdown = await self._calculate_breakdown(job, user_profile)
                    compatible_jobs.append(
                        {
                            "job": job,
                            "compatibility_score": float(score),
                            "breakdown": breakdown,
                        }
                    )

            total_duration = time.time() - start_time

            logger.info(
                "Compatible jobs found",
                extra={
                    "user_id": str(user_profile.user_id),
                    "total_results": len(rows),
                    "filtered_results": len(compatible_jobs),
                    "min_score": min_score,
                    "duration_ms": round(total_duration * 1000, 2),
                },
            )

            return compatible_jobs

    @trace_function("semantic_matcher.calculate_compatibility")
    async def calculate_compatibility(
        self,
        job: JobPosting,
        user_profile: UserProfile,
    ) -> dict:
        """
        Calculate detailed compatibility between a job and user profile.

        Computes individual similarity scores for:
        - Skills alignment
        - Experience match
        - Career goals alignment

        Then combines them using weighted averaging to produce an overall score.

        Args:
            job: Job posting with embeddings
            user_profile: User profile with embeddings

        Returns:
            Dictionary with overall score and individual component scores

        Example:
            compatibility = await matcher.calculate_compatibility(job, profile)
            # Returns: {
            #     "overall_score": 0.85,
            #     "skills_match": 0.90,
            #     "experience_match": 0.82,
            #     "goals_alignment": 0.78
            # }
        """
        start_time = time.time()

        logger.debug(
            "Calculating compatibility",
            extra={
                "job_id": str(job.id),
                "job_title": job.title,
                "user_id": str(user_profile.user_id),
            },
        )

        # Calculate individual similarities using cosine similarity
        skills_sim = self._cosine_similarity(
            job.description_embedding, user_profile.skills_embedding
        )
        experience_sim = self._cosine_similarity(
            job.requirements_embedding, user_profile.experience_embedding
        )
        goals_sim = self._cosine_similarity(job.description_embedding, user_profile.goals_embedding)

        # Weighted overall score
        overall_score = (
            skills_sim * self.weights["skills"]
            + experience_sim * self.weights["experience"]
            + goals_sim * self.weights["goals"]
        )

        result = {
            "overall_score": float(overall_score),
            "skills_match": float(skills_sim),
            "experience_match": float(experience_sim),
            "goals_alignment": float(goals_sim),
        }

        logger.debug(
            "Compatibility calculated",
            extra={
                "job_id": str(job.id),
                "overall_score": result["overall_score"],
                "skills_match": result["skills_match"],
                "experience_match": result["experience_match"],
                "goals_alignment": result["goals_alignment"],
                "duration_ms": round((time.time() - start_time) * 1000, 2),
            },
        )

        return result

    async def _calculate_breakdown(
        self,
        job: JobPosting,
        user_profile: UserProfile,
    ) -> dict:
        """
        Calculate detailed compatibility breakdown.

        Internal method that delegates to calculate_compatibility.

        Args:
            job: Job posting with embeddings
            user_profile: User profile with embeddings

        Returns:
            Compatibility breakdown dictionary
        """
        return await self.calculate_compatibility(job, user_profile)

    @staticmethod
    def _cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
        """
        Calculate cosine similarity between two vectors.

        Cosine similarity measures the cosine of the angle between two vectors,
        producing a value between -1 and 1, where:
        - 1 means identical direction (perfect match)
        - 0 means orthogonal (no similarity)
        - -1 means opposite direction

        Args:
            vec1: First vector (embedding)
            vec2: Second vector (embedding)

        Returns:
            Cosine similarity score (0.0-1.0)

        Note:
            Returns 0.0 if either vector is empty or if the norm product is zero.
        """
        if not vec1 or not vec2:
            logger.warning("Empty vector provided for cosine similarity")
            return 0.0

        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)

            dot_product = np.dot(v1, v2)
            norm_product = np.linalg.norm(v1) * np.linalg.norm(v2)

            if norm_product == 0:
                logger.warning("Zero norm product in cosine similarity calculation")
                return 0.0

            similarity = float(dot_product / norm_product)

            # Ensure result is in valid range [0, 1]
            similarity = max(0.0, min(1.0, similarity))

            return similarity

        except Exception:
            logger.error(
                "Error calculating cosine similarity",
                extra={
                    "vec1_length": len(vec1),
                    "vec2_length": len(vec2),
                },
                exc_info=True,
            )
            return 0.0


# Singleton instance
semantic_matcher = SemanticMatcher()
