"""Call control related MCP tools."""

from typing import Any, Dict

from ..mcp import mcp
from ..telnyx.services.call_control import CallControlService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def list_call_control_applications(
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """List call control applications.

    Args:
        page: Optional integer. Page number. Defaults to 1.
        page_size: Optional integer. Page size. Defaults to 20.
        filter_application_name_contains: Optional. Filter by application name (case-insensitive, min 3 characters).
        filter_outbound_voice_profile_id: Optional. Filter by associated outbound voice profile ID.
        sort: Optional. Sort order for results (created_at, connection_name, active). Defaults to created_at.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(CallControlService)
        return service.list_call_control_applications(request)
    except Exception as e:
        logger.error(f"Error listing call control applications: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def get_call_control_application(
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Retrieve a specific call control application.

    Args:
        id: Required. Identifies the call control application.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(CallControlService)
        return service.get_call_control_application(request)
    except Exception as e:
        logger.error(f"Error retrieving call control application: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def create_call_control_application(
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a call control application.

     Args:
        application_name: Required. A user-assigned name to help manage the application.
        webhook_event_url: Required. The URL where webhooks related to this connection will be sent. Must include a scheme, such as 'https'.
        active: Optional boolean. Specifies whether the connection can be used. Defaults to True.
        anchorsite_override: Optional. Directs Telnyx to route media through the site with the lowest round-trip time. Defaults to "Latency".
        dtmf_type: Optional. Sets the type of DTMF digits sent from Telnyx to this Connection. Defaults to "RFC 2833".
        first_command_timeout: Optional boolean. Specifies whether calls should hangup after timing out.
        first_command_timeout_secs: Optional integer. Seconds to wait before timing out a dial command. Defaults to 30.
        inbound: Optional dictionary. Inbound call settings with these possible keys:
            - channel_limit: Optional integer. Maximum number of concurrent inbound calls.
            - shaken_stir_enabled: Optional boolean. Enable SHAKEN/STIR verification for inbound calls.
            - sip_subdomain: Optional string. SIP subdomain for the application.
            - sip_subdomain_receive_settings: Optional string. Settings for SIP subdomain receiving.
        outbound: Optional dictionary. Outbound call settings with these possible keys:
            - channel_limit: Optional integer. Maximum number of concurrent outbound calls.
            - outbound_voice_profile_id: Optional string. ID of the outbound voice profile to use.
        webhook_api_version: Optional. Determines which webhook format will be used. Defaults to "1".
        webhook_event_failover_url: Optional. The failover URL for webhooks if the primary URL fails.
        webhook_timeout_secs: Optional integer. Seconds to wait before timing out a webhook.
    Returns:
     Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(CallControlService)
        return service.create_call_control_application(request)
    except Exception as e:
        logger.error(f"Error creating call control application: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def make_call(request: Dict[str, Any]) -> Dict[str, Any]:
    """Make a call.

    Args:
        to: Required. Destination number or SIP URI.
        from_: Required. Source number.
        connection_id: Optional. Connection ID of a call control application to use for the call (same as call_control_application_id).

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(CallControlService)
        return service.make_call(request)
    except Exception as e:
        logger.error(f"Error making call: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def hangup(request: Dict[str, Any]) -> Dict[str, Any]:
    """Hang up a call.

    Args:
        call_control_id: Required. Call control ID.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        call_control_id = request.pop("call_control_id")
        service = get_authenticated_service(CallControlService)
        return service.hangup(call_control_id, request)
    except Exception as e:
        logger.error(f"Error hanging up call: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def playback_start(request: Dict[str, Any]) -> Dict[str, Any]:
    """Start audio playback on a call.

    Args:
        call_control_id: Required. Call control ID.
        audio_url: Required. URL of audio file to play.
        loop: Optional. Number of times to loop the audio. Valid values: infinity, 1, 2, 3, 4, 5.
        overlay: Optional boolean. Whether to overlay the audio on existing audio. Defaults to False.
        stop: Optional. Which audio to stop. Valid values: current, all.
        target_legs: Optional. Which leg(s) to play the audio on. Valid values: self, peer, both.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        call_control_id = request.pop("call_control_id")
        service = get_authenticated_service(CallControlService)
        return service.playback_start(call_control_id, request)
    except Exception as e:
        logger.error(f"Error starting playback: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def playback_stop(request: Dict[str, Any]) -> Dict[str, Any]:
    """Stop audio playback on a call.

    Args:
        call_control_id: Required. Call control ID.
        overlay: Optional boolean. Whether to stop overlay audio. Defaults to False.
        stop: Optional. Which audio to stop. Valid values: current, all.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        call_control_id = request.pop("call_control_id")
        service = get_authenticated_service(CallControlService)
        return service.playback_stop(call_control_id, request)
    except Exception as e:
        logger.error(f"Error stopping playback: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def send_dtmf(request: Dict[str, Any]) -> Dict[str, Any]:
    """Send DTMF tones on a call.

    Args:
        call_control_id: Required. Call control ID.
        digits: Required. DTMF digits to send (0-9, *, #, w, W).
        duration_millis: Optional integer. Duration of each digit in milliseconds. Defaults to 500.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        call_control_id = request.pop("call_control_id")
        service = get_authenticated_service(CallControlService)
        return service.send_dtmf(call_control_id, request)
    except Exception as e:
        logger.error(f"Error sending DTMF: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def speak(request: Dict[str, Any]) -> Dict[str, Any]:
    """Speak text on a call using text-to-speech.

    Args:
        call_control_id: Required. Call control ID.
        payload: Required. Text to speak.
        voice: Required. Voice to use. Defaults to female
        payload_type: Optional. Type of payload. Valid values: text, ssml. Defaults to "text".
        service_level: Optional. Service level for TTS. Valid values: basic, premium. Defaults to "basic".
        stop: Optional. Which audio to stop. Valid values: current, all.
        language: Optional. Language code (e.g., 'en-US', 'arb').

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        call_control_id = request.pop("call_control_id")
        service = get_authenticated_service(CallControlService)
        return service.speak(call_control_id, request)
    except Exception as e:
        logger.error(f"Error speaking text: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def transfer(request: Dict[str, Any]) -> Dict[str, Any]:
    """Transfer a call to a new destination.

    Args:
        call_control_id: Required. Call control ID.
        to: Required. Destination number or SIP URI.
        from_: Required. Source number.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        call_control_id = request.pop("call_control_id")
        service = get_authenticated_service(CallControlService)
        return service.transfer(call_control_id, request)
    except Exception as e:
        logger.error(f"Error transferring call: {e}")
        raise handle_telnyx_error(e)
