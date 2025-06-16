"""In-memory store for OAuth authorization codes and sessions."""

import secrets
import time
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)

@dataclass
class AuthCodeData:
    """Data associated with an authorization code."""
    code: str
    azure_token: str
    azure_token_data: Dict[str, Any]
    user_info: Dict[str, Any]
    created_at: float
    expires_at: float
    used: bool = False
    state: Optional[str] = None
    redirect_uri: Optional[str] = None
    pkce_challenge: Optional[str] = None
    pkce_method: Optional[str] = None

@dataclass
class SessionData:
    """OAuth session data."""
    session_id: str
    state: str
    redirect_uri: Optional[str] = None
    created_at: float = field(default_factory=time.time)
    pkce_challenge: Optional[str] = None
    pkce_method: Optional[str] = None


class AuthStore:
    """Simple in-memory store for OAuth codes and sessions.
    
    Note: This is for development/testing. Production should use Redis or a database.
    """
    
    def __init__(self, code_ttl: int = 60, session_ttl: int = 3600):
        """Initialize the auth store.
        
        Args:
            code_ttl: Time-to-live for auth codes in seconds (default: 60 seconds)
            session_ttl: Time-to-live for sessions in seconds (default: 1 hour)
        """
        self._codes: Dict[str, AuthCodeData] = {}
        self._sessions: Dict[str, SessionData] = {}
        self.code_ttl = code_ttl
        self.session_ttl = session_ttl
    
    def create_auth_code(
        self,
        azure_token: str,
        azure_token_data: Dict[str, Any],
        user_info: Dict[str, Any],
        state: Optional[str] = None,
        redirect_uri: Optional[str] = None,
        pkce_challenge: Optional[str] = None,
        pkce_method: Optional[str] = None
    ) -> str:
        """Create a new authorization code.
        
        Returns:
            The generated authorization code
        """
        # Generate a cryptographically secure code
        code = secrets.token_urlsafe(32)
        
        # Store the code data
        self._codes[code] = AuthCodeData(
            code=code,
            azure_token=azure_token,
            azure_token_data=azure_token_data,
            user_info=user_info,
            created_at=time.time(),
            expires_at=time.time() + self.code_ttl,
            used=False,
            state=state,
            redirect_uri=redirect_uri,
            pkce_challenge=pkce_challenge,
            pkce_method=pkce_method
        )
        
        # Clean up expired codes
        self._cleanup_expired_codes()
        
        logger.info(f"Created auth code for user: {user_info.get('email', 'unknown')}")
        return code
    
    def get_auth_code(self, code: str) -> Optional[AuthCodeData]:
        """Retrieve auth code data.
        
        Args:
            code: The authorization code
            
        Returns:
            AuthCodeData if valid and not expired, None otherwise
        """
        data = self._codes.get(code)
        
        if not data:
            logger.warning(f"Auth code not found: {code[:8]}...")
            return None
        
        # Check if expired
        if time.time() > data.expires_at:
            logger.warning(f"Auth code expired: {code[:8]}...")
            del self._codes[code]
            return None
        
        # Check if already used
        if data.used:
            logger.warning(f"Auth code already used: {code[:8]}...")
            return None
        
        return data
    
    def mark_code_used(self, code: str) -> bool:
        """Mark an authorization code as used.
        
        Args:
            code: The authorization code
            
        Returns:
            True if successfully marked, False if not found
        """
        data = self._codes.get(code)
        if data:
            data.used = True
            logger.info(f"Marked auth code as used: {code[:8]}...")
            return True
        return False
    
    def create_session(
        self,
        state: str,
        redirect_uri: Optional[str] = None,
        pkce_challenge: Optional[str] = None,
        pkce_method: Optional[str] = None
    ) -> str:
        """Create a new OAuth session.
        
        Returns:
            The session ID
        """
        session_id = secrets.token_urlsafe(32)
        
        self._sessions[session_id] = SessionData(
            session_id=session_id,
            state=state,
            redirect_uri=redirect_uri,
            created_at=time.time(),
            pkce_challenge=pkce_challenge,
            pkce_method=pkce_method
        )
        
        # Clean up expired sessions
        self._cleanup_expired_sessions()
        
        logger.info(f"Created OAuth session: {session_id[:8]}...")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionData]:
        """Get session data.
        
        Args:
            session_id: The session ID
            
        Returns:
            SessionData if found and not expired, None otherwise
        """
        data = self._sessions.get(session_id)
        
        if not data:
            return None
        
        # Check if expired
        if time.time() > (data.created_at + self.session_ttl):
            logger.warning(f"Session expired: {session_id[:8]}...")
            del self._sessions[session_id]
            return None
        
        return data
    
    def get_session_by_state(self, state: str) -> Optional[SessionData]:
        """Find a session by state parameter.
        
        Args:
            state: The OAuth state parameter
            
        Returns:
            SessionData if found, None otherwise
        """
        for session in self._sessions.values():
            if session.state == state:
                # Check expiry
                if time.time() > (session.created_at + self.session_ttl):
                    continue
                return session
        return None
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session.
        
        Args:
            session_id: The session ID
            
        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Deleted session: {session_id[:8]}...")
            return True
        return False
    
    def _cleanup_expired_codes(self):
        """Remove expired authorization codes."""
        current_time = time.time()
        expired = [
            code for code, data in self._codes.items()
            if current_time > data.expires_at
        ]
        for code in expired:
            del self._codes[code]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired auth codes")
    
    def _cleanup_expired_sessions(self):
        """Remove expired sessions."""
        current_time = time.time()
        expired = [
            sid for sid, data in self._sessions.items()
            if current_time > (data.created_at + self.session_ttl)
        ]
        for sid in expired:
            del self._sessions[sid]
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired sessions")


# Global instance for the application
auth_store = AuthStore()