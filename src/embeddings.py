"""Embedding generation engine with support for FastEmbed, OpenAI, Ollama, and fallback."""

import logging
import hashlib
import math
from typing import List, Optional
import httpx

from src.config import settings

logger = logging.getLogger(__name__)


def _pseudo_embedding(text: str, dim: int = 384) -> List[float]:
    """Deterministic normalized pseudo-embedding for testing when ML libraries are not present."""
    words = text.lower().split()
    vec = [0.0] * dim
    for word in words:
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    
    # Cosine normalize
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        vec = [x / norm for x in vec]
    else:
        vec[0] = 1.0
    return vec


class EmbeddingService:
    def __init__(self) -> None:
        self._fastembed_model: Optional[object] = None
        self._fastembed_available: Optional[bool] = None

    def _get_fastembed(self):
        if self._fastembed_available is False:
            return None
        if self._fastembed_model is None:
            try:
                from fastembed import TextEmbedding
                logger.info(f"Loading FastEmbed model: {settings.fastembed_model}")
                self._fastembed_model = TextEmbedding(model_name=settings.fastembed_model)
                self._fastembed_available = True
            except ImportError:
                logger.warning("fastembed package not found. Using fallback embedding generator.")
                self._fastembed_available = False
                return None
            except Exception as e:
                logger.error(f"Failed to load FastEmbed model: {e}")
                self._fastembed_available = False
                return None
        return self._fastembed_model

    async def get_embedding(self, text: str) -> List[float]:
        """Generate a single embedding vector for the given text."""
        embeddings = await self.get_embeddings([text])
        return embeddings[0]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of texts."""
        clean_texts = [t.replace("\n", " ").strip() for t in texts]
        if not clean_texts:
            return []

        provider = settings.embedding_provider.lower()
        if provider == "fastembed":
            model = self._get_fastembed()
            if model is not None:
                generator = model.embed(clean_texts)
                return [vec.tolist() for vec in generator]
            return [_pseudo_embedding(t, settings.embedding_dim) for t in clean_texts]

        elif provider == "openai":
            return await self._embed_openai(clean_texts)
        elif provider == "ollama":
            return await self._embed_ollama(clean_texts)
        else:
            logger.warning(f"Unknown embedding provider '{provider}', falling back")
            return [_pseudo_embedding(t, settings.embedding_dim) for t in clean_texts]

    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI embedding provider")
        
        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "input": texts,
            "model": settings.openai_embedding_model,
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]

    async def _embed_ollama(self, texts: List[str]) -> List[List[float]]:
        url = f"{settings.ollama_base_url.rstrip('/')}/api/embeddings"
        results: List[List[float]] = []
        async with httpx.AsyncClient(timeout=30.0) as client:
            for text in texts:
                payload = {
                    "model": settings.ollama_embedding_model,
                    "prompt": text,
                }
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                data = resp.json()
                results.append(data["embedding"])
        return results


embedding_service = EmbeddingService()
