"""MCP tools package."""

from .assistants import (
    create_assistant,
    get_assistant,
    get_assistant_texml,
    list_assistants,
    mcp_telnyx_delete_assistant,
    start_assistant_call,
    update_assistant,
)
from .call_control import (
    create_call_control_application,
    get_call_control_application,
    hangup,
    list_call_control_applications,
    make_call,
    playback_start,
    playback_stop,
    send_dtmf,
    speak,
    transfer,
)
from .connections import get_connection, list_connections, update_connection
from .messaging import get_message, send_message
from .messaging_profiles import (
    create_messaging_profile,
    get_messaging_profile,
    list_messaging_profiles,
    update_messaging_profile,
)
from .phone_numbers import (
    get_phone_number,
    initiate_phone_number_order,
    list_available_phone_numbers,
    list_phone_numbers,
    update_phone_number,
    update_phone_number_messaging_settings,
)

__all__ = [
    # Assistant tools
    "create_assistant",
    "get_assistant",
    "get_assistant_texml",
    "list_assistants",
    "mcp_telnyx_delete_assistant",
    "start_assistant_call",
    "update_assistant",
    # Call control tools
    "create_call_control_application",
    "get_call_control_application",
    "hangup",
    "list_call_control_applications",
    "make_call",
    "playback_start",
    "playback_stop",
    "send_dtmf",
    "speak",
    "transfer",
    # Connection tools
    "get_connection",
    "list_connections",
    "update_connection",
    # Messaging tools
    "send_message",
    "get_message",
    # Messaging profile tools
    "create_messaging_profile",
    "get_messaging_profile",
    "list_messaging_profiles",
    "update_messaging_profile",
    # Phone number tools
    "initiate_phone_number_order",
    "get_phone_number",
    "list_available_phone_numbers",
    "list_phone_numbers",
    "update_phone_number",
    "update_phone_number_messaging_settings",
]
