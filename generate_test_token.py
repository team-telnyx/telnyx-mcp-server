#!/usr/bin/env python3
"""Generate a test JWT token for local development."""

import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "test-secret-key")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

# Create test user payload
user_info = {
    "id": "test-user-id",
    "email": "test@example.com",
    "name": "Test User",
    "displayName": "Test User",
    "userPrincipalName": "test@example.com"
}

# Create JWT token
expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
token_data = {
    **user_info,
    "exp": expiration,
    "iat": datetime.utcnow()
}

token = jwt.encode(token_data, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

print(token)