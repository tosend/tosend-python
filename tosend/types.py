"""Type definitions for ToSend SDK."""

from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Any


@dataclass
class Address:
    """Email address with optional name."""
    email: str
    name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {"email": self.email}
        if self.name:
            d["name"] = self.name
        return d


@dataclass
class Attachment:
    """Email attachment."""
    type: str  # MIME type
    name: str  # Filename
    content: str  # Base64 encoded content

    def to_dict(self) -> Dict[str, str]:
        return {"type": self.type, "name": self.name, "content": self.content}


@dataclass
class SendEmailRequest:
    """Request to send a single email."""
    from_address: Address
    to: List[Address]
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None
    cc: Optional[List[Address]] = None
    bcc: Optional[List[Address]] = None
    reply_to: Optional[Address] = None
    headers: Optional[Dict[str, str]] = None
    attachments: Optional[List[Attachment]] = None

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "from": self.from_address.to_dict(),
            "to": [addr.to_dict() for addr in self.to],
            "subject": self.subject,
        }
        if self.html:
            d["html"] = self.html
        if self.text:
            d["text"] = self.text
        if self.cc:
            d["cc"] = [addr.to_dict() for addr in self.cc]
        if self.bcc:
            d["bcc"] = [addr.to_dict() for addr in self.bcc]
        if self.reply_to:
            d["reply_to"] = self.reply_to.to_dict()
        if self.headers:
            d["headers"] = self.headers
        if self.attachments:
            d["attachments"] = [att.to_dict() for att in self.attachments]
        return d


@dataclass
class SendEmailResponse:
    """Response from sending an email."""
    message_id: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SendEmailResponse":
        return cls(message_id=data.get("message_id", ""))


@dataclass
class BatchEmailResult:
    """Result of a single email in a batch."""
    status: str
    message_id: Optional[str] = None
    message: Optional[str] = None
    # Nested per field ({"subject": {"required": "..."}}) or flat.
    errors: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchEmailResult":
        return cls(
            status=data.get("status", ""),
            message_id=data.get("message_id"),
            message=data.get("message"),
            errors=data.get("errors"),
        )


@dataclass
class BatchEmailResponse:
    """Response from sending batch emails."""
    results: List[BatchEmailResult]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BatchEmailResponse":
        results = [BatchEmailResult.from_dict(r) for r in data.get("results", [])]
        return cls(results=results)


@dataclass
class Domain:
    """A domain on the account, as returned by GET /v2/info."""

    id: int
    domain_name: str
    verification_status: str
    is_default: bool
    total_sent: int
    total_bounced: int
    total_complained: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Domain":
        return cls(
            id=data.get("id", 0),
            domain_name=data.get("domain_name", ""),
            verification_status=data.get("verification_status", ""),
            # Stored as 0/1, so coerce rather than trust the JSON type.
            is_default=bool(data.get("is_default", False)),
            total_sent=data.get("total_sent", 0) or 0,
            total_bounced=data.get("total_bounced", 0) or 0,
            total_complained=data.get("total_complained", 0) or 0,
        )


@dataclass
class Account:
    """Account information, as returned by GET /v2/info."""

    id: int
    status: str
    plan_type: str
    # None means the account does not consume credits.
    credit_balance: Optional[int]
    monthly_email_limit: Optional[int]
    limit_per_second: Optional[int]
    ses_region: str
    bounce_rate: float
    complaint_rate: float
    ses_status: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        return cls(
            id=data.get("id", 0),
            status=data.get("status", ""),
            plan_type=data.get("plan_type", ""),
            credit_balance=data.get("credit_balance"),
            monthly_email_limit=data.get("monthly_email_limit"),
            limit_per_second=data.get("limit_per_second"),
            ses_region=data.get("ses_region", ""),
            bounce_rate=float(data.get("bounce_rate") or 0),
            complaint_rate=float(data.get("complaint_rate") or 0),
            ses_status=data.get("ses_status", ""),
        )


@dataclass
class AccountInfo:
    """Account info response."""

    account: Account
    domains: List[Domain]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AccountInfo":
        return cls(
            account=Account.from_dict(data.get("account", {})),
            domains=[Domain.from_dict(d) for d in data.get("domains", [])],
        )
