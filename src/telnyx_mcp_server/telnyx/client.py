"""Telnyx API client."""

from typing import Any, Dict, Optional

import requests

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)


def mask_sensitive_data(data: Dict) -> Dict:
    """Mask sensitive data in dictionaries.

    Args:
        data: Dictionary potentially containing sensitive data

    Returns:
        Dict: Masked dictionary
    """
    result = {}

    for key, value in data.items():
        # Mask sensitive keys
        if any(
            sensitive in key.lower()
            for sensitive in ["key", "token", "auth", "password", "secret"]
        ):
            if isinstance(value, str):
                if len(value) > 8:
                    result[key] = f"{value[:5]}...{value[-3:]}"
                else:
                    result[key] = "[REDACTED]"
            else:
                result[key] = "[REDACTED]"
        # Handle nested dictionaries
        elif isinstance(value, dict):
            result[key] = mask_sensitive_data(value)
        # Handle lists potentially containing dictionaries
        elif isinstance(value, list):
            if value and isinstance(value[0], dict):
                result[key] = [
                    mask_sensitive_data(item)
                    if isinstance(item, dict)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        else:
            result[key] = value

    return result


class TelnyxClient:
    """Telnyx API client."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize the client.

        Args:
            api_key: Telnyx API key (optional if provided in headers)
            base_url: Base URL for Telnyx API (optional)
            headers: Optional headers dictionary containing authorization
        """
        logger.debug("Initializing TelnyxClient")
        self.api_key = api_key

        # Extract API key from headers if available
        if headers:
            logger.debug("Headers provided, checking for authorization")

            # Check Authorization header
            if "authorization" in headers:
                auth_header = headers.get("authorization", "")

                # Extract token from Bearer header
                if auth_header.lower().startswith("bearer "):
                    self.api_key = auth_header[7:]  # Remove "Bearer " prefix
                    logger.debug(
                        "Got API key from Bearer authorization header"
                    )
            else:
                logger.debug("No API key in headers")

        # Use the default API key from settings if none found
        if not self.api_key:
            logger.debug("Using default API key from settings")
            self.api_key = settings.telnyx_api_key

        # Log API key info (first few chars only for security)
        if self.api_key:
            masked_key = (
                "NONE"
                if not self.api_key
                else f"{self.api_key[:5]}..."
                if len(self.api_key) > 5
                else "[REDACTED]"
            )
            logger.debug(f"API key (masked): {masked_key}")
        else:
            logger.warning("No API key available")

        self.base_url = base_url or settings.telnyx_api_base_url
        logger.debug(f"Using base URL: {self.base_url}")

        self.session = requests.Session()
        logger.debug("Created requests Session")

        # Set up headers with authorization
        header_dict = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        logger.debug(f"Setting headers: {', '.join(header_dict.keys())}")
        self.session.headers.update(header_dict)
        logger.debug("TelnyxClient initialization complete")

    def get(
        self, path: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Make a GET request to the Telnyx API.

        Args:
            path: API path
            params: Query parameters

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"TELNYX REQUEST: GET {url}")
        logger.debug(f"TELNYX REQUEST PARAMS: {params}")

        # Log masked headers at debug level
        header_dict = dict(self.session.headers)
        masked_headers = mask_sensitive_data(header_dict)
        logger.debug(f"TELNYX REQUEST HEADERS: {masked_headers}")

        try:
            response = self.session.get(url, params=params)
            logger.info(f"TELNYX RESPONSE STATUS: {response.status_code}")
            logger.debug(f"TELNYX RESPONSE HEADERS: {dict(response.headers)}")

            if response.status_code >= 400:
                logger.error(f"TELNYX ERROR RESPONSE BODY: {response.text}")
            else:
                # Log a snippet of the successful response
                try:
                    response_json = response.json()
                    # Log full response at debug level, truncated at info level
                    logger.debug(
                        f"TELNYX RESPONSE FULL: {mask_sensitive_data(response_json)}"
                    )
                    logger.info(
                        f"TELNYX RESPONSE PREVIEW: {str(response_json)[:200]}..."
                    )
                except Exception as json_err:
                    logger.warning(
                        f"Could not parse response as JSON: {json_err}"
                    )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TELNYX REQUEST ERROR: {str(e)}")
            raise

    def post(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a POST request to the Telnyx API.

        Args:
            path: API path
            data: Request data

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"TELNYX REQUEST: POST {url}")

        # Log request data at debug level with sensitive information masked
        masked_data = mask_sensitive_data(data)
        logger.debug(f"TELNYX REQUEST DATA: {masked_data}")

        # Log masked headers at debug level
        header_dict = dict(self.session.headers)
        masked_headers = mask_sensitive_data(header_dict)
        logger.debug(f"TELNYX REQUEST HEADERS: {masked_headers}")

        try:
            response = self.session.post(url, json=data)
            logger.info(f"TELNYX RESPONSE STATUS: {response.status_code}")
            logger.debug(f"TELNYX RESPONSE HEADERS: {dict(response.headers)}")

            if response.status_code >= 400:
                logger.error(f"TELNYX ERROR RESPONSE BODY: {response.text}")
            else:
                # Log a snippet of the successful response
                try:
                    response_json = response.json()
                    # Log full response at debug level, truncated at info level
                    logger.debug(
                        f"TELNYX RESPONSE FULL: {mask_sensitive_data(response_json)}"
                    )
                    logger.info(
                        f"TELNYX RESPONSE PREVIEW: {str(response_json)[:200]}..."
                    )
                except Exception as json_err:
                    logger.warning(
                        f"Could not parse response as JSON: {json_err}"
                    )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TELNYX REQUEST ERROR: {str(e)}")
            raise

    def put(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PUT request to the Telnyx API.

        Args:
            path: API path
            data: Request data

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"TELNYX REQUEST: PUT {url}")

        # Log request data at debug level with sensitive information masked
        masked_data = mask_sensitive_data(data)
        logger.debug(f"TELNYX REQUEST DATA: {masked_data}")

        # Log masked headers at debug level
        header_dict = dict(self.session.headers)
        masked_headers = mask_sensitive_data(header_dict)
        logger.debug(f"TELNYX REQUEST HEADERS: {masked_headers}")

        try:
            response = self.session.put(url, json=data)
            logger.info(f"TELNYX RESPONSE STATUS: {response.status_code}")
            logger.debug(f"TELNYX RESPONSE HEADERS: {dict(response.headers)}")

            if response.status_code >= 400:
                logger.error(f"TELNYX ERROR RESPONSE BODY: {response.text}")
            else:
                # Log a snippet of the successful response
                try:
                    response_json = response.json()
                    # Log full response at debug level, truncated at info level
                    logger.debug(
                        f"TELNYX RESPONSE FULL: {mask_sensitive_data(response_json)}"
                    )
                    logger.info(
                        f"TELNYX RESPONSE PREVIEW: {str(response_json)[:200]}..."
                    )
                except Exception as json_err:
                    logger.warning(
                        f"Could not parse response as JSON: {json_err}"
                    )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TELNYX REQUEST ERROR: {str(e)}")
            raise

    def patch(self, path: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make a PATCH request to the Telnyx API.

        Args:
            path: API path
            data: Request data

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"TELNYX REQUEST: PATCH {url}")

        # Log request data at debug level with sensitive information masked
        masked_data = mask_sensitive_data(data)
        logger.debug(f"TELNYX REQUEST DATA: {masked_data}")

        # Log masked headers at debug level
        header_dict = dict(self.session.headers)
        masked_headers = mask_sensitive_data(header_dict)
        logger.debug(f"TELNYX REQUEST HEADERS: {masked_headers}")

        try:
            response = self.session.patch(url, json=data)
            logger.info(f"TELNYX RESPONSE STATUS: {response.status_code}")
            logger.debug(f"TELNYX RESPONSE HEADERS: {dict(response.headers)}")

            if response.status_code >= 400:
                logger.error(f"TELNYX ERROR RESPONSE BODY: {response.text}")
            else:
                # Log a snippet of the successful response
                try:
                    response_json = response.json()
                    # Log full response at debug level, truncated at info level
                    logger.debug(
                        f"TELNYX RESPONSE FULL: {mask_sensitive_data(response_json)}"
                    )
                    logger.info(
                        f"TELNYX RESPONSE PREVIEW: {str(response_json)[:200]}..."
                    )
                except Exception as json_err:
                    logger.warning(
                        f"Could not parse response as JSON: {json_err}"
                    )

            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"TELNYX REQUEST ERROR: {str(e)}")
            raise

    def delete(self, path: str) -> Dict[str, Any]:
        """Make a DELETE request to the Telnyx API.

        Args:
            path: API path

        Returns:
            Dict[str, Any]: Response data
        """
        url = f"{self.base_url}/{path.lstrip('/')}"
        logger.info(f"TELNYX REQUEST: DELETE {url}")

        # Log masked headers at debug level
        header_dict = dict(self.session.headers)
        masked_headers = mask_sensitive_data(header_dict)
        logger.debug(f"TELNYX REQUEST HEADERS: {masked_headers}")

        try:
            response = self.session.delete(url)
            logger.info(f"TELNYX RESPONSE STATUS: {response.status_code}")
            logger.debug(f"TELNYX RESPONSE HEADERS: {dict(response.headers)}")

            if response.status_code >= 400:
                logger.error(f"TELNYX ERROR RESPONSE BODY: {response.text}")

            response.raise_for_status()
            # Handle empty responses
            if not response.text:
                return {}
            return response.json()
        except Exception as e:
            logger.error(f"TELNYX REQUEST ERROR: {str(e)}")
            raise
