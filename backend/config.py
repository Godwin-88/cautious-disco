"""Application settings loaded from environment variables / .env file."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Neo4j
    neo4j_uri: str = "bolt://localhost:7688"
    neo4j_username: str = "neo4j"
    neo4j_password: str = "your-password"
    neo4j_database: str = "neo4j"

    # LLM — primary (vLLM on AMD MI300X)
    vllm_base_url: str = "http://localhost:8000/v1"
    vllm_model: str = "Qwen/Qwen2.5-72B-Instruct"
    llm_timeout: int = 120
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.3

    # LLM — fallback (Together.ai / public API)
    fallback_api_key: str = ""
    fallback_base_url: str = "https://api.together.xyz/v1"
    fallback_model: str = "Qwen/Qwen2.5-72B-Instruct-Turbo"

    # DRL
    drl_checkpoint_path: str = "backend/drl/checkpoints/ea_policy_v1.pt"

    # Embedding
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dim: int = 384

    # App
    cors_origins: list[str] = ["*"]
    log_level: str = "INFO"
    app_title: str = "EA Optimizer — AMD-Powered Agentic AI"
    app_version: str = "1.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
