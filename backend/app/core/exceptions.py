"""Custom exception classes for OpenClaw-Harness."""


class OCHError(Exception):
    """Base exception for OpenClaw-Harness."""

    def __init__(self, message: str, code: int = 500, details: dict | None = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(OCHError):
    """Resource not found."""

    def __init__(self, resource: str, id: str | int):
        super().__init__(f"{resource} with id '{id}' not found", 404)


class AuthenticationError(OCHError):
    """Authentication failed."""

    def __init__(self, message: str = "Invalid credentials"):
        super().__init__(message, 401)


class AuthorizationError(OCHError):
    """Insufficient permissions."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, 403)


class ValidationError(OCHError):
    """Validation error."""

    def __init__(self, message: str, field: str | None = None):
        details = {}
        if field:
            details['field'] = field
        super().__init__(message, 422, details)


class SessionError(OCHError):
    """Session-related errors."""

    def __init__(self, message: str, session_id: str | None = None):
        details = {}
        if session_id:
            details['session_id'] = session_id
        super().__init__(message, 400, details)


class ToolExecutionError(OCHError):
    """Tool execution failure."""

    def __init__(self, tool_name: str, error: str):
        super().__init__(
            f"Tool '{tool_name}' execution failed: {error}",
            500,
            {'tool_name': tool_name, 'error': error},
        )


class PermissionDeniedError(OCHError):
    """Permission denied by permission system."""

    def __init__(self, tool_name: str, reason: str = ""):
        super().__init__(
            f"Permission denied for '{tool_name}': {reason}",
            403,
            {'tool_name': tool_name, 'reason': reason},
        )
