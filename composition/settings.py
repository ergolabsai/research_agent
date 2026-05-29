# SPDX-FileCopyrightText: 2026 Chelsea Liekhus-Schmaltz and Johnathon Barhydt
#
# SPDX-License-Identifier: AGPL-3.0-only

"""Unified application settings.

Canonical location per docs/architecture/decisions/0009. Both halves of the
system (backend API and advisor pipeline) read from here. A thin re-export
remains at `advisor_pipeline.config.settings` for the duration of the
migration; new code should import from this module directly.
"""

import os
from typing import Optional

import dotenv
from pydantic_settings import BaseSettings

dotenv.load_dotenv()


class Settings(BaseSettings):
    """Unified application settings loaded from environment variables."""

    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)

    # Backend / SQLite
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./backend/data/app.db")

    # PASETO v4.public — Ed25519 key pair (PEM-encoded).
    # Generate once: openssl genpkey -algorithm ed25519 -out ed25519_private.pem
    #                openssl pkey -in ed25519_private.pem -pubout -out ed25519_public.pem
    # In .env, use a quoted multiline value or collapse with literal \n.
    paseto_private_key: str = os.getenv("PASETO_PRIVATE_KEY", "")
    paseto_public_key: str = os.getenv("PASETO_PUBLIC_KEY", "")

    # MCP Server
    mcp_server_url: Optional[str] = os.getenv("MCP_SERVER_URL", None)
    mcp_server_command: Optional[str] = os.getenv("MCP_SERVER_COMMAND", None)
    advisor_mcp_command: Optional[str] = os.getenv("ADVISOR_MCP_COMMAND", None)
    calculator_mcp_command: Optional[str] = os.getenv("CALCULATOR_MCP_COMMAND", None)
    calculator_transport: str = os.getenv("CALCULATOR_TRANSPORT", "stdio")  # "stdio" or "sse"

    # LLM Settings
    llm_provider: str = os.getenv("LLM_PROVIDER", "anthropic")  # "anthropic" or "openrouter"
    model_name: str = os.getenv("MODEL_NAME", "claude-haiku-4-5-20251001")
    openrouter_api_key: str = os.getenv("OPENROUTER_API_KEY", "")
    openrouter_model: str = os.getenv("OPENROUTER_MODEL", "google/gemma-2-9b-it")
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4000"))

    # Pipeline Settings
    max_retries: int = 3
    timeout_seconds: int = 300

    # LanceDB
    lancedb_path: str = os.getenv("LANCEDB_PATH", "backend/data/arxiv_lancedb")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5")

    # MinIO
    minio_endpoint: str = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    minio_access_key: str = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    minio_secret_key: str = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    minio_secure: bool = os.getenv("MINIO_SECURE", "false").lower() == "true"
    minio_bucket: str = os.getenv("MINIO_BUCKET", "attachments")
    storage_backend: str = os.getenv("STORAGE_BACKEND", "local").lower()  # "local" or "minio"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
