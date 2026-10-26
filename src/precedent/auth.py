"""Authentication and authorization module for Precedent.

Handles JWT token validation, user information extraction, and mapping
of roles to access groups for permission filtering.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

import jwt
from jwt.exceptions import InvalidTokenError

from .config import settings
from .exceptions import AuthenticationError


@dataclass
class AuthenticatedUser:
    """Represents an authenticated user with their access groups."""
    user_id: str
    username: str | None
    email: str | None
    roles: list[str]
    access_groups: list[str]


def get_current_user(token: str) -> AuthenticatedUser:
    """Validate JWT token and extract user information.

    Args:
        token: JWT token string

    Returns:
        AuthenticatedUser object with user info and access groups

    Raises:
        AuthenticationError: If token is invalid or user info cannot be extracted
    """
    if not token or not token.strip():
        raise AuthenticationError("Empty token provided")

    if not settings.jwt_secret_key:
        # Fail closed: without a configured secret, signatures cannot be verified,
        # so every token must be rejected — never fall back to an unverified decode.
        raise AuthenticationError(
            "JWT secret not configured (set JWT_SECRET_KEY); refusing to validate tokens"
        )

    try:
        # Decode token without verification first to check if it's JWT
        # We'll verify with the secret key below
        header = jwt.get_unverified_header(token)

        # Verify signature and claims
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer if settings.jwt_issuer else None,
            audience=settings.jwt_audience if settings.jwt_audience else None,
        )
    except InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")
    except Exception as e:
        raise AuthenticationError(f"Token validation failed: {str(e)}")

    # Extract user information from token payload
    user_id = payload.get("sub") or payload.get("user_id") or payload.get("uid")
    if not user_id:
        raise AuthenticationError("Token missing user identifier (sub)")

    username = payload.get("username") or payload.get("name") or payload.get("preferred_username")
    email = payload.get("email") or payload.get("email_address")

    # Extract roles from token - common locations
    roles = []
    # Check for roles in various common claim locations
    if "roles" in payload and isinstance(payload["roles"], list):
        roles = payload["roles"]
    elif "realm_access" in payload and isinstance(payload["realm_access"], dict):
        realm_roles = payload["realm_access"].get("roles", [])
        if isinstance(realm_roles, list):
            roles = realm_roles
    elif "resource_access" in payload and isinstance(payload["resource_access"], dict):
        resource_access = payload["resource_access"]
        # Look for our resource identifier in resource access
        if settings.jwt_resource_identifier in resource_access:
            resource_roles = resource_access[settings.jwt_resource_identifier].get("roles", [])
            if isinstance(resource_roles, list):
                roles = resource_roles
        # Also check any resource for roles (fallback)
        elif not roles:
            for resource, access in resource_access.items():
                if isinstance(access, dict) and "roles" in access:
                    resource_roles = access["roles"]
                    if isinstance(resource_roles, list):
                        roles.extend(resource_roles)

    # Use default role if no roles found
    if not roles:
        roles = [settings.default_role]

    # Map roles to access groups using configuration
    access_groups = []
    for role in roles:
        if role in settings.role_to_access_groups:
            access_groups.extend(settings.role_to_access_groups[role])

    # Remove duplicates while preserving order
    seen = set()
    unique_access_groups = []
    for group in access_groups:
        if group not in seen:
            seen.add(group)
            unique_access_groups.append(group)

    # Always include public access group if configured (for demo compatibility)
    if settings.always_include_public and "public" not in unique_access_groups:
        unique_access_groups.append("public")

    # Fallback: if no access groups mapped, use default role as access group
    if not unique_access_groups:
        unique_access_groups = [settings.default_role]
        if settings.always_include_public and settings.default_role != "public":
            unique_access_groups.append("public")

    return AuthenticatedUser(
        user_id=str(user_id),
        username=username,
        email=email,
        roles=roles,
        access_groups=unique_access_groups,
    )


def create_mock_user_for_dev() -> AuthenticatedUser:
    """Create a mock user for development/testing when no auth is configured.

    Returns:
        AuthenticatedUser object with development/default access
    """
    return AuthenticatedUser(
        user_id="dev-user",
        username="developer",
        email="dev@precedent.local",
        roles=[settings.default_role],
        access_groups=["public"] if settings.always_include_public else [settings.default_role],
    )