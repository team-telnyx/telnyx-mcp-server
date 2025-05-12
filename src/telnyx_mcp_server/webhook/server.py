"""Lightweight Unix Socket server for handling webhooks without port conflicts."""

from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler
import json
import os
from socketserver import UnixStreamServer
import tempfile
import threading
from typing import Any, Dict, List, Optional

from ..config import settings
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Store webhook history (most recent first)
webhook_history = deque(maxlen=100)  # Store last 100 webhooks


class UnixSocketHandler(BaseHTTPRequestHandler):
    """HTTP request handler for Unix domain sockets."""

    # Ensure HTTP/1.1 is used consistently
    protocol_version = "HTTP/1.1"

    # Override address_string to fix the IndexError with Unix sockets
    def address_string(self):
        """Return a string representation of the client address."""
        # For Unix sockets, client_address is often a string or None
        # Just return a placeholder instead of trying to index it
        return "unix-client"

    # Override log_message to ensure it doesn't fail with Unix sockets
    def log_message(self, format, *args):
        """Log an arbitrary message to the server log."""
        # Use a more robust implementation that won't fail with Unix sockets
        try:
            message = format % args
            logger.info(
                f"[UnixSocketHandler] {self.command} {self.path} - {message}"
            )
        except Exception as e:
            # Failsafe logging that doesn't rely on string formatting
            logger.info(
                f"[UnixSocketHandler] Request processed: {self.command} {self.path}"
            )

    def do_POST(self):
        """Handle POST requests from the ngrok tunnel."""
        try:
            # Get content length
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length > settings.webhook_max_body_size:
                self.send_error(413, "Request entity too large")
                return

            # Read the request body
            body = self.rfile.read(content_length)

            # Process the webhook request
            self._process_webhook(body)

            # Prepare a valid JSON response
            response = json.dumps(
                {
                    "status": "success",
                    "message": "Webhook received",
                    "timestamp": datetime.now().isoformat(),
                }
            )
            response_bytes = response.encode("utf-8")

            try:
                # Send a properly formatted HTTP response with more robust error handling
                self.send_response(200)
                # Set headers with proper HTTP/1.1 compliance
                self.send_header(
                    "Content-Type", "application/json; charset=utf-8"
                )
                self.send_header("Content-Length", str(len(response_bytes)))
                self.send_header(
                    "Connection", "close"
                )  # Important for HTTP/1.1
                # Add more headers to help with debugging
                self.send_header("X-Webhook-Handler", "Telnyx-MCP-Unix-Socket")
                self.send_header("Cache-Control", "no-store, no-cache")
                self.end_headers()

                # Write the response in a try-except block
                try:
                    self.wfile.write(response_bytes)
                    self.wfile.flush()  # Ensure the response is sent completely
                except (BrokenPipeError, ConnectionResetError) as pipe_error:
                    # Client disconnected - log but don't re-raise
                    logger.warning(
                        f"Client disconnected during response: {pipe_error}"
                    )
                except Exception as write_error:
                    logger.error(f"Error writing response: {write_error}")
                    # Don't re-raise - we've already processed the webhook
            except Exception as resp_error:
                logger.error(f"Error sending HTTP response: {resp_error}")
                # Don't re-raise - we've already processed the webhook
        except Exception as e:
            logger.error(f"Error handling webhook: {str(e)}")
            # Send a properly formatted error response with enhanced robustness
            try:
                error_response = json.dumps(
                    {
                        "status": "error",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat(),
                    }
                )
                error_bytes = error_response.encode("utf-8")

                self.send_response(500)
                self.send_header(
                    "Content-Type", "application/json; charset=utf-8"
                )
                self.send_header("Content-Length", str(len(error_bytes)))
                self.send_header("Connection", "close")
                self.send_header("X-Webhook-Handler", "Telnyx-MCP-Unix-Socket")
                self.end_headers()

                # Write error response with exception handling
                try:
                    self.wfile.write(error_bytes)
                    self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError):
                    # Client disconnected - just log it
                    logger.warning("Client disconnected during error response")
                except Exception as write_err:
                    logger.error(f"Error writing error response: {write_err}")
            except Exception as resp_err:
                logger.error(f"Failed to send error response: {resp_err}")

    def do_GET(self):
        """Handle GET requests for health checks."""
        try:
            # Prepare a valid JSON response
            response = json.dumps(
                {
                    "status": "ok",
                    "time": datetime.now().isoformat(),
                    "path": self.path,
                    "webhook_server": "Telnyx-MCP-Unix-Socket",
                }
            )
            response_bytes = response.encode("utf-8")

            # Send a properly formatted HTTP response with robust error handling
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.send_header("Connection", "close")
            self.send_header("X-Webhook-Handler", "Telnyx-MCP-Unix-Socket")
            self.send_header("Cache-Control", "no-store, no-cache")
            self.end_headers()

            # Write the response with exception handling
            try:
                self.wfile.write(response_bytes)
                self.wfile.flush()  # Ensure the response is sent completely
            except (BrokenPipeError, ConnectionResetError) as pipe_error:
                # Client disconnected - log but don't re-raise
                logger.warning(
                    f"Client disconnected during health check response: {pipe_error}"
                )
            except Exception as write_error:
                logger.error(
                    f"Error writing health check response: {write_error}"
                )
        except Exception as e:
            logger.error(f"Error handling health check request: {str(e)}")
            # Try to send an error response
            try:
                error_response = json.dumps(
                    {"status": "error", "message": str(e)}
                )
                error_bytes = error_response.encode("utf-8")
                self.send_response(500)
                self.send_header(
                    "Content-Type", "application/json; charset=utf-8"
                )
                self.send_header("Content-Length", str(len(error_bytes)))
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(error_bytes)
                self.wfile.flush()
            except Exception:
                # If that also fails, just log and continue
                logger.error("Failed to send health check error response")

    def _process_webhook(self, body: bytes) -> None:
        """Process the webhook request."""
        try:
            # Parse the request body as JSON
            if body:
                payload = json.loads(body)

                # Extract event type from payload - check both root level and nested data
                # This handles both {event_type: "x"} and {data: {event_type: "x"}} formats
                if "event_type" in payload:
                    event_type = payload.get("event_type", "unknown")
                else:
                    # Fall back to checking in data object or default to unknown
                    event_type = payload.get("data", {}).get(
                        "event_type", "unknown"
                    )

                # Log the webhook
                logger.info(f"Received webhook event: {event_type}")
                logger.debug(
                    f"Webhook payload: {json.dumps(payload, indent=2)}"
                )

                # Store in history
                webhook_history.appendleft(
                    {
                        "timestamp": datetime.now().isoformat(),
                        "event_type": event_type,
                        "payload": payload,
                        "headers": dict(self.headers),
                    }
                )

                logger.debug(
                    f"Added webhook to history (total: {len(webhook_history)})"
                )
            else:
                logger.warning("Received empty webhook body")
        except json.JSONDecodeError:
            logger.error("Failed to parse webhook payload as JSON")
        except Exception as e:
            logger.error(f"Error processing webhook: {str(e)}")
            raise  # Re-raise to allow proper error response


class UnixSocketHTTPServer(UnixStreamServer):
    """HTTP server using Unix domain sockets."""

    def __init__(self, server_address, RequestHandlerClass):
        """Initialize the server with a Unix socket."""
        super().__init__(server_address, RequestHandlerClass)
        self._thread = None
        self._running = False

    def start(self):
        """Start the server in a background thread."""
        self._running = True
        self._thread = threading.Thread(target=self.serve_forever)
        self._thread.daemon = True
        self._thread.start()
        logger.info(f"Unix socket server started on {self.server_address}")

    def stop(self):
        """Stop the server."""
        if self._running:
            self._running = False
            self.shutdown()
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=5.0)
            self.server_close()

            # Clean up the socket file
            try:
                if os.path.exists(self.server_address):
                    os.unlink(self.server_address)
                    logger.info(f"Removed socket file: {self.server_address}")
            except OSError as e:
                logger.warning(f"Error removing socket file: {e}")


# Global server instance
socket_server = None
socket_path = None


def generate_socket_path() -> str:
    """Generate a unique socket path."""
    temp_dir = tempfile.mkdtemp(prefix="telnyx_mcp_")
    socket_name = f"webhook-{os.getpid()}.sock"
    path = os.path.join(temp_dir, socket_name)
    return path


def get_webhook_history(limit: int = None) -> List[Dict[str, Any]]:
    """
    Get the webhook history.

    Args:
        limit: Maximum number of webhooks to return (None for all)

    Returns:
        List of webhook events, most recent first
    """
    if limit is None or limit > len(webhook_history):
        return list(webhook_history)
    return list(webhook_history)[:limit]


def start_webhook_server() -> Optional[str]:
    """
    Start the webhook server using a Unix domain socket.

    Returns:
        Optional[str]: The socket path if successful, None otherwise
    """
    global socket_server, socket_path

    if not settings.webhook_enabled:
        logger.info("Webhook server is disabled")
        return None

    try:
        # Generate a unique socket path
        socket_path = generate_socket_path()
        logger.info(f"Using Unix domain socket at: {socket_path}")

        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(socket_path), exist_ok=True)

        # Clean up any existing socket file
        if os.path.exists(socket_path):
            try:
                os.unlink(socket_path)
            except OSError as e:
                logger.warning(f"Could not remove existing socket file: {e}")

        # Create and start the server
        socket_server = UnixSocketHTTPServer(socket_path, UnixSocketHandler)
        socket_server.start()

        # Register cleanup on exit - but avoid signal handlers which won't work in all threads
        import atexit

        atexit.register(stop_webhook_server)

        return socket_path
    except Exception as e:
        logger.error(f"Failed to start webhook server: {e}")
        return None


def stop_webhook_server() -> None:
    """Stop the webhook server."""
    global socket_server, socket_path

    if socket_server:
        logger.info("Stopping webhook server...")
        socket_server.stop()
        socket_server = None

    # Clean up the socket directory
    if socket_path:
        try:
            dir_path = os.path.dirname(socket_path)
            if os.path.exists(dir_path) and dir_path.startswith(
                tempfile.gettempdir()
            ):
                os.rmdir(dir_path)
                logger.info(f"Removed socket directory: {dir_path}")
        except OSError as e:
            logger.warning(f"Error removing socket directory: {e}")

        socket_path = None
