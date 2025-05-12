"""Direct ngrok tunnel handler using Unix domain sockets."""

from datetime import datetime
import sys
import threading
import time
from typing import Optional

try:
    import ngrok
except ImportError as e:
    raise ImportError(
        f"Failed to import ngrok. Please install it with 'pip install ngrok>=0.9.0'. Error: {e}"
    )

from ..config import settings
from ..utils.logger import get_logger
from .server import (
    start_webhook_server,
    stop_webhook_server,
)

logger = get_logger(__name__)


class NgrokTunnelHandler:
    """
    Ngrok tunnel handler using the official Python SDK without binary dependencies.

    This class creates an ngrok tunnel directly using the ngrok-python SDK
    connecting to a Unix domain socket, avoiding port conflicts.
    """

    def __init__(self):
        """Initialize the tunnel handler."""
        self.listener = None
        self.public_url = None
        self._reconnect_thread = None
        self._running = False
        self.socket_path = None
        self._tunnel_was_established = (
            False  # Track if a tunnel was ever successfully established
        )

        # Clean up internal SDK resources only (not processes)
        self._cleanup_sdk_resources()

    def _cleanup_sdk_resources(self):
        """Thoroughly clean up ngrok SDK resources without affecting external processes."""
        logger.info("Performing thorough ngrok SDK resources cleanup...")

        try:
            # Use the Python API to clean up resources
            import ngrok

            try:
                # Multiple disconnect attempts with different approaches
                try:
                    # First generic disconnect
                    ngrok.disconnect()
                    time.sleep(0.5)

                    # Then try to list and disconnect any tunnels specifically
                    if hasattr(ngrok, "list_tunnels"):
                        tunnels = ngrok.list_tunnels()
                        for tunnel in tunnels:
                            try:
                                if hasattr(tunnel, "url"):
                                    ngrok.disconnect(tunnel.url())
                                elif hasattr(tunnel, "public_url"):
                                    ngrok.disconnect(tunnel.public_url)
                            except Exception:
                                pass

                    logger.info("Reset all ngrok connections via SDK")
                except Exception as e:
                    logger.warning(f"Failed to reset connections: {e}")

                # Comprehensive module state cleanup
                try:
                    # Clear anything that might store state
                    attrs_to_clear = [
                        "_tunnels",
                        "_listeners",
                        "_sessions",
                        "_endpoints",
                        "_configs",
                        "_connections",
                    ]

                    for attr in attrs_to_clear:
                        if hasattr(ngrok, attr):
                            if isinstance(getattr(ngrok, attr), dict):
                                setattr(ngrok, attr, {})
                            elif isinstance(getattr(ngrok, attr), list):
                                setattr(ngrok, attr, [])

                    # Reset API client if possible
                    if hasattr(ngrok, "api") and hasattr(ngrok.api, "_client"):
                        ngrok.api._client = None

                    logger.info("Reset all ngrok internal module state")
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Failed during ngrok reset: {e}")

        except Exception as e:
            logger.warning(f"Error during ngrok SDK cleanup: {e}")

        # Immediately try to patch NGrok to ignore domain settings
        try:
            import sys

            import ngrok

            # Try to force dynamic domains by monkey patching
            if hasattr(ngrok, "Config"):
                original_init = ngrok.Config.__init__

                # Define a patched init that ignores domain
                def patched_init(self, *args, **kwargs):
                    # Force domain to None before calling original
                    if "domain" in kwargs:
                        kwargs["domain"] = None
                    return original_init(self, *args, **kwargs)

                # Apply the patch
                ngrok.Config.__init__ = patched_init
                logger.info(
                    "Successfully patched NGrok Config to force dynamic domains"
                )
            else:
                logger.info(
                    "NGrok Config not found, could not apply domain patch"
                )

            # Also try to delete any module-level domain setting
            ngrok_modules = [m for m in sys.modules if m.startswith("ngrok")]
            for module_name in ngrok_modules:
                module = sys.modules[module_name]
                if hasattr(module, "domain"):
                    setattr(module, "domain", None)
                    logger.info(f"Reset domain in module {module_name}")
        except Exception as patch_err:
            logger.warning(f"Error patching NGrok (non-fatal): {patch_err}")

    def start(self) -> Optional[str]:
        """
        Start the ngrok tunnel.

        Returns:
            Optional[str]: The public URL for webhooks or None if startup fails

        Raises:
            SystemExit: If webhook_enabled is true but the tunnel cannot be created
        """
        if not settings.webhook_enabled:
            logger.info("Webhook handler is disabled")
            return None

        if not settings.ngrok_enabled:
            # If webhooks are enabled but ngrok is disabled, this is a fatal configuration error
            logger.critical(
                "FATAL ERROR: Webhook handler is enabled but NGrok is disabled"
            )
            logger.critical(
                "Webhooks cannot function without NGrok - exiting process"
            )
            sys.exit(1)  # Exit with error status code
            return None  # This will never execute

        # Add authtoken if available
        if settings.ngrok_authtoken:
            # Set for all connections
            try:
                ngrok.set_auth_token(settings.ngrok_authtoken)
                logger.info("Using ngrok authentication token")
            except Exception as e:
                logger.error(f"Failed to set ngrok authentication token: {e}")
                return None
        else:
            logger.warning(
                "No ngrok authentication token provided - tunnel may fail"
            )

        # First start the Unix socket server
        self.socket_path = start_webhook_server()
        if not self.socket_path:
            logger.error(
                "Failed to start webhook server. Cannot create ngrok tunnel."
            )
            return None

        # CRITICAL SAFETY CHECK: Force use of dynamic NGrok URLs
        # Ignore any custom domain settings to avoid TLS termination errors
        # Directly set ngrok_url to None in settings object to override any value
        if hasattr(settings, "ngrok_url") and settings.ngrok_url is not None:
            logger.warning(f"Detected custom domain: {settings.ngrok_url}")
            logger.warning("OVERRIDING to force dynamic NGrok URL")
            # Hard override the setting at runtime
            try:
                # This is a hack but necessary to force dynamic domains
                object.__setattr__(settings, "ngrok_url", None)
                logger.info("Successfully forced ngrok_url to None")
            except Exception as e:
                logger.warning(f"Could not override settings.ngrok_url: {e}")

        # Even if the above fails, still log that we're forcing dynamic domains
        logger.info("Forcing dynamic domain assignment for NGrok")

        try:
            # Aggressive cleanup of any existing ngrok resources (our own only)
            try:
                logger.info(
                    "Aggressively cleaning up existing ngrok SDK resources..."
                )

                # Multiple disconnect attempts to be thorough
                try:
                    ngrok.disconnect()
                    time.sleep(0.5)
                    # Try again to be sure
                    ngrok.disconnect()
                    time.sleep(0.5)
                except Exception:
                    pass

                # Clean up internal SDK state more thoroughly
                try:
                    # Reset any module-level state
                    import importlib

                    ngrok_module = importlib.import_module("ngrok")

                    # Clear any cached tunnels
                    if hasattr(ngrok_module, "_tunnels"):
                        ngrok_module._tunnels = {}
                    if hasattr(ngrok_module, "_listeners"):
                        ngrok_module._listeners = {}
                    if hasattr(ngrok_module, "api"):
                        # Reset API client if possible
                        ngrok_module.api._client = None

                    logger.info("Reset ngrok module internal state completely")
                except Exception as reset_err:
                    logger.warning(
                        f"Could not fully reset ngrok module state: {reset_err}"
                    )

                # Wait a bit to let any previous sessions expire
                time.sleep(1)
            except Exception as cleanup_err:
                logger.warning(
                    f"Failed during aggressive ngrok cleanup: {cleanup_err}"
                )

            # Prepare the Unix socket address
            unix_sock_addr = f"unix:{self.socket_path}"
            logger.info(f"Forwarding to Unix socket: {unix_sock_addr}")

            # More aggressive options to force dynamic domain - direct approach
            options = {
                "authtoken_from_env": bool(settings.ngrok_authtoken),
                "metadata": "Telnyx MCP Webhook Handler (Direct)",
                "verify_webhook_provider": "",  # Disable webhook verification
                "app_protocol": "http1",  # Explicitly use HTTP/1.1
                "domain": None,  # Explicitly set domain to None to force dynamic assignment
            }

            # Force override any custom domain settings from environment or cache
            if hasattr(ngrok, "set_config"):
                try:
                    ngrok.set_config(domain=None)
                    logger.info(
                        "Explicitly disabled custom domain in NGrok configuration"
                    )
                except Exception as config_err:
                    logger.warning(
                        f"Could not override NGrok domain config: {config_err}"
                    )

            # Create the tunnel - use the most direct approach possible
            logger.info(
                f"Creating ngrok tunnel with direct approach and options: {options}"
            )

            # Instead of using the Session API which is causing TLS termination issues,
            # Use a simplified direct approach without any custom domains or TLS options
            try:
                # Generate an extremely simplified set of options - remove TLS-related options
                simplified_options = {
                    "authtoken_from_env": bool(settings.ngrok_authtoken),
                    "metadata": "Telnyx MCP Webhook Handler (Simplified)",
                }

                # Skip the Session API approach entirely and use the basic forward function
                logger.info(
                    f"Creating NGrok tunnel with simplified options: {simplified_options}"
                )
                self.listener = ngrok.forward(
                    unix_sock_addr, **simplified_options
                )
                logger.info(
                    "Created NGrok tunnel using simplified forward method"
                )
            except Exception as module_err:
                # Final fallback with minimal options and different syntax
                logger.warning(
                    f"First approach failed: {module_err}, trying minimal fallback"
                )
                # Try with the absolute minimum options possible
                minimal_options = {
                    "authtoken_from_env": bool(settings.ngrok_authtoken),
                }
                logger.info(
                    f"Creating NGrok tunnel with minimal options: {minimal_options}"
                )
                self.listener = ngrok.forward(
                    unix_sock_addr, **minimal_options
                )
                logger.info(
                    "Created NGrok tunnel using minimal options approach"
                )

            # Get the public URL
            self.public_url = self.listener.url()

            # Mark that a tunnel was successfully established
            self._tunnel_was_established = True

            # Start reconnection monitor
            self._running = True
            self._start_reconnect_thread()

            logger.info(
                f"Ngrok tunnel established with dynamic URL: {self.public_url}"
            )
            logger.info(
                f"Webhook endpoint available at: {self.public_url}{settings.webhook_path}"
            )

            # Add a webhook to history to show it's working
            self._add_to_history(
                {
                    "event_type": "ngrok.tunnel.started",
                    "timestamp": datetime.now().isoformat(),
                    "url": self.public_url,
                    "webhook_endpoint": f"{self.public_url}{settings.webhook_path}",
                    "dynamic_url": True,
                }
            )

            return self.public_url
        except Exception as e:
            error_message = str(e)
            logger.error(f"Failed to start ngrok tunnel: {error_message}")

            # If session limit error, provide guidance but don't kill processes
            if "ERR_NGROK_108" in error_message:
                logger.error(
                    "Detected NGrok session limit error - cannot create a new tunnel"
                )
                logger.error(
                    "There are other NGrok sessions running that need to be closed"
                )
                logger.error(
                    "Manual intervention required: check https://dashboard.ngrok.com/agents"
                )

            # Record the error in webhook history
            self._add_to_history(
                {
                    "event_type": "ngrok.error",
                    "timestamp": datetime.now().isoformat(),
                    "error": error_message,
                    "error_type": "tls_error"
                    if "tls" in error_message.lower()
                    or "missing key" in error_message.lower()
                    else "session_limit"
                    if "ERR_NGROK_108" in error_message
                    else "unknown",
                }
            )

            # For any error, just log it and exit with a clear error message
            # Check for the specific ERR_NGROK_108 error (session limit)
            if "ERR_NGROK_108" in error_message:
                logger.critical(
                    f"FATAL ERROR: NGrok session limit exceeded: {error_message}"
                )
                logger.critical(
                    "You currently have other NGrok sessions running. To fix this issue:"
                )
                logger.critical(
                    "1. Go to https://dashboard.ngrok.com/agents to manage existing sessions"
                )
                logger.critical(
                    "2. Or wait for other sessions to complete before restarting"
                )
                logger.critical(
                    "3. Consider upgrading NGrok plan for more simultaneous sessions"
                )
            else:
                logger.critical(
                    f"FATAL ERROR: NGrok tunnel failed to start: {error_message}"
                )

            # Clean up and exit with a clear error message - webhooks are critical
            stop_webhook_server()
            logger.critical(
                "FATAL ERROR: Cannot continue without NGrok tunnel for webhooks"
            )
            logger.critical(f"Specific error: {error_message}")
            logger.critical(
                "Please fix NGrok configuration issues before restarting"
            )
            sys.exit(1)  # Exit with error code - fail decisively

    def _start_reconnect_thread(self):
        """Start a thread to monitor and reconnect the tunnel if needed."""
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return

        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop,
            daemon=True,
        )
        self._reconnect_thread.start()

    def _reconnect_loop(self):
        """Background thread: monitor the tunnel and reconnect if needed."""
        logger.info("Starting ngrok tunnel monitor thread")
        reconnection_attempts = 0
        max_reconnection_attempts = 3

        while self._running:
            time.sleep(30)  # Check every 30 seconds

            if not self._running:
                break

            try:
                # If we have a listener and public URL, we're good
                if self.listener and self.public_url:
                    reconnection_attempts = (
                        0  # Reset counter on successful connection
                    )
                    continue
                else:
                    # If the tunnel was previously established but is now gone, this is a critical error
                    if (
                        self._running
                        and hasattr(self, "_tunnel_was_established")
                        and self._tunnel_was_established
                    ):
                        logger.critical(
                            "FATAL ERROR: NGrok tunnel was previously established but has been lost"
                        )
                        logger.critical(
                            "Webhooks are required for MCP server operation"
                        )
                        logger.critical(
                            "The server will exit. Please restart when NGrok is available."
                        )
                        sys.exit(1)  # Exit with error code - fail decisively

                # Check if we've exceeded max reconnection attempts
                if reconnection_attempts >= max_reconnection_attempts:
                    logger.critical(
                        f"FATAL ERROR: Exceeded {max_reconnection_attempts} NGrok tunnel reconnection attempts"
                    )
                    logger.critical(
                        "Webhooks are required for operation - exiting process immediately"
                    )

                    # Record the terminal error in webhook history
                    try:
                        self._add_to_history(
                            {
                                "event_type": "ngrok.error.terminal",
                                "timestamp": datetime.now().isoformat(),
                                "error": f"Exceeded {max_reconnection_attempts} reconnection attempts",
                                "error_type": "reconnection_failure",
                            }
                        )
                    except Exception:
                        pass  # Ignore any errors in recording history at this point

                    # Exit with a clear error message - webhooks are critical
                    logger.critical(
                        "FATAL ERROR: Max reconnection attempts exceeded for NGrok tunnel"
                    )
                    logger.critical(
                        "Webhooks are required for MCP server operation"
                    )
                    sys.exit(1)  # Exit with error code - fail decisively

                # Increment attempt counter
                reconnection_attempts += 1
                logger.warning(
                    f"Tunnel not active, attempting to reconnect (attempt {reconnection_attempts}/{max_reconnection_attempts})..."
                )

                # Try to stop existing resources
                try:
                    self.stop()
                except Exception as stop_error:
                    logger.error(
                        f"Error stopping existing tunnel: {stop_error}"
                    )

                time.sleep(2)  # Brief delay before reconnecting

                # Try to start a new tunnel
                try:
                    new_url = self.start()
                    if new_url:
                        logger.info(
                            f"Successfully reconnected tunnel. New URL: {new_url}"
                        )
                        reconnection_attempts = 0  # Reset counter on success
                    else:
                        logger.error("Failed to reconnect tunnel")
                except Exception as start_error:
                    logger.error(f"Error starting new tunnel: {start_error}")
            except Exception as e:
                logger.error(f"Error in tunnel monitor thread: {e}")

        logger.info("Tunnel monitor thread stopped")

    def _add_to_history(self, data):
        """Add an event to the webhook history."""
        from .server import webhook_history

        webhook_history.appendleft(
            {
                "timestamp": datetime.now().isoformat(),
                "event_type": data.get("event_type", "unknown"),
                "payload": data,
            }
        )
        logger.debug(f"Added event to history (total: {len(webhook_history)})")

    def stop(self) -> None:
        """Stop the tunnel and clean up resources."""
        self._running = False

        # First stop the reconnect thread to prevent race conditions
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            logger.debug("Stopping reconnect thread...")
            try:
                self._reconnect_thread.join(timeout=5.0)
                if self._reconnect_thread.is_alive():
                    logger.warning(
                        "Reconnect thread did not terminate in time"
                    )
            except Exception as thread_err:
                logger.error(f"Error stopping reconnect thread: {thread_err}")

        # Then stop the tunnel
        if self.listener:
            try:
                logger.info("Stopping ngrok tunnel...")

                # Try all available methods to ensure the tunnel is stopped
                try:
                    # Handle different ngrok SDK versions
                    if hasattr(self.listener, "close"):
                        # Newer SDK versions
                        self.listener.close()
                except Exception as close_err:
                    logger.warning(f"Error closing listener: {close_err}")

                try:
                    # Try disconnecting specifically for older SDK versions
                    if hasattr(ngrok, "disconnect"):
                        if self.public_url:
                            ngrok.disconnect(self.public_url)
                        else:
                            # Fallback - disconnect all
                            ngrok.disconnect()
                except Exception as disconnect_err:
                    logger.warning(f"Error disconnecting: {disconnect_err}")

                logger.info("Ngrok tunnel stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping ngrok tunnel: {e}")

        # Stop the webhook server
        stop_webhook_server()

        # Always reset these variables regardless of any errors
        self.listener = None
        self.public_url = None
        self.socket_path = None
