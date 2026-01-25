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
    errors: Optional[Dict[str, Dict[str, str]]] = None

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
    """Verified domain."""
    domain_name: str
    verification_status: str
    created_at: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Domain":
        return cls(
            domain_name=data.get("domain_name", ""),
            verification_status=data.get("verification_status", ""),
            created_at=data.get("created_at", ""),
        )


@dataclass
class Account:
    """Account information."""
    title: str
    plan_type: str
    status: str
    emails_usage_this_month: int
    emails_sent_last_24hrs: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Account":
        return cls(
            title=data.get("title", ""),
            plan_type=data.get("plan_type", ""),
            status=data.get("status", ""),
            emails_usage_this_month=data.get("emails_usage_this_month", 0),
            emails_sent_last_24hrs=data.get("emails_sent_last_24hrs", 0),
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
