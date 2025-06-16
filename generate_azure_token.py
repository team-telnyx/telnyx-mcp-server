#!/usr/bin/env python3
"""Generate a test JWT token for Azure deployment."""

import jwt
import os
from datetime import datetime, timedelta

# Use the same secret key as configured in Azure
JWT_SECRET_KEY = "Yxvoyz7yccJ4D8QBqfiUcjV+0XjhzGXwT/kBtp+HFFc="
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

# Create test user payload
user_info = {
    "id": "azure-test-user",
    "email": "test@azure.com",
    "name": "Azure Test User",
    "displayName": "Azure Test User",
    "userPrincipalName": "test@azure.com"
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