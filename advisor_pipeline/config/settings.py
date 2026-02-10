import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API Keys
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY", None)
    
    # MongoDB
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    database_name: str = os.getenv("DATABASE_NAME", "advisor_db")
    
    # MCP Server
    mcp_server_url: Optional[str] = os.getenv("MCP_SERVER_URL", None)
    mcp_server_command: Optional[str] = os.getenv("MCP_SERVER_COMMAND", None)
    
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
