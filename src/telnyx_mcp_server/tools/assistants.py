"""Assistant related MCP tools."""

from typing import Any, Dict

from pydantic import Field

from ..mcp import mcp
from ..telnyx.services.assistants import AssistantsService
from ..utils.error_handler import handle_telnyx_error
from ..utils.logger import get_logger
from ..utils.service import get_authenticated_service

logger = get_logger(__name__)


@mcp.tool()
async def create_assistant(request: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new AI Assistant. The user will provide some details (sometimes
    detailed, sometimes vague) about the agent they want to create.

    Args:
        name: Required. Name of the assistant. If not provided, will be generated based on context.
        model: Required. Model to use for the assistant. Defaults to meta-llama/Meta-Llama-3.1-70B-Instruct.
        instructions: Required. Core instructions or behaviors for the agent.
        description: Optional. A summary of the agent's purpose.
        tools: Optional. List of tools for the assistant, each containing:
            - type: Required. Type of tool ("function", "retrieval", "webhook",
            "hangup", "send_dtmf", "transfer").
            - function: Optional. For function tools, contains:
                - name: Required. Name of the function.
                - description: Optional. Description of the function.
                - parameters: Required. Parameters schema for the function.
            - retrieval: Optional. For retrieval tools, contains:
                - bucket_ids: Required. List of bucket IDs for retrieval.
                - max_num_results: Optional. Maximum number of results to retrieve.
            - webhook: Optional. For webhook tools, contains:
                - name: Required. The name of the tool.
                - description: Required. The description of the tool.
                - url: Required. The URL of the external tool to be called. This URL can be
                  templated like: https://example.com/api/v1/{id}, where {id} is a
                  placeholder for a value that will be provided by the assistant if
                  path_parameters are provided with the id attribute.
                - method: Optional. The HTTP method to be used. Possible values:
                  [GET, POST, PUT, DELETE, PATCH]. Default value: POST.
                - headers: Optional. Array of header objects with:
                    - name: String name of the header.
                    - value: String value of the header. Supports mustache templating.
                      e.g., Bearer {{#integration_secret}}test-secret{{/integration_secret}}.
                      Secrets can be found in `list_integration_secrets`
                - body_parameters: Optional. JSON Schema object describing the body parameters:
                    - properties: Object defining the properties of the body parameters.
                    - required: Array of strings listing required properties.
                    - type: String. Possible value: "object".
                - path_parameters: Optional. JSON Schema object describing the path parameters:
                    - properties: Object defining the properties of the path parameters.
                    - required: Array of strings listing required properties.
                    - type: String. Possible value: "object".
                - query_parameters: Optional. JSON Schema object describing the query parameters:
                    - properties: Object defining the properties of the query parameters.
                    - required: Array of strings listing required properties.
                    - type: String. Possible value: "object".
            - hangup: Optional. For hangup tools, contains:
                - description: Optional. Description of the hangup function. Defaults to
                  "This tool is used to hang up the call."
            - send_dtmf: Optional. For DTMF tools, contains an empty object. This tool
              allows sending DTMF tones during a call.
            - transfer: Optional. For transfer tools, contains:
                - targets: Required. Array of transfer targets, each with:
                    - name: Optional. Name of the target.
                    - to: Required. Destination number or SIP URI.
                - from: Required. Number or SIP URI placing the call.
                - custom_headers: Optional. Array of custom SIP headers, each with:
                    - name: Required. Name of the header.
                    - value: Required. Value of the header. Supports mustache templating.
        greeting: Optional. A short welcoming message. Will be generated if not provided.
        llm_api_key_ref: Optional. LLM API key reference.
        transcription: Optional. Transcription settings with:
            - model: Optional. Model to use for transcription.
        messaging_settings: Optional. Messaging settings with:
            - default_messaging_profile_id: Optional. Default messaging profile ID.
            - delivery_status_webhook_url: Optional. Webhook URL for delivery status updates.
        insight_settings: Optional. Insight settings with:
            - insight_group_id: Optional. Insight group ID.
        dynamic_variables_webhook_url: Optional. Dynamic variables webhook URL.
        dynamic_variables: Optional. Dynamic variables dictionary.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(AssistantsService)
        return service.create_assistant(request)
    except Exception as e:
        logger.error(f"Error creating assistant: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def list_assistants() -> Dict[str, Any]:
    """List all AI Assistants.

    Returns:
        Dict[str, Any]: List of assistants
    """
    try:
        service = get_authenticated_service(AssistantsService)
        return service.list_assistants()
    except Exception as e:
        logger.error(f"Error listing assistants: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def get_assistant(request: Dict[str, Any]) -> Dict[str, Any]:
    """Get an AI Assistant by ID.

    Args:
        assistant_id: Required. Assistant ID.
        fetch_dynamic_variables_from_webhook: Optional boolean. Whether to fetch dynamic variables from webhook.
        from_: Optional. From parameter for dynamic variables.
        to: Optional. To parameter for dynamic variables.
        call_control_id: Optional. Call control ID for dynamic variables.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(AssistantsService)
        return service.get_assistant(
            assistant_id=request["assistant_id"],
            fetch_dynamic_variables_from_webhook=request.get(
                "fetch_dynamic_variables_from_webhook"
            ),
            from_=request.get("from_"),
            to=request.get("to"),
            call_control_id=request.get("call_control_id"),
        )
    except Exception as e:
        logger.error(f"Error getting assistant: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def update_assistant(
    assistant_id: str, request: Dict[str, Any]
) -> Dict[str, Any]:
    """Update an AI Assistant. Once there is an agent created, you can talk the
    user about what can be updated in an easy manner, rather than asking for a
    long list of fields to update.

    Args:
        assistant_id: Required. ID of the assistant to update.
        name: Optional. Name of the assistant.
        model: Optional. Model to use for the assistant.
        instructions: Optional. Core instructions or behaviors for the agent.
        description: Optional. A summary of the agent's purpose.
        tools: Optional. List of tools for the assistant, each containing:
            - type: Required. Type of tool (ANY of "hangup", "retrieval", "send_dtmf",
              "transfer", "webhook").
            - retrieval: Optional. For retrieval tools, contains:
                - bucket_ids: Required. List of bucket IDs for retrieval.
                - max_num_results: Optional. Maximum number of results to retrieve.
            - webhook: Optional. For webhook tools, contains:
                - name: Required. The name of the tool.
                - description: Required. The description of the tool.
                - url: Required. The URL of the external tool to be called. This URL can be
                  templated like: https://example.com/api/v1/{id}, where {id} is a
                  placeholder for a value that will be provided by the assistant if
                  path_parameters are provided with the id attribute.
                - method: Optional. The HTTP method to be used. Possible values:
                  [GET, POST, PUT, DELETE, PATCH]. Default value: POST.
                - headers: Optional. Array of header objects with:
                    - name: String name of the header.
                    - value: String value of the header. Supports mustache templating,
                      e.g., Bearer {{#integration_secret}}test-secret{{/integration_secret}}.
                      Secrets can be found in `list_integration_secrets`
                - body_parameters: Optional. JSON Schema object describing the body parameters:
                    - properties: Object defining the properties of the body parameters.
                    - required: Array of strings listing required properties.
                    - type: String. Possible value: "object".
                - path_parameters: Optional. JSON Schema object describing the path parameters:
                    - properties: Object defining the properties of the path parameters.
                    - required: Array of strings listing required properties.
                    - type: String. Possible value: "object".
                - query_parameters: Optional. JSON Schema object describing the query parameters:
                    - properties: Object defining the properties of the query parameters.
                    - required: Array of strings listing required properties.
                    - type: String. Possible value: "object".
            - hangup: Optional. For hangup tools, contains:
                - description: Optional. Description of the hangup function.
            - send_dtmf: Optional. For DTMF tools, contains an empty object. This tool
              allows sending DTMF tones during a call.
            - transfer: Optional. For transfer tools, contains:
                - targets: Required. Array of transfer targets, each with:
                    - name: Optional. Name of the target.
                    - to: Required. Destination number or SIP URI.
                - from: Required. Number or SIP URI placing the call.
                - custom_headers: Optional. Array of custom SIP headers, each with:
                    - name: Required. Name of the header.
                    - value: Required. Value of the header. Supports mustache templating.
                    eg: {{#integration_secret}}test-secret{{/integration_secret}}
                    to be used with integration secrets (Available secrets can be
                    found in `list_integration_secrets`)
        greeting: Optional. A short welcoming message used by the agent.
        llm_api_key_ref: Optional. LLM API key reference. This is meant to be used
        for models provided by external vendors. eg: openai, anthropic, Groq, xai-org.
        Available secrets can be found in `list_integration_secrets`
        transcription: Optional. Transcription settings with:
            - model: Optional. Model to use for transcription.
        telephony_settings: Optional. Telephony settings with:
            - default_texml_app_id: Optional. Default TeXML application ID.
        messaging_settings: Optional. Messaging settings with:
            - default_messaging_profile_id: Optional. Default messaging profile ID.
            - delivery_status_webhook_url: Optional. Webhook URL for delivery status updates.
        insight_settings: Optional. Insight settings with:
            - insight_group_id: Optional. Insight group ID.
        dynamic_variables_webhook_url: Optional. Dynamic variables webhook URL.
        dynamic_variables: Optional. Dynamic variables dictionary.

    Returns:
        Dict[str, Any]: Response data
    """
    try:
        service = get_authenticated_service(AssistantsService)
        return service.update_assistant(assistant_id, request)
    except Exception as e:
        logger.error(f"Error updating assistant: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def mcp_telnyx_delete_assistant(
    id: str = Field(..., description="Assistant ID as string"),
) -> Dict[str, Any]:
    """Delete an AI Assistant.

    Args:
        id: Assistant ID as string

    Returns:
        Dict[str, Any]: Response data containing deletion status
    """
    try:
        service = get_authenticated_service(AssistantsService)
        return service.delete_assistant(id)
    except Exception as e:
        logger.error(f"Error deleting assistant: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def get_assistant_texml(
    assistant_id: str = Field(..., description="Assistant ID"),
) -> str:
    """Get an assistant's TEXML by ID.

    Args:
        assistant_id: Assistant ID

    Returns:
        str: Assistant TEXML content
    """
    try:
        service = get_authenticated_service(AssistantsService)
        return service.get_assistant_texml(assistant_id)
    except Exception as e:
        logger.error(f"Error getting assistant TEXML: {e}")
        raise handle_telnyx_error(e)


@mcp.tool()
async def start_assistant_call(
    assistant_id: str,
    to: str,
    from_: str,
) -> Dict[str, Any]:
    """Start a call using an AI Assistant with a phone number.

    Args:
        assistant_id: Required. ID of the assistant to use for the call.
        to: Required. Destination phone number to call.
        from_: Required. Source phone number to call from (must be a number on your Telnyx account).

    Returns:
        Dict[str, Any]: Response data from the call initiation
    """
    try:
        # First, get the assistant to retrieve the default_texml_app_id
        service = get_authenticated_service(AssistantsService)
        assistant = service.get_assistant(assistant_id=assistant_id)

        # Extract the default_texml_app_id from the assistant
        if (
            not assistant
            or not assistant.get("telephony_settings")
            or not assistant["telephony_settings"].get("default_texml_app_id")
        ):
            raise ValueError(
                "The assistant does not have a default TeXML application ID configured"
            )

        default_texml_app_id = assistant["telephony_settings"][
            "default_texml_app_id"
        ]

        # Start the call
        response = service.start_assistant_call(
            default_texml_app_id=default_texml_app_id, to=to, from_=from_
        )
        return response
    except Exception as e:
        logger.error(f"Error starting assistant call: {e}")
        raise handle_telnyx_error(e)
