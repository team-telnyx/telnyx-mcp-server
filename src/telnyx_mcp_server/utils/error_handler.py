"""Error handling utilities."""

import requests

from .logger import get_logger

logger = get_logger(__name__)


def handle_telnyx_error(error: Exception) -> Exception:
    """Handle Telnyx API errors.

    Args:
        error: Original error

    Returns:
        Exception: Handled error
    """
    if isinstance(error, requests.HTTPError):
        response = error.response
        try:
            data = response.json()
            if "errors" in data and isinstance(data["errors"], list):
                errors = data["errors"]
                if errors:
                    error_message = errors[0].get("detail", str(error))
                    return Exception(f"Telnyx API error: {error_message}")
        except Exception:
            pass
    return error
