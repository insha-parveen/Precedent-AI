"""Unit tests for the authentication module."""
import json
from unittest.mock import patch

import pytest

from src.precedent.auth import AuthenticatedUser, create_mock_user_for_dev, get_current_user
from src.precedent.exceptions import AuthenticationError


def test_authenticated_user_dataclass():
    """Test AuthenticatedUser dataclass creation."""
    user = AuthenticatedUser(
        user_id="test123",
        username="testuser",
        email="test@example.com",
        roles=["admin", "user"],
        access_groups=["public", "internal"]
    )

    assert user.user_id == "test123"
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.roles == ["admin", "user"]
    assert user.access_groups == ["public", "internal"]


def test_create_mock_user_for_dev():
    """Test mock user creation for development."""
    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.precedent_env = "development"
        mock_settings.default_role = "public"
        mock_settings.always_include_public = True

        user = create_mock_user_for_dev()

        assert user.user_id == "dev-user"
        assert user.username == "developer"
        assert user.email == "dev@precedent.local"
        assert user.roles == ["public"]
        assert user.access_groups == ["public"]


def test_get_current_user_empty_token():
    """Test get_current_user with empty token."""
    with pytest.raises(AuthenticationError, match="Empty token provided"):
        get_current_user("")


def test_get_current_user_none_token():
    """Test get_current_user with None token."""
    with pytest.raises(AuthenticationError, match="Empty token provided"):
        get_current_user(None)


def test_get_current_user_invalid_token():
    """Test get_current_user with invalid token."""
    with pytest.raises(AuthenticationError, match="Invalid token"):
        get_current_user("invalid.token.string")


def test_get_current_user_missing_sub():
    """Test get_current_user with token missing sub claim."""
    # Create a token payload without sub
    test_payload = {
        "username": "testuser",
        "email": "test@example.com",
        "iat": 1516239022
    }

    import jwt
    test_token = jwt.encode(test_payload, "test-secret", algorithm="HS256")

    with patch('src.precedent.config.settings') as mock_settings, \
         patch('jwt.decode') as mock_decode:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        mock_settings.jwt_resource_identifier = "precedent"
        mock_settings.default_role = "public"
        mock_settings.role_to_access_groups = {}
        mock_settings.always_include_public = False

        # Mock the decoded payload
        mock_decode.return_value = test_payload

        with pytest.raises(AuthenticationError, match="Token missing user identifier"):
            get_current_user(test_token)


def test_get_current_user_valid_token():
    """Test get_current_user with valid token."""
    # Create a test token with sub claim
    test_payload = {
        "sub": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "roles": ["legal_team"],
        "iat": 1516239022
    }

    # Encode with a test secret
    import jwt
    test_token = jwt.encode(test_payload, "test-secret", algorithm="HS256")

    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        mock_settings.jwt_resource_identifier = "precedent"
        mock_settings.default_role = "public"
        mock_settings.role_to_access_groups = {"legal_team": ["public", "internal"]}
        mock_settings.always_include_public = True

        user = get_current_user(test_token)

        assert user.user_id == "user123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.roles == ["legal_team"]
        assert "public" in user.access_groups
        assert "internal" in user.access_groups


def test_get_current_user_resource_access_roles():
    """Test get_current_user extracting roles from resource_access."""
    # Token with resource_access structure (Keycloak format)
    test_payload = {
        "sub": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "resource_access": {
            "precedent": {
                "roles": ["audit"]
            }
        },
        "iat": 1516239022
    }

    import jwt
    test_token = jwt.encode(test_payload, "test-secret", algorithm="HS256")

    with patch('src.precedent.config.settings') as mock_settings, \
         patch('jwt.decode') as mock_decode:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        mock_settings.jwt_resource_identifier = "precedent"
        mock_settings.default_role = "public"
        mock_settings.role_to_access_groups = {"audit": ["public"]}
        mock_settings.always_include_public = True

        # Mock the decoded payload
        mock_decode.return_value = test_payload

        user = get_current_user(test_token)

        assert user.user_id == "user123"
        assert user.roles == ["audit"]
        assert user.access_groups == ["public"]


def test_get_current_user_realm_access_roles():
    """Test get_current_user extracting roles from realm_access."""
    # Token with realm_access structure
    test_payload = {
        "sub": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "realm_access": {
            "roles": ["legal_team", "audit"]
        },
        "iat": 1516239022
    }

    import jwt
    test_token = jwt.encode(test_payload, "test-secret", algorithm="HS256")

    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        mock_settings.jwt_resource_identifier = "precedent"
        mock_settings.default_role = "public"
        mock_settings.role_to_access_groups = {
            "legal_team": ["public", "internal"],
            "audit": ["public"]
        }
        mock_settings.always_include_public = True

        user = get_current_user(test_token)

        assert user.user_id == "user123"
        assert set(user.roles) == {"legal_team", "audit"}
        assert set(user.access_groups) == {"public", "internal"}


def test_get_current_user_no_roles_fallback():
    """Test get_current_user fallback to default role when no roles found."""
    test_payload = {
        "sub": "user123",
        "username": "testuser",
        "email": "test@example.com",
        "iat": 1516239022
    }

    import jwt
    test_token = jwt.encode(test_payload, "test-secret", algorithm="HS256")

    with patch('src.precedent.config.settings') as mock_settings, \
         patch('jwt.decode') as mock_decode:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        mock_settings.jwt_resource_identifier = "precedent"
        mock_settings.default_role = "public"
        mock_settings.role_to_access_groups = {}  # No mapping
        mock_settings.always_include_public = True

        # Mock the decoded payload
        mock_decode.return_value = test_payload

        user = get_current_user(test_token)

        assert user.user_id == "user123"
        assert user.roles == ["public"]  # Default role
        assert user.access_groups == ["public"]  # Should include public


def test_get_current_user_duplicate_access_groups():
    """Test that duplicate access groups are removed."""
    test_payload = {
        "sub": "user123",
        "roles": ["legal_team", "audit"],  # Both map to public
        "iat": 1516239022
    }

    import jwt
    test_token = jwt.encode(test_payload, "test-secret", algorithm="HS256")

    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        mock_settings.jwt_resource_identifier = "precedent"
        mock_settings.default_role = "public"
        mock_settings.role_to_access_groups = {
            "legal_team": ["public", "internal"],
            "audit": ["public", "internal"]  # Both map to same groups
        }
        mock_settings.always_include_public = True

        user = get_current_user(test_token)

        # Should have no duplicates
        assert user.access_groups == ["public", "internal"] or user.access_groups == ["internal", "public"]
        assert len(user.access_groups) == len(set(user.access_groups))


# --- Security hardening tests (fail-closed behavior) ---

def _make_token(payload: dict) -> str:
    import jwt
    return jwt.encode(payload, "test-secret", algorithm="HS256")


def test_get_current_user_fails_closed_without_secret():
    """Empty JWT_SECRET_KEY must reject every token, not validate against ''."""
    test_token = _make_token({"sub": "user123", "roles": ["legal_team"]})

    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.jwt_secret_key = ""  # not configured
        with pytest.raises(AuthenticationError, match="JWT secret not configured"):
            get_current_user(test_token)


def test_get_current_user_rejects_wrong_secret():
    """A token signed with a different secret must not validate."""
    import jwt
    other_token = jwt.encode({"sub": "user123"}, "attacker-secret", algorithm="HS256")

    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        with pytest.raises(AuthenticationError, match="Invalid token"):
            get_current_user(other_token)


def test_get_current_user_expired_token_rejected():
    """Expired tokens must be rejected (pyjwt validates exp by default)."""
    import jwt
    expired = jwt.encode({"sub": "user123", "exp": 1000000000}, "test-secret", algorithm="HS256")

    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        with pytest.raises(AuthenticationError, match="Invalid token"):
            get_current_user(expired)


def test_get_current_user_algorithm_confusion_rejected():
    """alg=none / unsigned tokens must not pass when HS256 is configured."""
    # Shape an alg=none token: header claims "none", empty signature
    unsigned_token = (
        "eyJhbGciOiJub25lIiwidHlwIjoiSldUIn0"  # {"alg":"none","typ":"JWT"}
        ".eyJzdWIiOiJ1c2VyMTIzIn0"              # {"sub":"user123"}
        "."                                      # empty signature
    )

    with patch('src.precedent.auth.settings') as mock_settings:
        mock_settings.jwt_secret_key = "test-secret"
        mock_settings.jwt_algorithm = "HS256"
        mock_settings.jwt_issuer = None
        mock_settings.jwt_audience = None
        with pytest.raises(AuthenticationError):
            get_current_user(unsigned_token)


if __name__ == "__main__":
    pytest.main([__file__])