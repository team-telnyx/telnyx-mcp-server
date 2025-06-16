"""Remote MCP server implementation for Telnyx using FastAPI."""

from fastapi import FastAPI, HTTPException, Request, Depends, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, RedirectResponse
from sse_starlette.sse import EventSourceResponse
from typing import Any, Dict, Optional, List, Union
import logging
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import json
import asyncio
from datetime import datetime
import httpx
import urllib.parse
import secrets
import time
import hashlib
import base64

# Import authentication
from .auth import (
    AuthService, get_current_user, optional_auth,
    AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, AZURE_REDIRECT_URI, AZURE_TENANT_ID,
    AZURE_TOKEN_URL
)
from .auth_store import auth_store

# Import existing Telnyx MCP components
from ..mcp import mcp
from ..config import settings
from ..utils.logger import get_logger

# Load environment variables
load_dotenv()

# Configure logging
logger = get_logger(__name__)

# Version information
__version__ = "0.5.0"
PROTOCOL_VERSION = "2025-03-26"


class TelnyxMCPServer:
    """Telnyx MCP Server implementation."""
    
    def __init__(self):
        """Initialize the MCP server with Telnyx tools."""
        self.tools = {}
        self.resources = {}
        self._tools_initialized = False
        self._initialized_sessions = set()  # Track initialized sessions
    
    async def initialize_tools(self):
        """Initialize tools from MCP instance if not already done."""
        if self._tools_initialized:
            return
            
        try:
            # Import all Telnyx tools to ensure they're registered with MCP
            from ..tools import (
                assistants,
                call_control,
                cloud_storage,
                connections,
                embeddings,
                messaging,
                messaging_profiles,
                phone_numbers,
                secrets,
                webhooks
            )
            
            # Get the list of tools from MCP
            tools_list = await mcp.list_tools()
            
            # Convert to dict format
            self.tools = {
                tool.name: {
                    "name": tool.name,
                    "description": tool.description or "",
                    "inputSchema": tool.inputSchema
                }
                for tool in tools_list
            }
            
            self._tools_initialized = True
            logger.info(f"Initialized {len(self.tools)} Telnyx tools")
            
        except Exception as e:
            logger.error(f"Failed to initialize tools: {e}", exc_info=True)
            self._tools_initialized = False
    
    def _extract_parameters_from_docstring(self, docstring: str) -> Dict[str, Any]:
        """Extract parameter definitions from tool docstring."""
        if not docstring:
            return {"type": "object", "properties": {}, "required": []}
        
        lines = docstring.split('\n')
        in_args = False
        properties = {}
        required = []
        
        for line in lines:
            line = line.strip()
            
            # Start of Args section
            if line.startswith("Args:"):
                in_args = True
                continue
            
            # End of Args section
            if in_args and (line.startswith("Returns:") or line == "" and not lines):
                break
            
            # Parse parameter lines
            if in_args and line:
                # Match parameter definition pattern
                if ":" in line:
                    parts = line.split(":", 1)
                    param_name = parts[0].strip()
                    description = parts[1].strip() if len(parts) > 1 else ""
                    
                    # Extract type and required status from description
                    is_required = "Required." in description or "required." in description
                    is_optional = "Optional" in description or "optional" in description
                    
                    # Determine type from description
                    param_type = "string"  # default
                    if "boolean" in description.lower() or "bool" in description.lower():
                        param_type = "boolean"
                    elif "integer" in description.lower() or "int" in description.lower():
                        param_type = "integer"
                    elif "number" in description.lower() or "float" in description.lower():
                        param_type = "number"
                    elif "array" in description.lower() or "list" in description.lower():
                        param_type = "array"
                    elif "object" in description.lower() or "dict" in description.lower():
                        param_type = "object"
                    
                    # Clean up parameter name (remove trailing underscore)
                    clean_name = param_name.rstrip('_')
                    
                    properties[clean_name] = {
                        "type": param_type,
                        "description": description
                    }
                    
                    if is_required and not is_optional:
                        required.append(clean_name)
        
        return {
            "type": "object",
            "properties": properties,
            "required": required
        }
    
    def _transform_tool_schema(self, tool: Dict[str, Any]) -> Dict[str, Any]:
        """Transform tool schema to flatten nested request objects."""
        # Create a copy of the tool
        transformed = tool.copy()
        
        # Check if this tool has the nested request pattern
        input_schema = tool.get("inputSchema", {})
        properties = input_schema.get("properties", {})
        
        if len(properties) == 1 and "request" in properties:
            # This is a nested schema - extract parameters from docstring
            docstring = tool.get("description", "")
            flattened_schema = self._extract_parameters_from_docstring(docstring)
            
            # Override with known schemas for common tools
            if tool["name"] == "send_message":
                flattened_schema = {
                    "type": "object",
                    "properties": {
                        "from": {
                            "type": "string",
                            "description": "Sending address (phone number, alphanumeric sender ID, or short code)"
                        },
                        "to": {
                            "type": "string",
                            "description": "Receiving address(es)"
                        },
                        "text": {
                            "type": "string",
                            "description": "Message text"
                        },
                        "messaging_profile_id": {
                            "type": "string",
                            "description": "Optional. Messaging profile ID"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Optional. Message subject"
                        },
                        "media_urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional. List of media URLs"
                        },
                        "webhook_url": {
                            "type": "string",
                            "description": "Optional. Webhook URL"
                        },
                        "type": {
                            "type": "string",
                            "enum": ["SMS", "MMS"],
                            "description": "Optional. The protocol for sending the message"
                        }
                    },
                    "required": ["from", "to", "text"]
                }
            elif tool["name"] == "get_message":
                flattened_schema = {
                    "type": "object",
                    "properties": {
                        "message_id": {
                            "type": "string",
                            "description": "The ID of the message to retrieve"
                        }
                    },
                    "required": ["message_id"]
                }
            elif tool["name"] == "list_phone_numbers":
                flattened_schema = {
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
                    },
                    "required": []
                }
            elif tool["name"] == "get_assistant":
                flattened_schema = {
                    "type": "object",
                    "properties": {
                        "assistant_id": {
                            "type": "string",
                            "description": "Assistant ID"
                        }
                    },
                    "required": ["assistant_id"]
                }
            elif tool["name"] == "start_assistant_call":
                flattened_schema = {
                    "type": "object",
                    "properties": {
                        "assistant_id": {
                            "type": "string",
                            "description": "ID of the assistant to use for the call"
                        },
                        "to": {
                            "type": "string",
                            "description": "Destination phone number to call"
                        },
                        "from": {
                            "type": "string",
                            "description": "Source phone number to call from (must be a number on your Telnyx account)"
                        }
                    },
                    "required": ["assistant_id", "to", "from"]
                }
            
            transformed["inputSchema"] = flattened_schema
        
        return transformed
    
    async def handle_initialize(self, request_id: Any, params: Dict[str, Any], session_id: str = None, base_url: str = None) -> Dict[str, Any]:
        """Handle MCP initialize request."""
        # Get client's requested protocol version
        client_version = params.get("protocolVersion", PROTOCOL_VERSION)
        
        # Version negotiation - we support 2025-03-26
        response_version = PROTOCOL_VERSION if client_version == PROTOCOL_VERSION else client_version
        
        # Mark session as initialized
        if session_id:
            self._initialized_sessions.add(session_id)
        
        # Use provided base_url or fallback to environment variable
        if not base_url:
            base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": response_version,
                "capabilities": {
                    "tools": {
                        "listChanged": True
                    },
                    "resources": {
                        "subscribe": True,
                        "listChanged": True
                    },
                    "logging": {},
                    "auth": {
                        "oauth2": True,
                        "authorizationServers": [
                            base_url
                        ]
                    }
                },
                "serverInfo": {
                    "name": "Telnyx MCP Server",
                    "version": __version__
                }
            }
        }
    
    async def handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialized notification from client."""
        # Client has confirmed initialization
        logger.info("Client confirmed initialization")
    
    async def handle_tools_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle tools/list request."""
        await self.initialize_tools()
        
        # Transform tool schemas to flatten nested request objects
        transformed_tools = []
        for tool in self.tools.values():
            transformed_tool = self._transform_tool_schema(tool)
            transformed_tools.append(transformed_tool)
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": transformed_tools
            }
        }
    
    async def handle_tools_call(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        await self.initialize_tools()
        
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32602,
                    "message": f"Tool '{tool_name}' not found"
                }
            }
        
        try:
            # Transform arguments if needed
            tool_schema = self.tools[tool_name].get("inputSchema", {})
            properties = tool_schema.get("properties", {})
            
            # If the tool expects a nested request object, wrap the arguments
            if len(properties) == 1 and "request" in properties:
                # This tool expects arguments wrapped in a request object
                transformed_args = {"request": arguments}
            else:
                # Tool has been flattened or uses direct parameters
                transformed_args = arguments
            
            # Call the tool through the existing MCP instance
            result = await mcp.call_tool(tool_name, transformed_args)
            
            # Format the result according to MCP protocol
            if hasattr(result, 'text'):
                content = [{"type": "text", "text": result.text}]
            elif hasattr(result, 'content'):
                content = result.content
            else:
                content = [{"type": "text", "text": str(result)}]
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": content
                }
            }
            
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": str(e)
                }
            }
    
    async def handle_resources_list(self, request_id: Any) -> Dict[str, Any]:
        """Handle resources/list request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "resources": list(self.resources.values())
            }
        }
    
    async def handle_resources_read(self, request_id: Any, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32602,
                "message": f"Resource '{uri}' not found"
            }
        }
    
    async def process_message(self, message: Union[Dict, List], session_id: str = None, base_url: str = None) -> Union[Dict, List]:
        """Process a JSON-RPC message or batch."""
        if isinstance(message, list):
            # Batch request
            responses = []
            for msg in message:
                if msg.get("jsonrpc") == "2.0":
                    response = await self._process_single_message(msg, session_id, base_url)
                    if response:  # Only include responses for requests, not notifications
                        responses.append(response)
            return responses if responses else None
        else:
            # Single request
            return await self._process_single_message(message, session_id, base_url)
    
    async def _process_single_message(self, message: Dict[str, Any], session_id: str = None, base_url: str = None) -> Optional[Dict[str, Any]]:
        """Process a single JSON-RPC message."""
        if message.get("jsonrpc") != "2.0":
            return {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {
                    "code": -32600,
                    "message": "Invalid Request - must be JSON-RPC 2.0"
                }
            }
        
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        # Notifications don't have id and don't get responses
        is_notification = msg_id is None
        
        try:
            # Route to appropriate handler
            if method == "initialize":
                response = await self.handle_initialize(msg_id, params, session_id, base_url)
            elif method == "notifications/initialized":
                await self.handle_initialized(params)
                return None  # No response for notifications
            elif method == "tools/list":
                response = await self.handle_tools_list(msg_id)
            elif method == "tools/call":
                response = await self.handle_tools_call(msg_id, params)
            elif method == "resources/list":
                response = await self.handle_resources_list(msg_id)
            elif method == "resources/read":
                response = await self.handle_resources_read(msg_id, params)
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                }
            
            return response if not is_notification else None
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            if not is_notification:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {
                        "code": -32603,
                        "message": "Internal error",
                        "data": str(e)
                    }
                }
            return None


# Initialize MCP server
telnyx_mcp_server = TelnyxMCPServer()


def get_base_url_from_request(request: Request) -> str:
    """Extract base URL from request, handling proxy headers."""
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    
    if forwarded_proto and forwarded_host:
        return f"{forwarded_proto}://{forwarded_host}"
    else:
        return str(request.base_url).rstrip('/')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Telnyx Remote MCP Server")
    await telnyx_mcp_server.initialize_tools()
    yield
    logger.info("Shutting down Telnyx Remote MCP Server")


# Create FastAPI app
app = FastAPI(
    title="Telnyx Remote MCP Server",
    description="Model Context Protocol server for Telnyx API integration",
    version=__version__,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming HTTP requests."""
    start_time = datetime.now()
    
    # Log request details
    logger.info(f"HTTP Request: {request.method} {request.url.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Query params: {dict(request.query_params)}")
    
    # Process request
    response = await call_next(request)
    
    # Log response details
    process_time = (datetime.now() - start_time).total_seconds()
    logger.info(f"HTTP Response: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time}s")
    
    return response


@app.get("/")
async def root():
    """Root endpoint with server information."""
    base_url = os.getenv("BASE_URL", "https://app-web-3ky2b33hy2dpm.azurewebsites.net")
    return {
        "name": "Telnyx Remote MCP Server",
        "version": __version__,
        "protocol_version": PROTOCOL_VERSION,
        "status": "healthy",
        "endpoints": {
            "mcp": "/mcp",
            "oauth_authorization_server": "/.well-known/oauth-authorization-server",
            "health": "/health"
        },
        "tools_available": len(telnyx_mcp_server.tools)
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "telnyx-mcp-server",
        "version": __version__,
        "protocol_version": PROTOCOL_VERSION
    }


@app.get("/.well-known/oauth-protected-resource")
async def oauth_protected_resource_metadata(request: Request):
    """OAuth 2.0 Protected Resource Metadata (RFC9728)."""
    # Get base URL from request, handling proxy headers
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    
    if forwarded_proto and forwarded_host:
        # Running behind a proxy (like Azure App Service)
        base_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        # Direct access
        base_url = str(request.base_url).rstrip('/')
    
    return {
        "resource": base_url,
        "authorization_servers": [base_url],
        "scopes_supported": ["openid", "profile", "email"],
        "bearer_methods_supported": ["header"],
        "resource_signing_alg_values_supported": ["RS256"],
        "resource_documentation": f"{base_url}/docs",
        "resource_policy_uri": f"{base_url}/privacy",
        "resource_tos_uri": f"{base_url}/terms"
    }


@app.get("/.well-known/oauth-authorization-server")
async def oauth_metadata(request: Request):
    """OAuth 2.0 Authorization Server Metadata (RFC8414)."""
    # Get base URL from request, handling proxy headers
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    
    if forwarded_proto and forwarded_host:
        # Running behind a proxy (like Azure App Service)
        base_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        # Direct access
        base_url = str(request.base_url).rstrip('/')
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "userinfo_endpoint": f"{base_url}/userinfo",
        "registration_endpoint": f"{base_url}/register",
        # Note: We use HS256 for JWT signing, not RS256 from Azure
        # Remove jwks_uri to avoid confusion since we don't publish our symmetric key
        # "jwks_uri": f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys" if AZURE_TENANT_ID else None,
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email", "User.Read"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
        "claims_supported": ["sub", "email", "name", "exp", "iat"],
        "service_documentation": f"{base_url}/docs"
    }


@app.get("/.well-known/mcp-oauth-metadata")
async def mcp_oauth_metadata(request: Request):
    """MCP OAuth 2.0 Metadata endpoint for Claude."""
    # Get base URL from request, handling proxy headers
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    
    if forwarded_proto and forwarded_host:
        # Running behind a proxy (like Azure App Service)
        base_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        # Direct access
        base_url = str(request.base_url).rstrip('/')
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "scopes_supported": ["openid", "profile", "email"],
        "code_challenge_methods_supported": ["S256"]
    }


@app.get("/.well-known/openid-configuration")
async def openid_configuration(request: Request):
    """OpenID Connect Discovery endpoint."""
    # Get base URL from request, handling proxy headers
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    
    if forwarded_proto and forwarded_host:
        # Running behind a proxy (like Azure App Service)
        base_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        # Direct access
        base_url = str(request.base_url).rstrip('/')
    
    return {
        "issuer": base_url,
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "userinfo_endpoint": f"{base_url}/userinfo",
        # Note: We use HS256 for JWT signing, not RS256 from Azure
        # Remove jwks_uri to avoid confusion since we don't publish our symmetric key
        # "jwks_uri": f"https://login.microsoftonline.com/{AZURE_TENANT_ID}/discovery/v2.0/keys" if AZURE_TENANT_ID else None,
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "profile", "email"],
        "token_endpoint_auth_methods_supported": ["none"],
        "code_challenge_methods_supported": ["S256"],
        "claims_supported": ["sub", "email", "name", "exp", "iat"]
    }


@app.get("/.well-known/mcp-metadata")
async def mcp_metadata(request: Request):
    """MCP Metadata endpoint for Claude Desktop discovery."""
    # Get base URL from request, handling proxy headers
    forwarded_proto = request.headers.get("x-forwarded-proto", "").lower()
    forwarded_host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    
    if forwarded_proto and forwarded_host:
        # Running behind a proxy (like Azure App Service)
        base_url = f"{forwarded_proto}://{forwarded_host}"
    else:
        # Direct access
        base_url = str(request.base_url).rstrip('/')
    
    return {
        "mcpVersion": "2025-03-26",
        "serverInfo": {
            "name": "Telnyx MCP Server",
            "version": __version__
        },
        "auth": {
            "type": "oauth2",
            "oauth2": {
                "authorizationEndpoint": f"{base_url}/authorize",
                "tokenEndpoint": f"{base_url}/token",
                "scopes": ["openid", "profile", "email"],
                "pkce": True
            }
        },
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": False,
            "logging": True
        }
    }


# OAuth 2.0 endpoints (simplified for MCP)
@app.get("/authorize")
async def authorize(
    client_id: str,
    redirect_uri: str,
    response_type: str = "code",
    scope: str = "openid profile email",
    state: Optional[str] = None,
    code_challenge: Optional[str] = None,
    code_challenge_method: Optional[str] = "S256"
):
    """OAuth 2.0 Authorization endpoint - initiates the two-layer OAuth flow."""
    # For public clients like Claude Desktop, accept any client_id
    # In production, you'd validate against registered clients
    logger.info(f"Authorization request from client_id: {client_id}")
    
    # Validate response_type
    if response_type != "code":
        return Response(
            content="Only response_type=code is supported",
            status_code=400
        )
    
    # PKCE is MANDATORY for public clients (RFC 7636)
    if not code_challenge:
        logger.error(f"Missing code_challenge from client_id: {client_id}")
        return Response(
            content="code_challenge is required for public clients",
            status_code=400
        )
    
    # Validate code_challenge_method - only S256 allowed for security
    if code_challenge_method != "S256":
        logger.error(f"Invalid code_challenge_method: {code_challenge_method}")
        return Response(
            content="Only S256 code_challenge_method is supported",
            status_code=400
        )
    
    # Generate a unique state for Azure AD if not provided
    azure_state = state or secrets.token_urlsafe(32)
    
    # Create a session to track this OAuth flow
    session_id = auth_store.create_session(
        state=azure_state,
        redirect_uri=redirect_uri,
        pkce_challenge=code_challenge,
        pkce_method=code_challenge_method
    )
    
    logger.info(f"Created OAuth session {session_id[:8]}... for redirect_uri: {redirect_uri}")
    
    # Get Azure AD authorization URL with our generated state
    auth_url = AuthService.get_authorization_url(azure_state)
    
    # Redirect to Azure AD
    return RedirectResponse(url=auth_url, status_code=302)


@app.post("/token")
async def token(request: Request):
    """OAuth 2.0 Token endpoint - exchanges MCP auth code for JWT token."""
    form_data = await request.form()
    code = form_data.get("code")
    grant_type = form_data.get("grant_type")
    client_id = form_data.get("client_id")
    code_verifier = form_data.get("code_verifier")  # PKCE
    
    # Validate grant type
    if grant_type != "authorization_code":
        return Response(
            content=json.dumps({
                "error": "unsupported_grant_type",
                "error_description": "Only authorization_code grant type is supported"
            }),
            status_code=400,
            media_type="application/json"
        )
    
    if not code:
        return Response(
            content=json.dumps({
                "error": "invalid_request",
                "error_description": "Missing authorization code"
            }),
            status_code=400,
            media_type="application/json"
        )
    
    try:
        # Retrieve the MCP auth code from our store
        auth_code_data = auth_store.get_auth_code(code)
        
        if not auth_code_data:
            logger.warning(f"Invalid or expired MCP auth code: {code[:8]}...")
            return Response(
                content=json.dumps({
                    "error": "invalid_grant",
                    "error_description": "Authorization code is invalid or expired"
                }),
                status_code=400,
                media_type="application/json"
            )
        
        # Mark the code as used to prevent replay attacks
        auth_store.mark_code_used(code)
        
        # PKCE validation is MANDATORY for public clients (RFC 7636)
        if auth_code_data.pkce_challenge:
            if not code_verifier:
                logger.error("PKCE code_verifier missing for code with challenge")
                return Response(
                    content=json.dumps({
                        "error": "invalid_request",
                        "error_description": "code_verifier is required for PKCE"
                    }),
                    status_code=400,
                    media_type="application/json"
                )
            
            # Validate PKCE - compute challenge from verifier and compare
            if auth_code_data.pkce_method == "S256":
                # SHA256 hash the verifier and base64url encode
                verifier_bytes = code_verifier.encode('ascii')
                challenge_bytes = hashlib.sha256(verifier_bytes).digest()
                computed_challenge = base64.urlsafe_b64encode(challenge_bytes).decode('ascii').rstrip('=')
            else:
                # Plain method not allowed for security
                logger.error(f"Unsupported PKCE method: {auth_code_data.pkce_method}")
                return Response(
                    content=json.dumps({
                        "error": "invalid_request",
                        "error_description": "Only S256 code_challenge_method is supported"
                    }),
                    status_code=400,
                    media_type="application/json"
                )
            
            # Compare with stored challenge
            if computed_challenge != auth_code_data.pkce_challenge:
                logger.error("PKCE verification failed - challenge mismatch")
                return Response(
                    content=json.dumps({
                        "error": "invalid_grant",
                        "error_description": "PKCE verification failed"
                    }),
                    status_code=400,
                    media_type="application/json"
                )
        
        # Create JWT token using the stored user info and Azure token
        user_info = auth_code_data.user_info
        jwt_token = AuthService.create_jwt_token(user_info)
        
        logger.info(f"Issued JWT token for user: {user_info.get('mail', user_info.get('userPrincipalName'))}")
        
        return {
            "access_token": jwt_token,
            "token_type": "Bearer",
            "expires_in": 86400,  # 24 hours
            "scope": "openid profile email"
        }
        
    except Exception as e:
        logger.error(f"Token exchange error: {e}", exc_info=True)
        return Response(
            content=json.dumps({
                "error": "server_error",
                "error_description": "An internal error occurred"
            }),
            status_code=500,
            media_type="application/json"
        )


@app.get("/userinfo")
async def userinfo(user: Dict[str, Any] = Depends(get_current_user)):
    """OpenID Connect UserInfo endpoint."""
    return {
        "sub": user.get("sub"),
        "email": user.get("email"),
        "name": user.get("name"),
        "email_verified": True,
        "updated_at": int(time.time())
    }


@app.get("/auth/callback")
async def oauth_callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None
):
    """OAuth 2.0 callback endpoint - handles the two-layer OAuth flow.
    
    This endpoint:
    1. Receives the authorization code from Azure AD
    2. Exchanges it for Azure AD tokens
    3. Generates an MCP-specific authorization code
    4. Redirects back to Claude.ai with the MCP code
    """
    if error:
        # Azure AD returned an error
        logger.error(f"OAuth callback error: {error} - {error_description}")
        html_content = f"""
        <html>
        <head><title>Authorization Failed</title></head>
        <body>
            <h1>Authorization Failed</h1>
            <p>Error: {error}</p>
            <p>Description: {error_description or "Authorization failed"}</p>
            <p>You can close this window and try again.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    if not code:
        logger.error("OAuth callback missing authorization code")
        html_content = """
        <html>
        <head><title>Authorization Failed</title></head>
        <body>
            <h1>Authorization Failed</h1>
            <p>Missing authorization code</p>
            <p>You can close this window and try again.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html")
    
    try:
        # Find the session by state parameter
        session = None
        if state:
            session = auth_store.get_session_by_state(state)
            if not session:
                logger.warning(f"Session not found for state: {state}")
        
        # Exchange the Azure AD code for tokens
        logger.info("Exchanging Azure AD code for tokens")
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                AZURE_TOKEN_URL,
                data={
                    "client_id": AZURE_CLIENT_ID,
                    "client_secret": AZURE_CLIENT_SECRET,
                    "code": code,
                    "redirect_uri": AZURE_REDIRECT_URI,
                    "grant_type": "authorization_code"
                }
            )
            
            if token_response.status_code != 200:
                logger.error(f"Azure token exchange failed: {token_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to exchange authorization code"
                )
            
            azure_token_data = token_response.json()
            azure_access_token = azure_token_data.get("access_token")
            
            if not azure_access_token:
                logger.error("No access token in Azure response")
                raise HTTPException(
                    status_code=500,
                    detail="No access token received from Azure"
                )
        
        # Get user info from Azure
        logger.info("Fetching user info from Azure AD")
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://graph.microsoft.com/v1.0/me",
                headers={"Authorization": f"Bearer {azure_access_token}"}
            )
            
            if user_response.status_code != 200:
                logger.error(f"Failed to get user info: {user_response.text}")
                raise HTTPException(
                    status_code=500,
                    detail="Failed to get user information"
                )
            
            user_info = user_response.json()
            logger.info(f"Retrieved user info for: {user_info.get('mail', user_info.get('userPrincipalName'))}")
        
        # Generate MCP-specific authorization code
        mcp_auth_code = auth_store.create_auth_code(
            azure_token=azure_access_token,
            azure_token_data=azure_token_data,
            user_info=user_info,
            state=state,
            redirect_uri=session.redirect_uri if session else None,
            pkce_challenge=session.pkce_challenge if session else None,
            pkce_method=session.pkce_method if session else None
        )
        
        logger.info(f"Generated MCP auth code: {mcp_auth_code[:8]}...")
        
        # Check if this is a browser flow or Claude.ai flow
        # For now, we'll detect Claude by looking for the session
        if session and session.redirect_uri:
            # This is part of a proper OAuth flow with a redirect URI
            # Build the redirect URL back to Claude.ai
            redirect_params = {
                "code": mcp_auth_code,
                "state": state
            }
            
            # Parse the redirect URI and add parameters
            if "?" in session.redirect_uri:
                redirect_url = f"{session.redirect_uri}&{urllib.parse.urlencode(redirect_params)}"
            else:
                redirect_url = f"{session.redirect_uri}?{urllib.parse.urlencode(redirect_params)}"
            
            logger.info(f"Redirecting to Claude.ai: {redirect_url}")
            return RedirectResponse(url=redirect_url, status_code=302)
        
        # For browser-based flows or testing, show success page with the MCP code
        html_content = f"""
        <html>
        <head>
            <title>Authorization Complete</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background-color: #f5f5f5;
                    padding: 1rem;
                }}
                .container {{
                    text-align: center;
                    padding: 2rem;
                    background-color: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    max-width: 500px;
                    width: 100%;
                }}
                .success {{
                    color: #22c55e;
                    font-size: 3rem;
                    margin-bottom: 1rem;
                }}
                h1 {{
                    margin: 0 0 1rem 0;
                    color: #1a1a1a;
                    font-size: 1.5rem;
                    font-weight: 600;
                }}
                p {{
                    color: #666;
                    margin: 0.5rem 0;
                    line-height: 1.5;
                }}
                .code-box {{
                    background-color: #f3f4f6;
                    border: 1px solid #e5e7eb;
                    border-radius: 4px;
                    padding: 1rem;
                    margin: 1.5rem 0;
                    font-family: monospace;
                    font-size: 0.875rem;
                    word-break: break-all;
                    user-select: all;
                }}
                .instructions {{
                    text-align: left;
                    margin: 1.5rem 0;
                    padding: 1rem;
                    background-color: #f9fafb;
                    border-radius: 4px;
                }}
                .instructions li {{
                    margin: 0.5rem 0;
                    color: #374151;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success">✓</div>
                <h1>Authorization Complete</h1>
                <p>You have successfully authenticated with Azure AD.</p>
                <p>Your MCP authorization code is:</p>
                <div class="code-box">{mcp_auth_code}</div>
                <div class="instructions">
                    <p><strong>Next steps:</strong></p>
                    <ol>
                        <li>Copy the authorization code above</li>
                        <li>Return to Claude.ai</li>
                        <li>Complete the connection process</li>
                    </ol>
                </div>
                <p style="margin-top: 2rem; font-size: 0.875rem; color: #999;">
                    This code expires in 10 minutes and can only be used once.
                </p>
            </div>
        </body>
        </html>
        """
        
        return Response(content=html_content, media_type="text/html")
        
    except Exception as e:
        logger.error(f"OAuth callback error: {str(e)}", exc_info=True)
        html_content = f"""
        <html>
        <head><title>Authorization Failed</title></head>
        <body>
            <h1>Authorization Failed</h1>
            <p>An error occurred during authentication.</p>
            <p>Error: {str(e)}</p>
            <p>Please close this window and try again.</p>
        </body>
        </html>
        """
        return Response(content=html_content, media_type="text/html", status_code=500)


@app.post("/register")
async def register(request: Request):
    """OAuth 2.0 Dynamic Client Registration (RFC7591).
    
    Since we're using Azure AD, we return our pre-registered app details.
    """
    try:
        client_data = await request.json()
    except:
        client_data = {}
    
    # Return our Azure AD app registration
    # For public clients, we return an empty string for client_secret
    return {
        "client_id": AZURE_CLIENT_ID,
        "client_secret": "",  # Empty string for public client
        "registration_access_token": "",
        "registration_client_uri": "",
        "client_id_issued_at": int(datetime.utcnow().timestamp()),
        "client_secret_expires_at": 0,
        "redirect_uris": [AZURE_REDIRECT_URI],
        "grant_types": ["authorization_code"],
        "response_types": ["code"],
        "token_endpoint_auth_method": "none",  # Public client
        "application_type": "web",
        "token_endpoint_auth_signing_alg": "RS256"
    }


# MCP Protocol Endpoints
@app.post("/mcp")
async def mcp_endpoint(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(optional_auth)
):
    """MCP endpoint implementing Streamable HTTP transport.
    
    Authentication is required for all methods except initialize.
    """
    # Get base URL first
    base_url = get_base_url_from_request(request)
    
    # Parse the request body first to check method
    try:
        body = await request.body()
        message = json.loads(body)
        
        # Determine if this request requires authentication
        requires_auth = True
        if isinstance(message, dict):
            method = message.get("method", "")
            # Only initialize and its notification are allowed without auth
            if method in ["initialize", "notifications/initialized"]:
                requires_auth = False
        
        # If auth is required but user is not authenticated, return 401
        if requires_auth and not current_user:
            headers = {
                "WWW-Authenticate": 'Bearer realm="MCP Server"',
                "Link": f'<{base_url}/.well-known/oauth-authorization-server>; rel="oauth-authorization-server"'
            }
            
            # Determine response ID for error
            response_id = None
            if isinstance(message, dict):
                response_id = message.get("id")
            
            return Response(
                content=json.dumps({
                    "jsonrpc": "2.0",
                    "id": response_id,
                    "error": {
                        "code": -32603,
                        "message": "Authentication required",
                        "data": {
                            "oauth_url": f"{base_url}/.well-known/oauth-authorization-server"
                        }
                    }
                }),
                status_code=401,
                headers=headers,
                media_type="application/json"
            )
        
        # Reset body for further processing
        request._body = body
        
    except json.JSONDecodeError:
        # Let it be handled by the normal error flow below
        pass
    # Check Accept header
    accept_header = request.headers.get("accept", "application/json")
    prefers_sse = "text/event-stream" in accept_header
    
    # Get session ID if provided
    session_id = request.headers.get("mcp-session-id")
    
    try:
        body = await request.body()
        message = json.loads(body)
    except json.JSONDecodeError as e:
        error_response = {
            "jsonrpc": "2.0",
            "id": None,
            "error": {
                "code": -32700,
                "message": "Parse error",
                "data": str(e)
            }
        }
        
        if prefers_sse:
            async def error_generator():
                yield {"data": json.dumps(error_response)}
            return EventSourceResponse(error_generator())
        
        return error_response
    
    # Log request
    if isinstance(message, list):
        methods = [msg.get("method") for msg in message if isinstance(msg, dict)]
        logger.info(f"MCP batch request: {methods} (user: {current_user.get('email') if current_user else 'anonymous'})")
    else:
        logger.info(f"MCP request: {message.get('method')} (user: {current_user.get('email') if current_user else 'anonymous'})")
    
    # Get base URL for OAuth discovery
    base_url = get_base_url_from_request(request)
    
    # Process the message(s)
    response = await telnyx_mcp_server.process_message(message, session_id, base_url)
    
    # Handle response format based on message type and Accept header
    if response is None:
        # Notification - return 202 Accepted with no body
        return Response(status_code=202)
    
    # Check if this contains only responses (no requests)
    is_batch = isinstance(response, list)
    contains_requests = False
    
    if is_batch:
        for resp in response:
            if "result" in resp or "error" in resp:
                # This is a response to a request
                contains_requests = True
                break
    else:
        if "result" in response or "error" in response:
            contains_requests = True
    
    # Return appropriate format
    if prefers_sse and contains_requests:
        async def event_generator():
            if is_batch:
                # Send each response as a separate SSE event
                for resp in response:
                    yield {"data": json.dumps(resp)}
            else:
                yield {"data": json.dumps(response)}
        
        headers = {}
        if session_id:
            headers["mcp-session-id"] = session_id
            
        return EventSourceResponse(event_generator(), headers=headers)
    else:
        # Return JSON response
        headers = {}
        if session_id:
            headers["mcp-session-id"] = session_id
            
        return Response(
            content=json.dumps(response),
            media_type="application/json",
            headers=headers
        )


@app.get("/mcp")
async def mcp_sse_stream(
    request: Request,
    current_user: Optional[Dict[str, Any]] = Depends(optional_auth)
):
    """GET endpoint for server-initiated SSE stream."""
    # SSE streams also require authentication
    if not current_user:
        base_url = get_base_url_from_request(request)
        headers = {
            "WWW-Authenticate": 'Bearer realm="MCP Server"',
            "Link": f'<{base_url}/.well-known/oauth-authorization-server>; rel="oauth-authorization-server"'
        }
        return Response(
            content="Authentication required for SSE stream",
            status_code=401,
            headers=headers
        )
    
    # Get session ID if provided
    session_id = request.headers.get("mcp-session-id")
    
    # Check Accept header
    accept_header = request.headers.get("accept", "")
    if "text/event-stream" not in accept_header:
        return Response(
            status_code=405,
            content="Method not allowed - this endpoint requires Accept: text/event-stream"
        )
    
    async def event_generator():
        # For now, just keep the connection open
        # In a real implementation, this would send server-initiated messages
        try:
            while True:
                await asyncio.sleep(30)  # Send keepalive every 30 seconds
                yield {"event": "ping", "data": ""}
        except asyncio.CancelledError:
            logger.info("SSE stream closed")
    
    headers = {}
    if session_id:
        headers["mcp-session-id"] = session_id
        
    return EventSourceResponse(event_generator(), headers=headers)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")