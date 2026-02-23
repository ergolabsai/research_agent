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

    # LLM Settings
    model_name: str = os.getenv("MODEL_NAME", "claude-sonnet-4-20250514")
    temperature: float = float(os.getenv("TEMPERATURE", "0.1"))
    max_tokens: int = int(os.getenv("MAX_TOKENS", "4000"))

    # Pipeline Settings
    max_retries: int = 3
    timeout_seconds: int = 300

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
