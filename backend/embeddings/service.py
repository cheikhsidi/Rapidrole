from openai import AsyncOpenAI
from typing import List
import time
from tenacity import retry, stop_after_attempt, wait_exponential

from config.settings import settings
from utils.logging import get_logger, log_api_call
from utils.tracing import trace_function


logger = get_logger(__name__)


class EmbeddingService:
    """
    Service for generating embeddings using OpenAI's embedding API.
    
    This service provides:
    - Single text embedding generation
    - Batch embedding generation for efficiency
    - Automatic retry logic for transient failures
    - Comprehensive logging and monitoring
    
    All embeddings are 768-dimensional vectors using text-embedding-3-small model.
    """
    
    def __init__(self):
        """Initialize the embedding service"""
        logger.info("Initializing EmbeddingService")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_embedding_model
        self.dimension = 768
        logger.debug(f"Using embedding model: {self.model} ({self.dimension}d)")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    @trace_function("embedding_service.embed_text")
    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed (will be truncated to 8000 chars)
            
        Returns:
            768-dimensional embedding vector
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding, returning zero vector")
            return [0.0] * self.dimension
        
        truncated_text = text.strip()[:8000]
        if len(text) > 8000:
            logger.warning(
                f"Text truncated from {len(text)} to 8000 characters for embedding"
            )
        
        try:
            start_time = time.time()
            logger.debug(f"Generating embedding for text of length {len(truncated_text)}")
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=truncated_text,
            )
            
            duration = time.time() - start_time
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else None
            
            log_api_call(
                provider="openai",
                model=self.model,
                tokens=tokens,
                duration=duration,
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding with {len(embedding)} dimensions")
            
            return embedding
            
        except Exception as e:
            logger.error(
                "Failed to generate embedding",
                extra={"text_length": len(truncated_text)},
                exc_info=True
            )
            log_api_call(
                provider="openai",
                model=self.model,
                error=str(e),
            )
            raise
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    @trace_function("embedding_service.embed_batch")
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of 768-dimensional embedding vectors
        """
        if not texts:
            logger.warning("Empty text list provided for batch embedding")
            return []
        
        logger.info(f"Generating batch embeddings for {len(texts)} texts")
        
        # Filter and truncate
        processed_texts = [t.strip()[:8000] for t in texts if t and t.strip()]
        
        if not processed_texts:
            logger.warning("All texts were empty after processing")
            return [[0.0] * self.dimension] * len(texts)
        
        try:
            start_time = time.time()
            
            response = await self.client.embeddings.create(
                model=self.model,
                input=processed_texts,
            )
            
            duration = time.time() - start_time
            tokens = response.usage.total_tokens if hasattr(response, 'usage') else None
            
            log_api_call(
                provider="openai",
                model=self.model,
                tokens=tokens,
                duration=duration,
            )
            
            embeddings = [item.embedding for item in response.data]
            logger.info(
                f"Generated {len(embeddings)} embeddings",
                extra={
                    "batch_size": len(embeddings),
                    "tokens": tokens,
                    "duration_ms": round(duration * 1000, 2),
                }
            )
            
            return embeddings
            
        except Exception as e:
            logger.error(
                "Failed to generate batch embeddings",
                extra={"batch_size": len(processed_texts)},
                exc_info=True
            )
            log_api_call(
                provider="openai",
                model=self.model,
                error=str(e),
            )
            raise
    
    @trace_function("embedding_service.embed_profile")
    async def embed_profile(self, skills: str, experience: str, goals: str) -> dict:
        """
        Generate embeddings for user profile components.
        
        Args:
            skills: Comma-separated skills string
            experience: Work experience description
            goals: Career goals description
            
        Returns:
            Dictionary with skills, experience, and goals embeddings
        """
        logger.info("Generating embeddings for user profile")
        
        embeddings = await self.embed_batch([skills, experience, goals])
        
        result = {
            "skills_embedding": embeddings[0],
            "experience_embedding": embeddings[1],
            "goals_embedding": embeddings[2],
        }
        
        logger.info("User profile embeddings generated successfully")
        return result
    
    @trace_function("embedding_service.embed_job")
    async def embed_job(self, description: str, requirements: str) -> dict:
        """
        Generate embeddings for job posting components.
        
        Args:
            description: Job description text
            requirements: Job requirements text
            
        Returns:
            Dictionary with description and requirements embeddings
        """
        logger.info("Generating embeddings for job posting")
        
        embeddings = await self.embed_batch([description, requirements])
        
        result = {
            "description_embedding": embeddings[0],
            "requirements_embedding": embeddings[1],
        }
        
        logger.info("Job posting embeddings generated successfully")
        return result


# Singleton instance
embedding_service = EmbeddingService()
