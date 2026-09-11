"""Integration tests for context store ranking and in-memory fallback search."""

import pytest
from src.context_store import ContextStore, _cosine_similarity
from src.models import ContextDocument


@pytest.mark.asyncio
async def test_cosine_similarity():
    v1 = [1.0, 0.0, 0.0]
    v2 = [1.0, 0.0, 0.0]
    assert pytest.approx(_cosine_similarity(v1, v2), 0.001) == 1.0

    v3 = [0.0, 1.0, 0.0]
    assert pytest.approx(_cosine_similarity(v1, v3), 0.001) == 0.0

    v4 = [0.7071, 0.7071, 0.0]
    assert pytest.approx(_cosine_similarity(v1, v4), 0.01) == 0.7071


@pytest.mark.asyncio
async def test_context_document_serialization():
    doc = ContextDocument(
        title="Architecture Guide",
        content="Microservices communication using gRPC and NATS",
        tags=["architecture", "grpc"],
        project="platform",
        author_device="macbook-pro",
        metadata_={"version": "1.0"},
        embedding=[0.1] * 384,
    )
    d = doc.to_dict(include_embedding=False)
    assert d["title"] == "Architecture Guide"
    assert d["project"] == "platform"
    assert d["tags"] == ["architecture", "grpc"]
    assert "embedding" not in d

    d_with_emb = doc.to_dict(include_embedding=True)
    assert "embedding" in d_with_emb
    assert len(d_with_emb["embedding"]) == 384
