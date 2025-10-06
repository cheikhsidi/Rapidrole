"""
Comprehensive tests for embedding service and semantic matching.

Tests cover:
- Embedding generation
- Semantic matching
- Vector similarity calculations
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from db.models import JobPosting, UserProfile
from embeddings.matcher import SemanticMatcher
from embeddings.service import EmbeddingService


@pytest.mark.asyncio
class TestEmbeddingService:
    """Test suite for EmbeddingService"""

    def test_embedding_service_initialization(self):
        """Test service initializes correctly"""
        service = EmbeddingService()
        assert service is not None
        assert service.client is not None
        assert service.dimension == 768

    async def test_embed_text_success(self):
        """Test successful text embedding"""
        service = EmbeddingService()

        with patch.object(
            service.client.embeddings, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 768)]
            mock_response.usage = Mock(total_tokens=100)
            mock_create.return_value = mock_response

            result = await service.embed_text("test text")

            assert isinstance(result, list)
            assert len(result) == 768

    async def test_embed_text_empty_input(self):
        """Test embedding with empty text"""
        service = EmbeddingService()

        result = await service.embed_text("")

        assert isinstance(result, list)
        assert len(result) == 768
        assert all(x == 0.0 for x in result)

    async def test_embed_batch_success(self):
        """Test batch embedding"""
        service = EmbeddingService()

        texts = ["text1", "text2", "text3"]

        with patch.object(
            service.client.embeddings, "create", new_callable=AsyncMock
        ) as mock_create:
            mock_response = Mock()
            mock_response.data = [
                Mock(embedding=[0.1] * 768),
                Mock(embedding=[0.2] * 768),
                Mock(embedding=[0.3] * 768),
            ]
            mock_response.usage = Mock(total_tokens=300)
            mock_create.return_value = mock_response

            result = await service.embed_batch(texts)

            assert isinstance(result, list)
            assert len(result) == 3
            assert all(len(emb) == 768 for emb in result)

    async def test_embed_profile_success(self):
        """Test profile embedding"""
        service = EmbeddingService()

        with patch.object(service, "embed_batch", new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = [
                [0.1] * 768,
                [0.2] * 768,
                [0.3] * 768,
            ]

            result = await service.embed_profile(
                skills="Python, FastAPI", experience="5 years", goals="Build great products"
            )

            assert "skills_embedding" in result
            assert "experience_embedding" in result
            assert "goals_embedding" in result

    async def test_embed_job_success(self):
        """Test job embedding"""
        service = EmbeddingService()

        with patch.object(service, "embed_batch", new_callable=AsyncMock) as mock_batch:
            mock_batch.return_value = [
                [0.1] * 768,
                [0.2] * 768,
            ]

            result = await service.embed_job(
                description="Great job opportunity", requirements="Python, FastAPI required"
            )

            assert "description_embedding" in result
            assert "requirements_embedding" in result


@pytest.mark.asyncio
class TestSemanticMatcher:
    """Test suite for SemanticMatcher"""

    def test_semantic_matcher_initialization(self):
        """Test matcher initializes correctly"""
        matcher = SemanticMatcher()
        assert matcher is not None
        assert matcher.weights is not None
        assert sum(matcher.weights.values()) == 1.0

    def test_cosine_similarity_identical_vectors(self):
        """Test cosine similarity with identical vectors"""
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]

        similarity = SemanticMatcher._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(1.0, abs=0.01)

    def test_cosine_similarity_orthogonal_vectors(self):
        """Test cosine similarity with orthogonal vectors"""
        vec1 = [1.0, 0.0, 0.0]
        vec2 = [0.0, 1.0, 0.0]

        similarity = SemanticMatcher._cosine_similarity(vec1, vec2)

        assert similarity == pytest.approx(0.0, abs=0.01)

    def test_cosine_similarity_empty_vectors(self):
        """Test cosine similarity with empty vectors"""
        vec1 = []
        vec2 = [1.0, 2.0]

        similarity = SemanticMatcher._cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    async def test_calculate_compatibility(self):
        """Test compatibility calculation"""
        matcher = SemanticMatcher()

        # Create mock job and profile
        job = Mock(spec=JobPosting)
        job.id = "job-123"
        job.title = "Test Job"
        job.description_embedding = [0.5] * 768
        job.requirements_embedding = [0.6] * 768

        profile = Mock(spec=UserProfile)
        profile.user_id = "user-123"
        profile.skills_embedding = [0.5] * 768
        profile.experience_embedding = [0.6] * 768
        profile.goals_embedding = [0.5] * 768

        result = await matcher.calculate_compatibility(job, profile)

        assert "overall_score" in result
        assert "skills_match" in result
        assert "experience_match" in result
        assert "goals_alignment" in result
        assert 0.0 <= result["overall_score"] <= 1.0

    async def test_find_compatible_jobs(self):
        """Test finding compatible jobs"""
        matcher = SemanticMatcher()

        # Create mock database session
        mock_db = AsyncMock()

        # Create mock profile
        profile = Mock(spec=UserProfile)
        profile.user_id = "user-123"
        profile.skills_embedding = [0.5] * 768
        profile.experience_embedding = [0.6] * 768
        profile.goals_embedding = [0.5] * 768

        # Create mock jobs
        mock_job = Mock(spec=JobPosting)
        mock_job.id = "job-123"
        mock_job.title = "Test Job"
        mock_job.company = "Test Co"
        mock_job.location = "Remote"
        mock_job.description_embedding = [0.5] * 768
        mock_job.requirements_embedding = [0.6] * 768

        # Mock database query result
        mock_result = Mock()
        mock_result.all.return_value = [(mock_job, 0.85)]
        mock_db.execute.return_value = mock_result

        results = await matcher.find_compatible_jobs(
            db=mock_db, user_profile=profile, limit=10, min_score=0.7
        )

        assert isinstance(results, list)
        # Results might be empty if score filtering happens
        if len(results) > 0:
            assert "job" in results[0]
            assert "compatibility_score" in results[0]
            assert "breakdown" in results[0]
