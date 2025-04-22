"""Configuration management for the Telnyx MCP server."""

import os
from typing import Literal

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


# Determine API base URL based on environment
def get_api_base_url() -> str:
    """
    Return the Telnyx API base URL.

    Returns:
        str: The Telnyx API base URL
            - Value of TELNYX_API_BASE environment variable if set
            - https://api.telnyx.com/v2 otherwise
    """
    telnyx_api_base = os.getenv("TELNYX_API_BASE")
    if telnyx_api_base:
        return telnyx_api_base
    return "https://api.telnyx.com/v2"

class Settings(BaseSettings):
    """Server settings."""

    # Telnyx API settings
    telnyx_api_key: str = Field(
        default=os.getenv("TELNYX_API_KEY", ""),
        description="Telnyx API key for authentication",
    )
    telnyx_api_base_url: str = Field(
        default=get_api_base_url(),
        description="Base URL for Telnyx API",
    )

    # Server settings
    host: str = Field(
        default="0.0.0.0", description="Host to bind the server to"
    )
    port: int = Field(default=8000, description="Port to bind the server to")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = (
        Field(default="INFO", description="Logging level")
    )

    # MCP settings
    warn_on_duplicate_resources: bool = Field(
        default=True, description="Warn on duplicate resources"
    )
    warn_on_duplicate_tools: bool = Field(
        default=True, description="Warn on duplicate tools"
    )
    warn_on_duplicate_prompts: bool = Field(
        default=True, description="Warn on duplicate prompts"
    )
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


# Create a global settings instance
settings = Settings()
