"""
ToSend Python SDK

Official Python SDK for the ToSend email API.
"""

from .client import ToSend
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

__version__ = "1.0.0"
__all__ = [
    "ToSend",
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
