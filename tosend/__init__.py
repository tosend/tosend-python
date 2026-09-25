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

__version__ = "1.1.0"
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
