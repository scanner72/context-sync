"""Configuration settings for Remote Context Store."""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Security
    auth_token: str = Field(
        default="context-secret-token",
        description="Bearer token for authenticating MCP clients",
    )

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://context_user:context_password@localhost:5432/context_db",
        description="Async PostgreSQL connection URI",
    )

    # Embeddings
    embedding_provider: str = Field(
        default="fastembed",
        description="Embedding provider: 'fastembed', 'openai', or 'ollama'",
    )
    fastembed_model: str = Field(
        default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        description="Pretrained FastEmbed model name (384-dim)",
    )
    embedding_dim: int = Field(
        default=384,
        description="Dimensionality of the embedding vector",
    )

    # OpenAI Embeddings (optional)
    openai_api_key: str | None = Field(
        default=None,
        description="API key for OpenAI embeddings",
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        description="OpenAI model identifier",
    )

    # Ollama Embeddings (optional)
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL",
    )
    ollama_embedding_model: str = Field(
        default="nomic-embed-text",
        description="Ollama embedding model name",
    )

    # Server Network
    host: str = Field(default="0.0.0.0", description="Bind host")
    port: int = Field(default=8000, description="Bind port")
    debug: bool = Field(default=False, description="Debug mode")
    allowed_origins: str = Field(default="*", description="CORS allowed origins")

    @property
    def cors_origins(self) -> List[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


settings = Settings()
