"""Exceptions for ToSend SDK."""

from typing import Optional, Dict, Any


class ToSendError(Exception):
    """ToSend API error."""

    def __init__(
        self,
        message: str,
        status_code: int = 0,
        error_type: str = "unknown_error",
        errors: Optional[Dict[str, Dict[str, str]]] = None,
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
            status_code=status_code,
            error_type=data.get("error_type", "unknown_error"),
            errors=data.get("errors"),
        )

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
