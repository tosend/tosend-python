"""Exceptions for ToSend SDK."""

from typing import Optional, Dict, Any


class ToSendError(Exception):
    """ToSend API error.

    ``errors`` comes in two shapes. The sending API nests it per field
    (``{"subject": {"required": "Subject is required."}}``); the Admin API
    returns a flat map (``{"name": "required"}``, or
    ``{"code": "insufficient_scope", "required_scope": "domains:read"}``).
    Admin API errors also carry no ``error_type``.
    """

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        error_type: str = "unknown_error",
        errors: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.errors = errors or {}

    @classmethod
    def from_response(cls, data: Dict[str, Any], status_code: int) -> "ToSendError":
        return cls(
            message=data.get("message", "Unknown error"),
            # The HTTP status is authoritative; the body's copy is optional.
            status_code=status_code or data.get("status_code", 0),
            error_type=data.get("error_type") or "unknown_error",
            errors=data.get("errors") if isinstance(data.get("errors"), dict) else None,
        )

    @property
    def code(self) -> Optional[str]:
        """Machine-readable code from a flat ``errors`` map, e.g. ``insufficient_scope``."""
        value = self.errors.get("code")
        return value if isinstance(value, str) else None

    @property
    def is_validation_error(self) -> bool:
        return self.error_type == "validation_error" or self.status_code == 422

    @property
    def is_authentication_error(self) -> bool:
        return (
            self.error_type in ("unauthorized", "forbidden")
            or self.status_code in (401, 403)
        )

    @property
    def is_rate_limit_error(self) -> bool:
        return self.error_type == "rate_limit_exceeded" or self.status_code == 429

    def __str__(self) -> str:
        return f"ToSendError: {self.message} (status: {self.status_code}, type: {self.error_type})"
