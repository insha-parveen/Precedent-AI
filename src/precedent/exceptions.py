"""Exception classes for Precedent.

Defines custom exception types used throughout the application.
"""


class AuthenticationError(Exception):
    """Raised when authentication fails or token is invalid."""
    pass