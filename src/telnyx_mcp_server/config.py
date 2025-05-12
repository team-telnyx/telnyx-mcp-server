"""Configuration management for the Telnyx MCP server."""

import os
import random
import socket
from typing import Literal, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load environment variables from .env file
load_dotenv()


# Generate a random port number in the dynamic/private port range
def get_random_high_port() -> int:
    """
    Generate a random port number in the higher end of the dynamic/private port range.

    Returns:
        int: A random port number between 50000 and 65000
    """
    return random.randint(50000, 65000)


def is_unix_socket_supported() -> bool:
    """
    Check if the system supports Unix domain sockets.

    Returns:
        bool: True if Unix domain sockets are supported, False otherwise
    """
    # On Unix-like systems, we can use os.name to check
    if os.name != "posix":
        return False

    # Further check by trying to create a Unix domain socket
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        # Clean up the socket
        sock.close()
        return True
    except (AttributeError, OSError):
        return False


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

    # Webhook settings
    webhook_enabled: bool = Field(
        default=False, description="Enable webhook receiver"
    )
    webhook_port: int = Field(
        default=get_random_high_port(),
        description="Port to bind the webhook server to (random high port to avoid conflicts)",
    )
    webhook_path: str = Field(
        default="/webhooks", description="Path for webhook endpoint"
    )
    webhook_max_body_size: int = Field(
        default=1_048_576,  # 1 MB
        description="Maximum webhook request body size in bytes",
    )
    use_unix_socket: bool = Field(
        default=is_unix_socket_supported(),
        description="Use Unix domain socket instead of TCP/IP port (Unix-like systems only)",
    )
    socket_dir: Optional[str] = Field(
        default=None,
        description="Directory for Unix domain socket (default: system temp directory)",
    )

    # Ngrok settings
    ngrok_enabled: bool = Field(
        default=bool(os.getenv("NGROK_AUTHTOKEN", ""))
        or bool(os.getenv("NGROK_URL", "")),
        description="Enable ngrok tunnel for webhooks",
    )
    ngrok_authtoken: Optional[str] = Field(
        default=os.getenv("NGROK_AUTHTOKEN", None),
        description="Ngrok authentication token",
    )

    ngrok_url: Optional[str] = Field(
        default=os.getenv("NGROK_URL", None),
        description="NGROK custom domain - Experimental - TLS errors are possible.",
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
        env_nested_delimiter="__",
        extra="ignore",
        validate_default=True,
    )


# Create a global settings instance
settings = Settings()
