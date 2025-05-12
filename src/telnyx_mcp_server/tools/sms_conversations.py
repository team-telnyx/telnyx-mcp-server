"""SMS Conversations resource for MCP server."""

from collections import defaultdict
from datetime import datetime
from typing import Any, Dict

from ..mcp import mcp
from ..utils.logger import get_logger
from ..webhook import get_webhook_history

logger = get_logger(__name__)

# Resource URI for SMS conversations
SMS_CONVERSATIONS_URI = "resource://sms/conversations"


def _extract_conversation_details(webhook_events):
    """
    Extract SMS conversation details from webhook events.

    This function organizes SMS events into conversations based on phone numbers.
    It tracks messages between the same pair of numbers.

    Args:
        webhook_events: List of webhook events

    Returns:
        List of conversation summaries
    """
    # Dictionary to store conversations by conversation ID (combo of to/from numbers)
    conversations = defaultdict(
        lambda: {
            "messages": [],
            "participants": set(),
            "last_message_time": None,
            "started_at": None,
        }
    )

    # Process all webhook events
    for event in webhook_events:
        # Check if this is an SMS-related event
        event_type = event.get("event_type", "")
        payload = event.get("payload", {})

        if "message" in event_type.lower() or "sms" in event_type.lower():
            try:
                # Handle Telnyx webhook structure which has nested payload
                data_payload = None

                # First try to navigate through the Telnyx webhook structure
                if payload and "data" in payload:
                    data = payload["data"]
                    if "payload" in data:
                        data_payload = data["payload"]

                # If we found the proper payload structure, use it
                if data_payload:
                    # Extract from phone number
                    from_info = data_payload.get("from", {})
                    from_number = None
                    if (
                        isinstance(from_info, dict)
                        and "phone_number" in from_info
                    ):
                        from_number = from_info["phone_number"]
                    elif isinstance(from_info, str):
                        from_number = from_info

                    # Extract to phone number
                    to_info = data_payload.get("to", [])
                    to_number = None
                    if isinstance(to_info, list) and len(to_info) > 0:
                        first_to = to_info[0]
                        if (
                            isinstance(first_to, dict)
                            and "phone_number" in first_to
                        ):
                            to_number = first_to["phone_number"]
                    elif (
                        isinstance(to_info, dict) and "phone_number" in to_info
                    ):
                        to_number = to_info["phone_number"]
                    elif isinstance(to_info, str):
                        to_number = to_info

                    # Get message text
                    message_text = data_payload.get("text", "")

                    # Extract direction and timestamp
                    direction = data_payload.get("direction", "")

                    # Try different timestamp fields
                    message_time = None
                    timestamp_fields = [
                        "received_at",
                        "sent_at",
                        "completed_at",
                        "timestamp",
                    ]
                    for field in timestamp_fields:
                        if field in data_payload and data_payload[field]:
                            message_time = data_payload[field]
                            break

                    if not message_time:
                        occurred_at = data.get("occurred_at")
                        if occurred_at:
                            message_time = occurred_at
                        else:
                            message_time = event.get(
                                "timestamp", datetime.now().isoformat()
                            )
                else:
                    # Fallback to simpler webhook format
                    # Extract message details from payload
                    data = payload.get("data", payload)

                    # Extract message details
                    from_number = None
                    from_info = data.get("from", {})
                    if (
                        isinstance(from_info, dict)
                        and "phone_number" in from_info
                    ):
                        from_number = from_info["phone_number"]
                    elif isinstance(from_info, str):
                        from_number = from_info

                    to_number = None
                    # Handle different payload structures
                    to_info = data.get("to", [])
                    if isinstance(to_info, list) and len(to_info) > 0:
                        first_to = to_info[0]
                        if (
                            isinstance(first_to, dict)
                            and "phone_number" in first_to
                        ):
                            to_number = first_to["phone_number"]
                    elif (
                        isinstance(to_info, dict) and "phone_number" in to_info
                    ):
                        to_number = to_info["phone_number"]
                    elif isinstance(to_info, str):
                        to_number = to_info

                    # Extract message content
                    message_text = data.get("text", "")

                    # Try different timestamp fields based on webhook format
                    timestamp_fields = [
                        "timestamp",
                        "received_at",
                        "sent_at",
                        "created_at",
                        "updated_at",
                    ]
                    message_time = None
                    for field in timestamp_fields:
                        if field in data and data[field]:
                            message_time = data[field]
                            break

                    if not message_time:
                        message_time = event.get(
                            "timestamp", datetime.now().isoformat()
                        )

                    # Determine direction
                    direction = data.get("direction", "")

                # Skip if we can't identify the numbers
                if not from_number or not to_number:
                    logger.warning(
                        f"Could not identify from or to number in event: {event_type}"
                    )
                    continue

                # Create a unique conversation ID (sort numbers to ensure consistency)
                conv_participants = sorted([from_number, to_number])
                conversation_id = (
                    f"{conv_participants[0]}:{conv_participants[1]}"
                )

                # Determine direction if not already set
                if not direction:
                    if "outbound" in event_type.lower():
                        direction = "outbound"
                    elif (
                        "inbound" in event_type.lower()
                        or "received" in event_type.lower()
                    ):
                        direction = "inbound"
                    else:
                        direction = "unknown"

                # Get message ID if available
                message_id = None
                if data_payload and "id" in data_payload:
                    message_id = data_payload["id"]
                elif "id" in data:
                    message_id = data["id"]

                # Create message object
                message = {
                    "id": message_id,
                    "from": from_number,
                    "to": to_number,
                    "text": message_text,
                    "timestamp": message_time,
                    "direction": direction,
                    "event_type": event_type,
                }

                # Log the extracted message for debugging
                logger.debug(
                    f"Extracted message: {from_number} -> {to_number}: '{message_text}'"
                )

                # Add/update conversation details
                conversations[conversation_id]["messages"].append(message)
                conversations[conversation_id]["participants"].add(from_number)
                conversations[conversation_id]["participants"].add(to_number)

                # Update timestamps
                if not conversations[conversation_id]["started_at"]:
                    conversations[conversation_id]["started_at"] = message_time

                conversations[conversation_id]["last_message_time"] = (
                    message_time
                )
            except Exception as e:
                logger.error(f"Error processing message event: {e}")
                continue

    # Convert to list of conversations
    result = []
    for conv_id, data in conversations.items():
        # Only include conversations with at least one message
        if len(data["messages"]) > 0:
            # Sort messages by timestamp
            sorted_messages = sorted(
                data["messages"], key=lambda m: m.get("timestamp", "")
            )

            # Create conversation summary
            conversation = {
                "conversation_id": conv_id,
                "participants": list(data["participants"]),
                "message_count": len(sorted_messages),
                "started_at": data["started_at"],
                "last_message_time": data["last_message_time"],
                "last_message": sorted_messages[-1]["text"]
                if sorted_messages
                else "",
                "messages": sorted_messages,
            }

            result.append(conversation)

    # Sort conversations by last message time (most recent first)
    return sorted(
        result, key=lambda c: c.get("last_message_time", ""), reverse=True
    )


@mcp.resource(SMS_CONVERSATIONS_URI)
def get_sms_conversations() -> Dict[str, Any]:
    """
    Get a list of ongoing SMS conversations.

    This resource extracts and organizes SMS conversations from webhook events.

    Returns:
        Dict[str, Any]: List of SMS conversations with participants and messages
    """
    try:
        # Get all webhook history
        webhook_events = get_webhook_history()

        # Log webhook count
        logger.info(f"Got {len(webhook_events)} webhook events for processing")

        # Log some details about the first event
        if webhook_events:
            first_event = webhook_events[0]
            event_type = first_event.get("event_type", "unknown")
            logger.info(f"First event type: {event_type}")

            # Log structure of webhook payload
            logger.info(
                f"Webhook payload structure: {list(first_event.keys())}"
            )
            if "payload" in first_event:
                payload = first_event["payload"]
                if isinstance(payload, dict):
                    logger.info(f"Payload keys: {list(payload.keys())}")

                    # Log data structure if present
                    if "data" in payload:
                        data = payload["data"]
                        if isinstance(data, dict):
                            logger.info(f"Data keys: {list(data.keys())}")

                            # Log inner payload structure if present
                            if "payload" in data:
                                inner_payload = data["payload"]
                                if isinstance(inner_payload, dict):
                                    logger.info(
                                        f"Inner payload keys: {list(inner_payload.keys())}"
                                    )

        # Extract conversations from webhook events
        conversations = _extract_conversation_details(webhook_events)

        # Log the number of conversations found
        logger.info(
            f"Found {len(conversations)} SMS conversations from webhook history"
        )

        return {
            "conversations": conversations,
            "count": len(conversations),
            "updated_at": datetime.now().isoformat(),
            "source": "webhook_history",
            "webhook_count": len(webhook_events),
        }
    except Exception as e:
        logger.error(f"Error retrieving SMS conversations: {e}")
        logger.error(f"Exception traceback: {str(e.__traceback__)}")
        return {
            "error": f"Failed to retrieve SMS conversations: {str(e)}",
            "conversations": [],
            "count": 0,
            "updated_at": datetime.now().isoformat(),
        }


@mcp.resource("resource://sms/recent/{limit}")
def get_recent_conversations(limit: int = 5) -> Dict[str, Any]:
    """
    Get a list of the most recent SMS conversations.

    Args:
        limit: Maximum number of conversations to return

    Returns:
        Dict[str, Any]: List of recent SMS conversations with participants and messages
    """
    try:
        # Get all conversations
        all_conversations = get_sms_conversations()

        # Get the conversations (they're already sorted by most recent first)
        conversations = all_conversations.get("conversations", [])

        # Limit the number of conversations
        limited_conversations = conversations[: min(limit, len(conversations))]

        return {
            "conversations": limited_conversations,
            "count": len(limited_conversations),
            "total_available": len(conversations),
            "limit": limit,
            "updated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Error retrieving recent conversations: {e}")
        return {
            "error": f"Failed to retrieve recent conversations: {str(e)}",
            "conversations": [],
            "count": 0,
            "updated_at": datetime.now().isoformat(),
        }


# Resource template for individual conversations
@mcp.resource("resource://sms/conversation/{conversation_id}")
def get_sms_conversation(conversation_id: str) -> Dict[str, Any]:
    """
    Get details for a specific SMS conversation.

    Args:
        conversation_id: The ID of the conversation (format: "number1:number2")

    Returns:
        Dict[str, Any]: Detailed conversation data including all messages
    """
    try:
        # Get all conversations
        all_conversations = get_sms_conversations()

        # Find the specific conversation
        for conversation in all_conversations.get("conversations", []):
            if conversation.get("conversation_id") == conversation_id:
                return {
                    "conversation": conversation,
                    "updated_at": datetime.now().isoformat(),
                }

        # Conversation not found
        return {
            "error": f"Conversation {conversation_id} not found",
            "updated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(
            f"Error retrieving SMS conversation {conversation_id}: {e}"
        )
        return {
            "error": f"Failed to retrieve SMS conversation: {str(e)}",
            "updated_at": datetime.now().isoformat(),
        }


# Resource template for conversations by phone number
@mcp.resource("resource://sms/by_number/{phone_number}")
def get_conversations_by_number(phone_number: str) -> Dict[str, Any]:
    """
    Get all conversations involving a specific phone number.

    Args:
        phone_number: The phone number to find conversations for

    Returns:
        Dict[str, Any]: List of conversations involving the phone number
    """
    try:
        # Get all conversations
        all_conversations = get_sms_conversations()

        # Filter conversations by phone number
        matching_conversations = []
        for conversation in all_conversations.get("conversations", []):
            participants = conversation.get("participants", [])
            if phone_number in participants:
                matching_conversations.append(conversation)

        return {
            "phone_number": phone_number,
            "conversations": matching_conversations,
            "count": len(matching_conversations),
            "updated_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(
            f"Error retrieving conversations for number {phone_number}: {e}"
        )
        return {
            "error": f"Failed to retrieve conversations: {str(e)}",
            "phone_number": phone_number,
            "conversations": [],
            "count": 0,
            "updated_at": datetime.now().isoformat(),
        }
