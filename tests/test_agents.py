"""
Comprehensive tests for AI agents.

Tests cover:
- Job analyzer agent
- Resume optimizer agent
- Cover letter generator agent
- Workflow orchestration
"""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from agents.cover_letter_generator import CoverLetterGeneratorAgent
from agents.job_analyzer import JobAnalyzerAgent
from agents.resume_optimizer import ResumeOptimizerAgent


@pytest.mark.asyncio
class TestJobAnalyzerAgent:
    """Test suite for JobAnalyzerAgent"""

    async def test_job_analyzer_initialization(self):
        """Test agent initializes correctly"""
        agent = JobAnalyzerAgent()
        assert agent is not None
        assert agent.llm is not None

    async def test_analyze_job_success(self):
        """Test successful job analysis"""
        agent = JobAnalyzerAgent()

        state = {
            "job_posting": {
                "title": "Senior Python Developer",
                "company": "Tech Corp",
                "description": "We need a Python expert with FastAPI experience",
                "requirements": "5+ years Python, FastAPI, PostgreSQL",
            },
            "errors": [],
        }

        # Mock the invoke method using patch on the class
        with patch("langchain_openai.ChatOpenAI.ainvoke", new_callable=AsyncMock) as mock_llm:
            mock_response = Mock()
            mock_response.content = (
                '{"required_skills": ["Python", "FastAPI"], "experience_level": "senior"}'
            )
            mock_llm.return_value = mock_response

            result = await agent.analyze(state)

            assert "required_skills" in result
            assert len(result["errors"]) == 0
            assert result.get("confidence_score", 0) > 0

    @pytest.mark.integration
    async def test_analyze_job_handles_errors(self):
        """Test agent handles errors gracefully"""
        agent = JobAnalyzerAgent()

        state = {
            "job_posting": {
                "title": "Test Job",
                "company": "Test Co",
                "description": "",
                "requirements": "",
            },
            "errors": [],
        }

        with patch("langchain_openai.ChatOpenAI.ainvoke", side_effect=Exception("API Error")):
            result = await agent.analyze(state)

            assert len(result["errors"]) > 0
            assert result.get("confidence_score") == 0.0

    @pytest.mark.integration
    async def test_extract_skills(self):
        """Test skill extraction"""
        agent = JobAnalyzerAgent()

        description = "Looking for Python, FastAPI, PostgreSQL, Docker skills"

        with patch("langchain_openai.ChatOpenAI.ainvoke", new_callable=AsyncMock) as mock_llm:
            mock_response = Mock()
            mock_response.content = '["Python", "FastAPI", "PostgreSQL", "Docker"]'
            mock_llm.return_value = mock_response

            skills = await agent.extract_skills(description)

            assert isinstance(skills, list)
            assert len(skills) > 0


@pytest.mark.asyncio
class TestResumeOptimizerAgent:
    """Test suite for ResumeOptimizerAgent"""

    async def test_resume_optimizer_initialization(self):
        """Test agent initializes correctly"""
        agent = ResumeOptimizerAgent()
        assert agent is not None
        assert agent.llm is not None

    @pytest.mark.integration
    async def test_optimize_resume_success(self):
        """Test successful resume optimization"""
        agent = ResumeOptimizerAgent()

        resume = "John Doe - Software Engineer with Python experience"
        job_requirements = {
            "required_skills": ["Python", "FastAPI"],
            "experience_level": "senior",
        }
        user_profile = {
            "skills": ["Python", "Django", "PostgreSQL"],
            "experience": {"total_years": 5},
        }

        with patch("langchain_openai.ChatOpenAI.ainvoke", new_callable=AsyncMock) as mock_llm:
            mock_response = Mock()
            mock_response.content = "Optimized resume with FastAPI highlighted"
            mock_llm.return_value = mock_response

            result = await agent.optimize(resume, job_requirements, user_profile)

            assert "resume" in result
            assert "recommendations" in result
            assert "ats_score" in result
            assert len(result["resume"]) > 0

    async def test_optimize_handles_errors(self):
        """Test optimizer handles errors"""
        agent = ResumeOptimizerAgent()

        with patch("langchain_openai.ChatOpenAI.ainvoke", side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await agent.optimize("resume", {}, {})


@pytest.mark.asyncio
class TestCoverLetterGeneratorAgent:
    """Test suite for CoverLetterGeneratorAgent"""

    async def test_cover_letter_generator_initialization(self):
        """Test agent initializes correctly"""
        agent = CoverLetterGeneratorAgent()
        assert agent is not None
        assert agent.llm is not None

    @pytest.mark.integration
    async def test_generate_cover_letter_success(self):
        """Test successful cover letter generation"""
        agent = CoverLetterGeneratorAgent()

        job_posting = {
            "title": "Senior Developer",
            "company": "Tech Corp",
            "description": "Great opportunity",
        }
        user_profile = {
            "skills": ["Python", "FastAPI"],
            "experience": {},
            "career_goals": "Build great products",
        }
        analysis = {
            "required_skills": ["Python"],
            "key_responsibilities": ["Develop APIs"],
        }

        with patch("langchain_anthropic.ChatAnthropic.ainvoke", new_callable=AsyncMock) as mock_llm:
            mock_response = Mock()
            mock_response.content = "Dear Hiring Manager, I am excited to apply..."
            mock_llm.return_value = mock_response

            result = await agent.generate(job_posting, user_profile, analysis)

            assert isinstance(result, str)
            assert len(result) > 0

    async def test_generate_handles_errors(self):
        """Test generator handles errors"""
        agent = CoverLetterGeneratorAgent()

        with patch("langchain_anthropic.ChatAnthropic.ainvoke", side_effect=Exception("API Error")):
            with pytest.raises(Exception):
                await agent.generate({}, {}, {})


@pytest.mark.asyncio
class TestWorkflow:
    """Test suite for workflow orchestration"""

    async def test_workflow_nodes_exist(self):
        """Test all workflow nodes are defined"""
        from agents.workflow import (
            analyze_job_node,
            finalize_node,
            generate_cover_letter_node,
            optimize_resume_node,
        )

        assert analyze_job_node is not None
        assert optimize_resume_node is not None
        assert generate_cover_letter_node is not None
        assert finalize_node is not None

    async def test_analyze_job_node(self):
        """Test job analysis workflow node"""
        from agents.workflow import analyze_job_node

        state = {
            "stage": "init",
            "job_posting": {
                "title": "Test Job",
                "company": "Test Co",
                "description": "Test description",
                "requirements": "Test requirements",
            },
            "user_profile": {},
            "errors": [],
        }

        with patch("agents.workflow.job_analyzer.analyze", new_callable=AsyncMock) as mock_analyze:
            mock_analyze.return_value = {
                "required_skills": ["Python"],
                "preferred_skills": ["Docker"],
                "experience_level": "mid",
                "errors": [],
            }

            result = await analyze_job_node(state)

            assert result["stage"] == "analyzing"
            assert "compatibility_analysis" in result or len(result["errors"]) > 0
