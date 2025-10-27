"""Configuration management for Music RAG."""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = "Music RAG"
    app_version: str = "0.1.0"
    debug: bool = Field(default=False, validation_alias="DEBUG")
    environment: str = Field(default="development", validation_alias="ENVIRONMENT")

    # Database
    chromadb_path: str = Field(default="./data/chromadb", validation_alias="CHROMADB_PATH")
    chromadb_host: Optional[str] = Field(default=None, validation_alias="CHROMADB_HOST")
    chromadb_port: Optional[int] = Field(default=None, validation_alias="CHROMADB_PORT")

    # Embeddings
    text_model: str = Field(default="all-MiniLM-L6-v2", validation_alias="TEXT_MODEL")
    audio_sample_rate: int = Field(default=22050, validation_alias="AUDIO_SAMPLE_RATE")
    audio_n_mfcc: int = Field(default=40, validation_alias="AUDIO_N_MFCC")

    # CLAP embeddings (v0.2.0)
    use_clap: bool = Field(default=False, validation_alias="USE_CLAP")
    clap_model: str = Field(default="laion/clap-htsat-unfused", validation_alias="CLAP_MODEL")

    # LLM integration (v0.2.0)
    openai_api_key: Optional[str] = Field(default=None, validation_alias="OPENAI_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", validation_alias="LLM_MODEL")
    enable_query_enhancement: bool = Field(default=False, validation_alias="ENABLE_QUERY_ENHANCEMENT")
    enable_result_explanation: bool = Field(default=False, validation_alias="ENABLE_RESULT_EXPLANATION")

    # Reranking (v0.2.0)
    enable_reranking: bool = Field(default=False, validation_alias="ENABLE_RERANKING")
    reranker_model: str = Field(default="cross-encoder/ms-marco-MiniLM-L-6-v2", validation_alias="RERANKER_MODEL")

    # Retrieval
    default_top_k: int = Field(default=10, validation_alias="DEFAULT_TOP_K")
    default_semantic_weight: float = Field(default=0.7, validation_alias="DEFAULT_SEMANTIC_WEIGHT")

    # API
    api_host: str = Field(default="0.0.0.0", validation_alias="API_HOST")
    api_port: int = Field(default=8000, validation_alias="API_PORT")
    api_reload: bool = Field(default=False, validation_alias="API_RELOAD")
    api_key: Optional[str] = Field(default=None, validation_alias="API_KEY")

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        validation_alias="LOG_FORMAT"
    )

    # Performance
    max_batch_size: int = Field(default=100, validation_alias="MAX_BATCH_SIZE")
    cache_enabled: bool = Field(default=False, validation_alias="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, validation_alias="CACHE_TTL")  # seconds

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment.lower() == "development"


# Global settings instance
settings = Settings()
