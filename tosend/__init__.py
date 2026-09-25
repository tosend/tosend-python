"""
ToSend Python SDK

Official Python SDK for the ToSend email API.
"""

from .client import ToSend
from .admin import ToSendAdmin
from .exceptions import ToSendError
from .types import (
    Address,
    Attachment,
    SendEmailRequest,
    SendEmailResponse,
    BatchEmailResult,
    BatchEmailResponse,
    Domain,
    Account,
    AccountInfo,
)

from .client import __version__  # noqa: F401  (single source of truth)
__all__ = [
    "ToSend",
    "ToSendAdmin",
    "ToSendError",
    "Address",
    "Attachment",
    "SendEmailRequest",
    "SendEmailResponse",
    "BatchEmailResult",
    "BatchEmailResponse",
    "Domain",
    "Account",
    "AccountInfo",
]
