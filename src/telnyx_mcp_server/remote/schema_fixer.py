"""Fix tool schemas for better Claude.ai compatibility."""

from typing import Dict, Any


def fix_tool_schema(tool: Dict[str, Any]) -> Dict[str, Any]:
    """Fix tool schema by extracting properties from nested request object.
    
    This transforms schemas from:
    {
        "properties": {
            "request": {
                "type": "object"
            }
        },
        "required": ["request"]
    }
    
    To a flat structure with actual properties defined.
    """
    # For now, return the tool as-is since we need the actual property definitions
    # from the docstrings. This would require parsing the docstrings to extract
    # the parameter definitions.
    
    # A proper fix would be to refactor all tools to use individual parameters
    # instead of request: Dict[str, Any]
    
    return tool


# Tool-specific schema overrides for common tools
SCHEMA_OVERRIDES = {
    "send_message": {
        "type": "object",
        "properties": {
            "from_": {
                "type": "string",
                "description": "Sending address (phone number, alphanumeric sender ID, or short code)"
            },
            "to": {
                "type": "string", 
                "description": "Receiving address"
            },
            "text": {
                "type": "string",
                "description": "Message text"
            },
            "messaging_profile_id": {
                "type": "string",
                "description": "Messaging profile ID (optional)"
            }
        },
        "required": ["from_", "to", "text"]
    },
    "list_phone_numbers": {
        "type": "object",
        "properties": {
            "page": {
                "type": "integer",
                "description": "Page number",
                "default": 1
            },
            "page_size": {
                "type": "integer", 
                "description": "Page size",
                "default": 20
            },
            "filter_phone_number": {
                "type": "string",
                "description": "Filter by phone number"
            },
            "filter_status": {
                "type": "string",
                "description": "Filter by status"
            },
            "filter_voice_enabled": {
                "type": "boolean",
                "description": "Filter by voice enabled"
            }
        }
    },
    "get_message": {
        "type": "object",
        "properties": {
            "message_id": {
                "type": "string",
                "description": "The ID of the message to retrieve"
            }
        },
        "required": ["message_id"]
    }
}


def get_fixed_schema(tool_name: str, original_schema: Dict[str, Any]) -> Dict[str, Any]:
    """Get the fixed schema for a tool."""
    if tool_name in SCHEMA_OVERRIDES:
        return SCHEMA_OVERRIDES[tool_name]
    
    # For tools with simple parameters (not using request dict), return as-is
    if "request" not in original_schema.get("properties", {}):
        return original_schema
        
    # For others, we'd need to parse docstrings or refactor the tools
    return original_schema