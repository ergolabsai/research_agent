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
    secret_key: str = os.getenv("SECRET_KEY", "change-this-to-a-random-secret-key")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")

    # MongoDB (pipeline + calculator)
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "advisor_db")

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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
