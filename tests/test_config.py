"""Tests for the configuration module."""

import os
from unittest import mock

import pytest

from telnyx_mcp_server.config import get_api_base_url


@pytest.mark.parametrize(
    "telnyx_api_base,expected_url",
    [
        ("http://foobar", "http://foobar"),
        (None, "https://api.telnyx.com/v2"),  # Test None value
    ],
)
def test_get_api_base_url(telnyx_api_base, expected_url):
    """Test that get_api_base_url returns the correct URL based on APP_ENV."""
    with mock.patch.dict(
        os.environ,
        {"TELNYX_API_BASE": telnyx_api_base}
        if telnyx_api_base is not None
        else {},
        clear=True,
    ):
        assert get_api_base_url() == expected_url
